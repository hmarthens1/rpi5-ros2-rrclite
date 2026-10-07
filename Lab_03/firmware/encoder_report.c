/**
 * encoder_report.c - Lab 03 add-on for the Hiwonder RRC Lite "ros" firmware.
 *
 * Hiwonder's source is NOT edited. The Makefile links this file in and uses
 * the linker's --wrap option to hook two functions:
 *
 *   packet_handle_init()  -> after Hiwonder's setup, put our handler in front of
 *                            the PACKET_FUNC_MOTOR (3) handler and start the
 *                            report task. Every motor sub-command we don't know
 *                            is passed on unchanged, so the protocol stays
 *                            100 % compatible with the factory firmware.
 *   motors_init()         -> after Hiwonder's setup, also start motor 4's
 *                            encoder timer (TIM3). The factory code starts TIM4
 *                            twice and never TIM3, so M4's encoder reads nothing.
 *
 * Stops are made HARD: Hiwonder's speed loop is incremental (pwm += PID output
 * every 10 ms), so "target 0" alone leaves the PWM where it was while a motor
 * can't turn (battery off, wheel blocked) - and it starts again later. Here,
 * stop commands (sub-commands 0x02, 0x03), any target of 0, and the watchdog
 * also set the PWM to 0 and clear the PID's stored errors.
 *
 * New PACKET_FUNC_MOTOR sub-commands (Pi -> board):
 *   0x10 <u8 period_ms>   encoder report every period_ms (10..255), 0 = off
 *   0x11 <u16 timeout_ms> command watchdog: if no motor command arrives for
 *                         timeout_ms, every motor's target speed is set to 0.
 *                         0 = off (the default, like the factory firmware).
 *                         Protects against a lost USB link leaving a motor running.
 *   0x12 <u8 motor_id 0-3, 0xFF = all> <i32 ticks_per_circle> <f32 rps_limit>
 *        <f32 kp> <f32 ki> <f32 kd>
 *                         set one or all motors' speed-control parameters
 *                         (like sub-command 5, but any value)
 *   0x13 <f32 kf> <f32 kp> <f32 ki>
 *                         gains of the Lab 03 speed loop (speed_control.c,
 *                         built with SPEED_LOOP=lab03 only)
 *
 * Encoder report (board -> Pi), PACKET_FUNC_MOTOR, 57 data bytes:
 *   0x10, then for M1..M4: <i32 count> <f32 rps> <f32 target_rps> <i16 pwm>
 *     count       total encoder counts (4 per encoder line, quadrature x4)
 *     rps         measured output-shaft speed = counts/s / ticks_per_circle
 *     target_rps  the PID set point
 *     pwm         PWM duty sent to the driver, -1000..1000 (sign = direction)
 */
#include <string.h>
#include "cmsis_os2.h"
#include "tim.h"
#include "global.h"
#include "packet.h"
#include "encoder_motor.h"

extern EncoderMotorObjectTypeDef *motors[4];

void __real_packet_handle_init(void);
void __real_motors_init(void);
#ifdef LAB03_SPEED_LOOP
void speed_control_init(void);
void speed_control_set_gains(float kf, float kp, float ki);
#endif

static packet_handle hiwonder_motor_handle;   /* the factory PACKET_FUNC_MOTOR handler */
static volatile uint8_t report_period_ms;     /* 0 = off */
static volatile uint16_t watchdog_ms;         /* 0 = off */
static volatile uint32_t last_motor_cmd;      /* osKernelGetTickCount() of the last motor command */

#pragma pack(1)
typedef struct {
    int32_t count;
    float   rps;
    float   target_rps;
    int16_t pwm;
} MotorReportTypeDef;

typedef struct {
    uint8_t sub_cmd;                          /* 0x10 */
    MotorReportTypeDef motor[4];
} EncoderReportTypeDef;

typedef struct {
    uint8_t sub_cmd;                          /* 0x12 */
    uint8_t motor_id;
    int32_t ticks_per_circle;
    float   rps_limit;
    float   kp, ki, kd;
} MotorParamCommandTypeDef;
#pragma pack()

/* Target 0, PWM 0, PID history cleared - with interrupts off, so the 100 Hz
 * control interrupt (TIM7_IRQHandler) can't run in the middle. */
static void hard_stop(int i)
{
    if (motors[i] == NULL) {
        return;
    }
    __disable_irq();
    motors[i]->pid_controller.set_point = 0.0f;
    motors[i]->pid_controller.previous_0_err = 0.0f;
    motors[i]->pid_controller.previous_1_err = 0.0f;
    motors[i]->pid_controller.output = 0.0f;
    motors[i]->current_pulse = 0;
    motors[i]->set_pulse(motors[i], 0);
    __enable_irq();
}

/* The factory firmware only sets up the motors on its first motor command
 * (motors[] is NULL before that). Send it a harmless "stop no motors". */
