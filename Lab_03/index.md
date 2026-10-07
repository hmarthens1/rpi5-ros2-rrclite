---
layout: default
title: "Lab 03 — Encoder Motors & Speed Control"
---

# Lab 03 — Encoder Motors & Speed Control

**Raspberry Pi 5 · Hiwonder RRC Lite (STM32F407VET6) · JGB37-520 encoder motors · arm-none-eabi-gcc**

**Objectives:** Understand how the RRC Lite drives a DC motor at a set speed: the H-bridge
and its PWM timers, the quadrature encoder and its timer, **encoder counts per turn**, and the
100 Hz control loop. Build the controller firmware **on the Pi** with GCC instead of Keil on
Windows, add an encoder read-back to the serial protocol, flash it, and test both motors.
Then swap in this lab's own speed controller (`speed_control.c`), with the pins and timers
configured in code you can read and change.

---

## Before You Start

- **Labs 01 and 02 are done**: `flash_rrclite.sh info` reaches the bootloader, and you have a
  backup of the factory firmware (Lab 02, Part 7.1)
- Two **Hiwonder JGB37-520** encoder motors on ports **M1** and **M2**, the battery
  connected, the board's switch **ON**
- **Wheels off the ground** for every test in this lab: the robot on a stand, or held

> **Safety first.** A speed controller with a wrong setting — the wrong motor profile, an
> encoder plugged in reversed — does not run a motor slowly: it drives it at **full power**,
> and it keeps going. Everything in this lab is built around that: the test sets the motor
> profile before anything moves, the firmware stops the motors when the Pi goes quiet
> (Part 6), and the test resets the board if a wheel races. Keep your hand near the
> board's power switch anyway. **Switching it OFF always stops the motors.**

---

## Part 1 — How the board runs a motor at a set speed

### 1.1 The parts

```
 Pi ──USB── STM32 ──PWM──> H-bridge ──> DC motor ──gearbox 1:90──> wheel
              ^                            │
              └──── timer in encoder mode ◄┘ Hall encoder, 11 lines, signals A and B
```

| Part | What it does |
|---|---|
| **H-bridge** (one per motor, two inputs IN1/IN2) | PWM on IN1 → forward, PWM on IN2 → backward. Duty cycle = average voltage = speed (roughly) |
| **Hall encoder** on the motor shaft | two square waves, A and B, 90° apart. Which one leads tells the direction |
| **STM32 timer in encoder mode** | counts every edge of A and B in hardware: up one way, down the other |
| **Control loop**, 100 times a second | measures the speed from the counts, compares it with the target, adjusts the PWM |

### 1.2 Pins and timers

From the schematic and Hiwonder's CubeMX file (`RosRobotControllerM4.ioc`):

| Motor | PWM "forward" | PWM "reverse" | Encoder A / B | Encoder timer |
|---|---|---|---|---|
| **M1** | TIM1_CH4 · PE14 | TIM1_CH3 · PE13 | PA0 / PA1 | **TIM5** |
| **M2** | TIM1_CH2 · PE11 | TIM1_CH1 · PE9 | PA15 / PB3 | **TIM2** |
| **M3** | TIM9_CH1 · PE5 | TIM9_CH2 · PE6 | PD12 / PD13 | **TIM4** |
| **M4** | TIM11_CH1 · PB9 | TIM10_CH1 · PB8 | PB4 / PB5 | **TIM3** |

| Timer job | Clock | Setting | Result |
|---|---|---|---|
| PWM (TIM1, 9, 10, 11) | 168 MHz | prescaler 840, period 1000 | 200 Hz PWM, duty 0–1000 |
| Encoders (TIM2–5) | — | encoder mode TI12, period 60000 | counts every A and B edge (×4) |
| Control loop (TIM7) | 84 MHz | prescaler 84, period 10000 | interrupt every **10 ms** (100 Hz) |

The clocks come from a 16 MHz crystal: 16 MHz ÷ 8 × 168 ÷ 2 = 168 MHz system clock; the APB2
timers run at 168 MHz, the APB1 timers at 84 MHz.

### 1.3 Encoder counts per turn — the number the controller needs

```
counts per output-shaft turn = encoder lines × 4 (both edges of A and B) × gear ratio
JGB37-520:                   =      11       ×              4            ×     90     = 3960
```

So one wheel turn = **3960 counts**, and

```
speed [rev/s] = counts in the last 10 ms / 3960 / 0.01 s
```

