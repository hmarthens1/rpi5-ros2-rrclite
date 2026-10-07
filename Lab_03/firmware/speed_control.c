/**
 * speed_control.c - Lab 03: a complete encoder-motor speed controller for the
 * Hiwonder RRC Lite (STM32F407VET6), written for this lab.
 *
 * Built in with:  make SRC=... SPEED_LOOP=lab03
 * It then REPLACES Hiwonder's speed loop (their TIM7_IRQHandler in stm32f4xx_it.c), while the rest of
 * the firmware - the 0xAA 0x55 protocol, IMU, battery, servos - stays theirs. The Pi
 * still sets targets with the normal motor commands; encoder_report.c still reports.
 *
 * ---------------------------------------------------------------------------------
 * 1. Hardware (from the schematic and Hiwonder's CubeMX file RosRobotControllerM4.ioc)
 * ---------------------------------------------------------------------------------
 * Clocks: 16 MHz crystal -> PLL (M=8, N=168, P=2) -> SYSCLK 168 MHz
 *         APB1 = 42 MHz -> APB1 timer clock 84 MHz  (TIM2, TIM3, TIM4, TIM5, TIM7)
 *         APB2 = 84 MHz -> APB2 timer clock 168 MHz (TIM1, TIM9, TIM10, TIM11)
 *
 * Each motor has a two-input H-bridge (IN1/IN2, one PWM on each input) and a
 * two-channel (A/B) Hall encoder:
 *
 *   motor  PWM "forward"     PWM "reverse"     encoder A / B           encoder timer
 *   M1     TIM1_CH4  PE14    TIM1_CH3  PE13    PA0  / PA1   (AF2)      TIM5 (32-bit)
 *   M2     TIM1_CH2  PE11    TIM1_CH1  PE9     PA15 / PB3   (AF1)      TIM2 (32-bit)
 *   M3     TIM9_CH1  PE5     TIM9_CH2  PE6     PD12 / PD13  (AF2)      TIM4 (16-bit)
 *   M4     TIM11_CH1 PB9     TIM10_CH1 PB8     PB4  / PB5   (AF2)      TIM3 (16-bit)
 *   (TIM1 = AF1, TIM9/10/11 = AF3)
 *
 *   PWM:      PSC 839, ARR 999 at 168 MHz -> 200 kHz count, 1000 steps, 200 Hz.
 *             Duty 0..1000 on ONE input, the other input at 0 -> direction.
 *   Encoder:  encoder mode TI12: the timer counts every edge of A and B
 *             (x4 decoding) and counts down when B leads A. ARR 60000.
 *   Control:  TIM7, PSC 83, ARR 9999 at 84 MHz -> 1 MHz count, 100 Hz interrupt.
 *
 * ---------------------------------------------------------------------------------
 * 2. Counts per turn - the number the speed controller needs
 * ---------------------------------------------------------------------------------
 *   ticks_per_circle = encoder lines x 4 (x4 decoding) x gear ratio
 *   JGB37-520 (Hiwonder "JGB520"):  11 x 4 x 90 = 3960 counts per output-shaft turn
 *   speed [rev/s] = (counts this period) / ticks_per_circle / 0.01 s
 *   One count at 100 Hz = 1/3960/0.01 = 0.025 rev/s: the speed reading is grainy,
 *   so it is low-pass filtered.
 *
 * ---------------------------------------------------------------------------------
 * 3. The controller (every 10 ms, per motor)
 * ---------------------------------------------------------------------------------
 *   delta   = counter now - counter before   (wrapped to the timer's range)
 *   speed   = 0.7 * speed + 0.3 * delta / tpc / dt          (low-pass)
 *   error   = target - speed
 *   integ  += error * dt                (frozen while the output is saturated)
 *   pwm     = kf * target + kp * error + ki * integ          (feed-forward + PI)
 *   pwm     = clamp(pwm, -1000, 1000)
 *   target == 0  ->  pwm = 0, integ = 0   (a stop is always a real stop)
 *
 *   Unlike Hiwonder's incremental loop (pwm += PID output), this "positional" form
 *   cannot keep a stale PWM when the motor is stalled: target 0 is always PWM 0.
 *   Feed-forward kf does most of the work (about 600 PWM per rev/s for a JGB37-520
 *   on 8 V, measured in Lab 03, Part 5); the PI term removes the remaining error.
 */