static void ensure_motors_ready(void)
{
    if (motors[0] == NULL && hiwonder_motor_handle != NULL) {
        struct PacketRawFrame f;
        memset(&f, 0, sizeof(f));
        f.function = PACKET_FUNC_MOTOR;
        f.data_length = 2;
        f.data_and_checksum[0] = 0x03;        /* stop by mask */
        f.data_and_checksum[1] = 0x00;        /* mask 0: nothing */
        hiwonder_motor_handle(&f);
    }
}

static void motor_handle(struct PacketRawFrame *frame)
{
    uint8_t *d = frame->data_and_checksum;
    last_motor_cmd = osKernelGetTickCount();
    switch (d[0]) {
    case 0x10:
        if (frame->data_length >= 2) {
            ensure_motors_ready();
            report_period_ms = (d[1] != 0 && d[1] < 10) ? 10 : d[1];
        }
        break;
    case 0x11:
        if (frame->data_length >= 3) {
            watchdog_ms = (uint16_t)(d[1] | (d[2] << 8));
        }
        break;
    case 0x12:
        if (frame->data_length >= sizeof(MotorParamCommandTypeDef)) {
            MotorParamCommandTypeDef c;
            memcpy(&c, d, sizeof(c));
            ensure_motors_ready();
            for (int i = 0; i < 4; ++i) {
                if (c.motor_id == 0xFF || c.motor_id == i) {
                    motors[i]->ticks_per_circle = c.ticks_per_circle;
                    motors[i]->rps_limit = c.rps_limit;
                    motors[i]->pid_controller.kp = c.kp;
                    motors[i]->pid_controller.ki = c.ki;
                    motors[i]->pid_controller.kd = c.kd;
                }
            }
        }
        break;
#ifdef LAB03_SPEED_LOOP
    case 0x13:
        if (frame->data_length >= 13) {
            float g[3];
            memcpy(g, &d[1], sizeof(g));
            speed_control_set_gains(g[0], g[1], g[2]);
        }
        break;
#endif
    default:
        if (hiwonder_motor_handle != NULL) {
            hiwonder_motor_handle(frame);
        }
        if (motors[0] == NULL) {
            break;
        }
        if (d[0] == 0x00 || d[0] == 0x01 || d[0] == 0x02) {   /* one motor, several, stop one */
            for (int i = 0; i < 4; ++i) {
                if (motors[i]->pid_controller.set_point == 0.0f && motors[i]->current_pulse != 0) {
                    hard_stop(i);
                }
            }
        } else if (d[0] == 0x03) {                           /* stop by mask */
            for (int i = 0; i < 4; ++i) {
                if (d[1] & (1u << i)) {
                    hard_stop(i);
                }
            }
        }
        break;
    }
}

static void report_task_entry(void *argument)
{
    (void)argument;
    EncoderReportTypeDef r;
    uint32_t last_report = 0;
    for (;;) {
        osDelay(10);
        if (motors[0] == NULL) {
            continue;
        }
        uint32_t now = osKernelGetTickCount();     /* 1 tick = 1 ms */
        uint16_t wd = watchdog_ms;
        if (wd != 0 && now - last_motor_cmd > wd) {
            for (int i = 0; i < 4; ++i) {
                if (motors[i]->pid_controller.set_point != 0.0f || motors[i]->current_pulse != 0) {
                    hard_stop(i);
                }
            }
        }
        uint8_t period = report_period_ms;
        if (period == 0 || now - last_report < period) {
            continue;
        }
        last_report = now;
        r.sub_cmd = 0x10;
        for (int i = 0; i < 4; ++i) {
            r.motor[i].count = (int32_t)motors[i]->counter;
            r.motor[i].rps = motors[i]->rps;
            r.motor[i].target_rps = motors[i]->pid_controller.set_point;
            r.motor[i].pwm = (int16_t)motors[i]->current_pulse;
        }
        packet_transmit(&packet_controller, PACKET_FUNC_MOTOR, &r, sizeof(r));
    }
}

void __wrap_packet_handle_init(void)
{
    static const osThreadAttr_t attr = {
        .name = "encoder_report",
        .stack_size = 128 * 4,
        .priority = (osPriority_t)osPriorityBelowNormal,
    };
    __real_packet_handle_init();
    hiwonder_motor_handle = packet_controller.handles[PACKET_FUNC_MOTOR];
    packet_register_callback(&packet_controller, PACKET_FUNC_MOTOR, motor_handle);
    osThreadNew(report_task_entry, NULL, &attr);
}

void __wrap_motors_init(void)
{
    __real_motors_init();
    HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);   /* M4 encoder, missing in the factory code */
#ifdef LAB03_SPEED_LOOP
    speed_control_init();                             /* our pins, timers and 100 Hz loop */
#endif
}