One count per 10 ms is already 0.025 rev/s, so the speed reading is grainy and the firmware
smooths it (a low-pass filter). In Part 5 you check the 3960 on the real wheel.

Hiwonder's firmware knows four motors (`Hiwonder/Portings/motors_param.h`), selected with
**motor sub-command 5**:

| Profile | Value | Counts per turn | Max speed | PID kp / ki / kd |
|---|---|---|---|---|
| **JGB520** — the JGB37-520, 1:90 | **0** | 3960 | 1.5 rev/s | 63 / 2.6 / 2.4 |
| JGB37 | 1 | 1980 | 3.0 rev/s | 40 / 2.0 / 2.0 |
| JGA27 | 2 | 1040 | 6.0 rev/s | **−36 / −1 / −1** |
| JGB528 | 3 | 5764 | 1.1 rev/s | 300 / 2 / 12 |

> **The factory firmware starts with the JGA27 profile** — negative gains, because that motor's
> encoder counts the other way. On a JGB37-520 this makes the controller push the wrong way:
> a runaway at full power. **Always send the profile first:** `AA 55 03 02 05 00 38`.

### 1.4 Hiwonder's control loop

In `Core/Src/stm32f4xx_it.c`, `TIM7_IRQHandler()` runs every 10 ms. For each motor it calls
`encoder_update()` (counts → `rps`) and `encoder_motor_control()` (`Hiwonder/Peripherals/encoder_motor.c`):

```
pwm = pwm + PID_output(target - rps)       incremental: the PID output is ADDED each time
pwm = clamp(pwm, -1000, 1000), and |pwm| < 250 is sent as 0
```

Things this lab found in the factory firmware, all fixed in the Lab 03 firmware:

| Problem | Effect | Lab 03 fix |
|---|---|---|
| No encoder read-back in the protocol | the Pi can't see speeds or counts | encoder report (Part 6) |
| A stop only sets the **target** to 0 | if the motor couldn't turn (battery off, wheel blocked), the PWM stays where it was — and the motor starts by itself later | stops are hard: PWM 0 and PID cleared |
| No command timeout | if the USB link drops, the last speed command runs forever | command watchdog (sub-command 0x11) |
| Motor 4's encoder timer (TIM3) is never started (`motors_init()` starts TIM4 twice) | M4's speed control can't work | TIM3 started |

---

## Part 2 — Quick check with the factory firmware

No build needed. On the Pi, with the wheels lifted:

```bash
python3 - <<'EOF'
import serial, struct, time
s = serial.Serial(); s.port = '/dev/rrclite'; s.baudrate = 1000000
s.dtr, s.rts = True, False; s.open()          # BOOT0 stays low (Lab 02, Part 6.2)
def crc8(d):
    c = 0
    for b in d:
        c ^= b
        for _ in range(8): c = (c >> 1) ^ 0x8C if c & 1 else c >> 1
    return c
def motor(data):
    body = bytes([3, len(data)]) + bytes(data)
    s.write(b'\xAA\x55' + body + bytes([crc8(body)]))
motor([0x05, 0x00])                           # profile JGB520 first!
for m in (0, 1):                              # M1, M2 (0-based on the wire)
    for v in (0.3, -0.3):
        motor(struct.pack('<BBf', 0x00, m, v)); time.sleep(2)
        motor([0x02, m]); time.sleep(1)
motor([0x03, 0x0F])                           # stop all
EOF
```

Each wheel should turn slowly (about 18 rpm) one way, then the other. The factory firmware
can't tell the Pi what the encoders read, so you judge by eye. For numbers, build the Lab 03
firmware.

---

## Part 3 — Build the firmware on the Pi

Hiwonder's project is for **Keil MDK** on Windows. The STM32 doesn't care which compiler
made its program, so this lab builds the same source with **GCC** on Linux.

### 3.1 Install the ARM toolchain

```bash
sudo apt install -y gcc-arm-none-eabi libnewlib-arm-none-eabi make
arm-none-eabi-gcc --version | head -1          # 13.2 on Ubuntu 24.04
```

### 3.2 Hiwonder's source and this lab's files

From the **laptop**, copy Hiwonder's source folder to the Pi (about 40 MB without Keil's
build output):

```bash
cd "<path>/Appendix/Source Code/RosRobotControllerLite_ros_250814"
tar czf - --exclude=.git --exclude='MDK-ARM/RosRobotControllerM4' RosRobotControllerLite_ros_250811 \
  | ssh robot01-pi5 'mkdir -p ~/rrclite && tar xzf - -C ~/rrclite'
```