#include "tim.h"
#include "gpio.h"
#include "encoder_motor.h"

#ifndef SC_KF
#define SC_KF   600.0f   /* PWM per rev/s (feed-forward) */
#endif
#ifndef SC_KP
#define SC_KP   400.0f   /* PWM per rev/s of error */
#endif
#ifndef SC_KI
#define SC_KI   1500.0f  /* PWM per (rev/s * s) of accumulated error */
#endif
#define SC_DT       0.01f   /* control period, s (TIM7 at 100 Hz) */
#define SC_PWM_MAX  1000
#define SC_ENC_ARR  60000u  /* encoder timers count 0..60000 */

extern EncoderMotorObjectTypeDef *motors[4];   /* Hiwonder's motor objects: target, report fields */

typedef struct {
    TIM_HandleTypeDef *pwm_fwd_tim; uint32_t pwm_fwd_ch;
    TIM_HandleTypeDef *pwm_rev_tim; uint32_t pwm_rev_ch;
    TIM_HandleTypeDef *enc_tim;
} MotorHwTypeDef;

static const MotorHwTypeDef hw[4] = {
    { &htim1,  TIM_CHANNEL_4, &htim1,  TIM_CHANNEL_3, &htim5 },   /* M1 */
    { &htim1,  TIM_CHANNEL_2, &htim1,  TIM_CHANNEL_1, &htim2 },   /* M2 */
    { &htim9,  TIM_CHANNEL_1, &htim9,  TIM_CHANNEL_2, &htim4 },   /* M3 */
    { &htim11, TIM_CHANNEL_1, &htim10, TIM_CHANNEL_1, &htim3 },   /* M4 */
};

typedef struct {
    uint32_t last_cnt;
    int64_t  count;      /* total counts since start */
    float    speed;      /* rev/s, filtered */
    float    integ;
    int      pwm;
} MotorStateTypeDef;

static MotorStateTypeDef st[4];
static float gain_kf = SC_KF, gain_kp = SC_KP, gain_ki = SC_KI;
static volatile int sc_ready;

/* ------------------------------------------------------------------ GPIO + timers */

static void gpio_af(GPIO_TypeDef *port, uint32_t pins, uint32_t af, uint32_t pull)
{
    GPIO_InitTypeDef g = {0};
    g.Pin = pins;
    g.Mode = GPIO_MODE_AF_PP;
    g.Pull = pull;
    g.Speed = GPIO_SPEED_FREQ_LOW;
    g.Alternate = af;
    HAL_GPIO_Init(port, &g);
}

static void pwm_timer_init(TIM_HandleTypeDef *h, TIM_TypeDef *inst, const uint32_t *channels, int n)
{
    TIM_OC_InitTypeDef oc = {0};
    h->Instance = inst;
    h->Init.Prescaler = 839;                    /* 168 MHz / 840 = 200 kHz */
    h->Init.CounterMode = TIM_COUNTERMODE_UP;
    h->Init.Period = SC_PWM_MAX - 1;            /* 1000 steps -> 200 Hz */
    h->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    h->Init.RepetitionCounter = 0;
    h->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    HAL_TIM_PWM_Init(h);
    oc.OCMode = TIM_OCMODE_PWM1;                /* output high while CNT < CCR */
    oc.Pulse = 0;
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_ENABLE;
    for (int i = 0; i < n; ++i) {
        HAL_TIM_PWM_ConfigChannel(h, &oc, channels[i]);
        HAL_TIM_PWM_Start(h, channels[i]);
    }
}

static void encoder_timer_init(TIM_HandleTypeDef *h, TIM_TypeDef *inst)
{
    TIM_Encoder_InitTypeDef e = {0};
    h->Instance = inst;
    h->Init.Prescaler = 0;
    h->Init.CounterMode = TIM_COUNTERMODE_UP;
    h->Init.Period = SC_ENC_ARR;
    h->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    h->Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    e.EncoderMode = TIM_ENCODERMODE_TI12;       /* count on A and B edges: x4 */
    e.IC1Polarity = TIM_ICPOLARITY_RISING;
    e.IC1Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC1Prescaler = TIM_ICPSC_DIV1;
    e.IC1Filter = 6;                            /* a little noise filtering on the Hall signals */
    e.IC2Polarity = TIM_ICPOLARITY_RISING;
    e.IC2Selection = TIM_ICSELECTION_DIRECTTI;
    e.IC2Prescaler = TIM_ICPSC_DIV1;
    e.IC2Filter = 6;
    HAL_TIM_Encoder_Init(h, &e);
    HAL_TIM_Encoder_Start(h, TIM_CHANNEL_ALL);
}

/* Called once, the first time the Pi sends a motor command (from __wrap_motors_init,
 * after Hiwonder's motors_init()). Sets up every pin and timer the motors use. */
void speed_control_init(void)
{
    static const uint32_t tim1_ch[] = { TIM_CHANNEL_1, TIM_CHANNEL_2, TIM_CHANNEL_3, TIM_CHANNEL_4 };
    static const uint32_t tim9_ch[] = { TIM_CHANNEL_1, TIM_CHANNEL_2 };
    static const uint32_t ch1[] = { TIM_CHANNEL_1 };

    sc_ready = 0;
    __HAL_RCC_GPIOA_CLK_ENABLE(); __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE(); __HAL_RCC_GPIOE_CLK_ENABLE();
    __HAL_RCC_TIM1_CLK_ENABLE();  __HAL_RCC_TIM2_CLK_ENABLE();  __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();  __HAL_RCC_TIM5_CLK_ENABLE();  __HAL_RCC_TIM7_CLK_ENABLE();
    __HAL_RCC_TIM9_CLK_ENABLE();  __HAL_RCC_TIM10_CLK_ENABLE(); __HAL_RCC_TIM11_CLK_ENABLE();

    /* PWM outputs to the H-bridges */
    gpio_af(GPIOE, GPIO_PIN_9 | GPIO_PIN_11 | GPIO_PIN_13 | GPIO_PIN_14, GPIO_AF1_TIM1, GPIO_NOPULL);
    gpio_af(GPIOE, GPIO_PIN_5 | GPIO_PIN_6, GPIO_AF3_TIM9, GPIO_NOPULL);
    gpio_af(GPIOB, GPIO_PIN_8, GPIO_AF3_TIM10, GPIO_NOPULL);
    gpio_af(GPIOB, GPIO_PIN_9, GPIO_AF3_TIM11, GPIO_NOPULL);
    pwm_timer_init(&htim1, TIM1, tim1_ch, 4);
    __HAL_TIM_MOE_ENABLE(&htim1);               /* TIM1 is an "advanced" timer: main output enable */
    pwm_timer_init(&htim9, TIM9, tim9_ch, 2);
    pwm_timer_init(&htim10, TIM10, ch1, 1);
    pwm_timer_init(&htim11, TIM11, ch1, 1);

    /* Encoder inputs (pull-ups: the Hall sensors have open-collector outputs) */
    gpio_af(GPIOA, GPIO_PIN_0 | GPIO_PIN_1, GPIO_AF2_TIM5, GPIO_PULLUP);
    gpio_af(GPIOA, GPIO_PIN_15, GPIO_AF1_TIM2, GPIO_PULLUP);
    gpio_af(GPIOB, GPIO_PIN_3, GPIO_AF1_TIM2, GPIO_PULLUP);
    gpio_af(GPIOD, GPIO_PIN_12 | GPIO_PIN_13, GPIO_AF2_TIM4, GPIO_PULLUP);
    gpio_af(GPIOB, GPIO_PIN_4 | GPIO_PIN_5, GPIO_AF2_TIM3, GPIO_PULLUP);
    encoder_timer_init(&htim5, TIM5);
    encoder_timer_init(&htim2, TIM2);
    encoder_timer_init(&htim4, TIM4);
    encoder_timer_init(&htim3, TIM3);

    for (int i = 0; i < 4; ++i) {
        st[i].last_cnt = __HAL_TIM_GET_COUNTER(hw[i].enc_tim);
        st[i].count = 0; st[i].speed = 0; st[i].integ = 0; st[i].pwm = 0;
    }

    /* 100 Hz control interrupt: 84 MHz / 84 / 10000 */
    htim7.Instance = TIM7;
    htim7.Init.Prescaler = 83;
    htim7.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim7.Init.Period = 9999;
    htim7.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    HAL_TIM_Base_Init(&htim7);
    HAL_NVIC_SetPriority(TIM7_IRQn, 5, 0);
    HAL_NVIC_EnableIRQ(TIM7_IRQn);
    sc_ready = 1;
    HAL_TIM_Base_Start_IT(&htim7);
}