On the **Pi**, get this lab's files:

```bash
mkdir -p ~/lab03/firmware ~/lab03/code && cd ~/lab03/firmware
for f in Makefile srcs_list.mk STM32F407VETx_FLASH.ld gcc_syscalls.c encoder_report.c speed_control.c; do
  curl -fsSLO {{ site.github.url }}/Lab_03/firmware/$f
done
cd ~/lab03/code && curl -fsSLO {{ site.github.url }}/Lab_03/code/motor_encoder_test.py
```

| File | What it is |
|---|---|
| ⬇️ [Makefile](firmware/Makefile) | builds Hiwonder's tree with GCC; nothing in that tree is changed |
| ⬇️ [srcs_list.mk](firmware/srcs_list.mk) | the 131 source files Keil compiles (from `RosRobotControllerM4.uvprojx`) |
| ⬇️ [STM32F407VETx_FLASH.ld](firmware/STM32F407VETx_FLASH.ld) | linker script: 512 KB flash at `0x08000000`, 128 KB RAM; the 64 KB CCM RAM is left to the firmware's own allocator |
| ⬇️ [gcc_syscalls.c](firmware/gcc_syscalls.c) | replaces Hiwonder's Keil-only `syscall.c` (`printf` → SEGGER RTT, as before) |
| ⬇️ [encoder_report.c](firmware/encoder_report.c) | encoder report, command watchdog, hard stops, M4 encoder fix (Part 6) |
| ⬇️ [speed_control.c](firmware/speed_control.c) | this lab's own speed controller: pins, timers, measurement, PID (Part 7) |
| ⬇️ [motor_encoder_test.py](code/motor_encoder_test.py) | the test (Part 5) |

### 3.3 Build

```bash
cd ~/lab03/firmware
make SRC=~/rrclite/RosRobotControllerLite_ros_250811 -j4
```

```
  CC  Core/Src/main.c
  ...
  CC  encoder_report.c (lab03)
  LD  build/rrclite_lab03.elf
Memory region         Used Size  Region Size  %age Used
          CCMRAM:          0 GB        64 KB      0.00%
             RAM:       96376 B       128 KB     73.53%
           FLASH:       60296 B       512 KB     11.50%
  HEX build/rrclite_lab03.hex
```

About 20 seconds on a Pi 5. The warnings come from Hiwonder's code (IMU and RTT files) and are
harmless.

How the Makefile adds code **without editing Hiwonder's files**:

| Technique | Used for |
|---|---|
| `-Wl,--wrap=packet_handle_init` | after Hiwonder's protocol setup, `encoder_report.c` puts its handler in front of the motor handler. Unknown sub-commands are passed on unchanged |
| `-Wl,--wrap=motors_init` | after Hiwonder's motor setup: start M4's encoder timer, and (with `SPEED_LOOP=lab03`) set up our speed loop |
| `objcopy --weaken-symbol=TIM7_IRQHandler` | `SPEED_LOOP=lab03` only: Hiwonder's 100 Hz interrupt handler becomes "weak", so the one in `speed_control.c` replaces it |

---

## Part 4 — Flash it

Use Lab 02's script. It checks the `.hex`, then erases, writes, verifies and resets. It
doesn't make a backup, so keep the one from Lab 02, Part 7.1:

```bash
cd ~/lab02
bash flash_rrclite.sh flash ~/lab03/firmware/build/rrclite_lab03.hex
python3 rrclite_probe.py --beep          # battery ~1/s, IMU ~50/s, beep: still the same protocol
```

The Lab 03 firmware is a superset of the factory firmware: Hiwonder's ROS 2 node (Lab 02,
Part 9) works with it unchanged. To go back:

```bash
bash flash_rrclite.sh flash RosRobotControllerLite_ros_250814.hex
bash flash_rrclite.sh compare RosRobotControllerLite_ros_250814.hex     # IDENTICAL
```

---

## Part 5 — Test both motors

Wheels lifted, battery on:

```bash
cd ~/lab03/code
python3 motor_encoder_test.py --motors 1 2
```

Output from the lab's robot (Lab 03 firmware, factory speed loop):

```
Port /dev/rrclite, profile JGB520 (3960 counts per turn), battery 8.07 V, 25 reports/s
M1 target +0.30 r/s: PASS  counts/s    1161  rps(counts)  0.293  rps(fw)  0.292  pwm   275
M1 target +0.50 r/s: PASS  counts/s    1960  rps(counts)  0.495  rps(fw)  0.495  pwm   310
M1 target -0.50 r/s: PASS  counts/s   -1959  rps(counts) -0.495  rps(fw) -0.492  pwm  -309
M2 target +0.30 r/s: PASS  counts/s    1159  rps(counts)  0.293  rps(fw)  0.295  pwm   388
M2 target +0.50 r/s: PASS  counts/s    1972  rps(counts)  0.498  rps(fw)  0.495  pwm   436
M2 target -0.50 r/s: PASS  counts/s   -1969  rps(counts) -0.497  rps(fw) -0.496  pwm  -417

RESULT: 6/6 steps passed
```

For each motor and target speed (3 s each, the first second ignored while it speeds up):

| Column | Meaning | Check |
|---|---|---|
| `counts/s` | encoder counts per second, from the raw counter | sign = direction of the command |
| `rps(counts)` | `counts/s ÷ 3960` — computed **on the Pi** | within 10 % of the target |
| `rps(fw)` | the firmware's own speed estimate | agrees with `rps(counts)` |
| `pwm` | the duty cycle the loop needed (of 1000) | here M2 needs ~40 % more than M1: more friction in its gearbox |

It also fails a step when **another** motor's encoder moves (motor plugs swapped), and it
resets the board if a wheel races past its target (wrong profile, reversed encoder).

**Check the 3960 by eye.** Put a mark on the wheel, then:

```bash
python3 motor_encoder_test.py --motors 1 --turns 1
```

The motor turns until exactly 3960 counts have passed. The mark should come back to where it
started (it coasts a few degrees past). Two turns' worth means the gear ratio is 1:180, half a
turn means 1:45, and so on: then that's the profile to change.

Other options: `--motors 1 2 3 4`, `--speeds 0.2 0.4 -0.4`, `--type JGB37`.

---

## Part 6 — The protocol additions

All in `PACKET_FUNC_MOTOR` (function code 3), so nothing else changes (Lab 02, Part 3):

| Sub-command | Data | Meaning |
|---|---|---|
| `0x10` | `u8 period_ms` | encoder report every `period_ms` (10–255), `0` = off |
| `0x11` | `u16 timeout_ms` | **command watchdog**: no motor command for `timeout_ms` → every motor stops. `0` = off (default) |
| `0x12` | `u8 motor (0–3, 0xFF = all)`, `i32 counts_per_turn`, `f32 max_rps`, `f32 kp`, `f32 ki`, `f32 kd` | set any motor parameters, not just the four profiles |
| `0x13` | `f32 kf`, `f32 kp`, `f32 ki` | gains of this lab's speed loop (`SPEED_LOOP=lab03` only) |

The report the board sends (57 data bytes): `0x10`, then for M1…M4:

| Field | Type | Meaning |
|---|---|---|
| count | `int32` | total encoder counts since power-on |
| rps | `float` | measured speed, rev/s |
| target | `float` | the speed the controller is aiming for |
| pwm | `int16` | duty cycle sent to the H-bridge, −1000…1000 |

Example: turn the report on at 20 Hz: `AA 55 03 02 10 32 ` + CRC. Use the `frame()` function in
`motor_encoder_test.py` to build any of these.

> **Use the watchdog on a robot.** The test turns it on (300 ms) and resends its speed every
> 100 ms. On this lab's robot the USB link has dropped several times with a motor at about
> 1 rev/s, and without the watchdog the last command kept the wheel turning until the battery
> switch was turned off.

---

## Part 7 — This lab's own speed controller

[`speed_control.c`](firmware/speed_control.c) is a complete motor speed controller written for
this lab, with everything in one file you can read top to bottom:

| Section | What it does |
|---|---|
| `speed_control_init()` | turns on the GPIO and timer clocks; sets the PWM pins and encoder pins to their timer functions; configures TIM1/9/10/11 for 200 Hz PWM, TIM2–5 in encoder mode, TIM7 for the 100 Hz interrupt |
| `set_pwm()` | duty on the "forward" or "reverse" input of the H-bridge, the other at 0 |
| `control_step()` | counts since last time (with wrap-around), speed with a low-pass filter, then the controller |
| `TIM7_IRQHandler()` | runs `control_step()` for the four motors every 10 ms |

The controller:

```
error  = target - speed
pwm    = kf × target  +  kp × error  +  ki × ∫error dt         (feed-forward + PI)
pwm    = clamp(pwm, -1000, 1000)        - the integral stops growing while clamped (anti-windup)
target = 0  →  pwm = 0, integral = 0     - a stop is always a real stop
```