void speed_control_set_gains(float kf, float kp, float ki)
{
    gain_kf = kf; gain_kp = kp; gain_ki = ki;
}

/* ------------------------------------------------------------------ PWM output */

static void set_pwm(int i, int pwm)
{
    const MotorHwTypeDef *m = &hw[i];
    uint32_t duty = (uint32_t)(pwm >= 0 ? pwm : -pwm);
    if (pwm >= 0) {
        __HAL_TIM_SET_COMPARE(m->pwm_rev_tim, m->pwm_rev_ch, 0);
        __HAL_TIM_SET_COMPARE(m->pwm_fwd_tim, m->pwm_fwd_ch, duty);
    } else {
        __HAL_TIM_SET_COMPARE(m->pwm_fwd_tim, m->pwm_fwd_ch, 0);
        __HAL_TIM_SET_COMPARE(m->pwm_rev_tim, m->pwm_rev_ch, duty);
    }
}

/* ------------------------------------------------------------------ 100 Hz loop */

static void control_step(int i)
{
    EncoderMotorObjectTypeDef *mo = motors[i];
    MotorStateTypeDef *s = &st[i];

    /* 1. measure: counts since last time, wrapped to the 0..60000 counter range */
    uint32_t cnt = __HAL_TIM_GET_COUNTER(hw[i].enc_tim);
    int32_t delta = (int32_t)cnt - (int32_t)s->last_cnt;
    if (delta >  (int32_t)(SC_ENC_ARR / 2)) delta -= (int32_t)(SC_ENC_ARR + 1);
    if (delta < -(int32_t)(SC_ENC_ARR / 2)) delta += (int32_t)(SC_ENC_ARR + 1);
    s->last_cnt = cnt;
    /* Hiwonder's motor profiles flip the encoder direction with a negative gain (JGA27) */
    if (mo->pid_controller.kp < 0.0f) delta = -delta;
    s->count += delta;
    float tpc = mo->ticks_per_circle > 0 ? (float)mo->ticks_per_circle : 3960.0f;
    s->speed = 0.7f * s->speed + 0.3f * ((float)delta / tpc / SC_DT);

    /* 2. control */
    float target = mo->pid_controller.set_point;
    if (target >  mo->rps_limit) target =  mo->rps_limit;
    if (target < -mo->rps_limit) target = -mo->rps_limit;
    int pwm;
    if (target == 0.0f) {
        s->integ = 0.0f;
        pwm = 0;
    } else {
        float err = target - s->speed;
        float out = gain_kf * target + gain_kp * err + gain_ki * (s->integ + err * SC_DT);
        if (out > SC_PWM_MAX)       out = SC_PWM_MAX;
        else if (out < -SC_PWM_MAX) out = -SC_PWM_MAX;
        else s->integ += err * SC_DT;          /* anti-windup: integrate only when not saturated */
        pwm = (int)out;
    }
    s->pwm = pwm;
    set_pwm(i, pwm);

    /* 3. publish into Hiwonder's motor object, so encoder_report.c reports our numbers */
    mo->counter = s->count;
    mo->rps = s->speed;
    mo->current_pulse = pwm;
}

/* Replaces Hiwonder's TIM7_IRQHandler: the Makefile makes theirs weak (objcopy
 * --weaken-symbol), so this strong definition is the one the vector table uses. */
void TIM7_IRQHandler(void)
{
    if (__HAL_TIM_GET_FLAG(&htim7, TIM_FLAG_UPDATE) != RESET) {
        __HAL_TIM_CLEAR_FLAG(&htim7, TIM_FLAG_UPDATE);
        if (!sc_ready || motors[0] == NULL) {
            return;
        }
        for (int i = 0; i < 4; ++i) {
            control_step(i);
        }
    }
}