The feed-forward term `kf × target` does most of the work: from Part 5, the motors need about
**600 PWM per rev/s** (M1: 310 at 0.5 rev/s). The PI part only fixes what's left, so it can be
gentle and stable. Defaults: `kf = 600`, `kp = 400`, `ki = 1500`.

Build and flash it:

```bash
cd ~/lab03/firmware
make SRC=~/rrclite/RosRobotControllerLite_ros_250811 SPEED_LOOP=lab03 -j4    # build/sc/rrclite_lab03_sc.hex
bash ~/lab02/flash_rrclite.sh flash build/sc/rrclite_lab03_sc.hex
python3 ~/lab03/code/motor_encoder_test.py --motors 1 2
```

The lab's robot with this controller:

```
M1 target +0.30 r/s: PASS  counts/s    1158  rps(counts)  0.293  rps(fw)  0.293  pwm   256
M1 target +0.50 r/s: PASS  counts/s    2022  rps(counts)  0.511  rps(fw)  0.505  pwm   311
M1 target -0.50 r/s: PASS  counts/s   -1991  rps(counts) -0.503  rps(fw) -0.501  pwm  -312
M2 target +0.30 r/s: PASS  counts/s    1115  rps(counts)  0.282  rps(fw)  0.278  pwm   384
M2 target +0.50 r/s: PASS  counts/s    2016  rps(counts)  0.509  rps(fw)  0.504  pwm   446
M2 target -0.50 r/s: PASS  counts/s   -1976  rps(counts) -0.499  rps(fw) -0.497  pwm  -438
RESULT: 6/6 steps passed
```

**Things to try** (change gains without rebuilding: sub-command `0x13`):

1. Set `kf = 0` and watch how much slower the PI controller alone reaches the target.
2. Set `ki = 0`: the steady-state error of a proportional-only controller. M2, with more
   friction, misses by more than M1.
3. Change the PWM frequency from 200 Hz to 20 kHz (prescaler 839 → 7 in `pwm_timer_init()`):
   the motor whine goes away. Does the motor need a different `kf`?
4. Log `count` from the report at 20 Hz while the wheel turns by hand (battery switch OFF,
   USB still connected) to see the encoder without the motor.

---

## Troubleshooting

| Problem | Try this |
|---------|---------|
| `make`: `SRC=... is not Hiwonder's RosRobotControllerLite source folder` | Point `SRC` at the folder that contains `MDK-ARM/` and `Core/` |
| `arm-none-eabi-gcc missing` / `stdio.h: No such file` | `sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi` |
| Test: `No encoder report` | The board runs the factory firmware: flash `build/rrclite_lab03.hex` (Part 4) |
| A wheel races or `!! RUNAWAY` | Wrong profile for the motor (`--type`), or the encoder counts backwards (then `rps(counts)` has the wrong sign at low speed). The test has already reset the board |
| `encoder of M2 moved too: plugs swapped?` | The motor cables or the encoder cables are in different ports. Each motor's cable carries both, so swap the whole cable |
| `encoder counts the wrong way or not at all` | Encoder cable loose, or a different motor type |
| A motor turns when nothing commanded it | It kept a stale PWM (factory firmware, Part 1.4): switch the board OFF. With the Lab 03 firmware a stop always sets PWM 0 |
| The USB link drops (`USB disconnect` in `journalctl -k`) while a motor runs fast | Seen on this lab's robot at ~1 rev/s and still being investigated. The watchdog stops the motors. Reseat the cable, keep test speeds ≤ 0.5 rev/s, and if the port doesn't come back, reboot the Pi |
| `--turns 1` stops at 2 turns / half a turn | The gear ratio isn't 1:90: wrong profile (Part 1.3) |

---

## Completion Checklist

- [ ] You can name each motor's PWM timer and encoder timer, and work out 3960 counts per turn
- [ ] Part 2: both wheels turn slowly both ways with the factory firmware
- [ ] The toolchain is installed and `make` builds `build/rrclite_lab03.hex` on the Pi
- [ ] The Lab 03 firmware is flashed and `rrclite_probe.py --beep` still works
- [ ] `motor_encoder_test.py --motors 1 2` passes 6/6
- [ ] `--turns 1` turns the marked wheel once
- [ ] `SPEED_LOOP=lab03` builds, flashes and passes the same test
- [ ] At least one of the "things to try" in Part 7
- [ ] The board is back on the firmware you want to keep (factory or Lab 03)
