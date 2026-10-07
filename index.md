---
layout: default
title: Home
---

# RPi5 + ROS 2 + RRC Lite
## Raspberry Pi 5 · Ubuntu Server 24.04 LTS · ROS 2 Jazzy · Hiwonder RRC Lite

```
> Computer:    Raspberry Pi 5 (4, 8 or 16 GB), headless
> OS:          Ubuntu Server 24.04 LTS (64-bit, arm64)
> ROS:         ROS 2 Jazzy Jalisco, ros-base
> Controller:  Hiwonder RRC Lite - STM32F407VET6, USB-C serial link to the Pi at 1 Mbaud
```

---

## Labs

| Lab | Topic |
|-----|-------|
| [Lab 01 — Raspberry Pi 5: Ubuntu Server & ROS 2](Lab_01/) | Flash Ubuntu Server 24.04, join the Wi-Fi router, connect over SSH, static Wi-Fi IP, update, swap, then install `ros-jazzy-ros-base` and the build tools and build a first workspace |
| [Lab 02 — RRC Lite Firmware](Lab_02/) | The controller's serial protocol, find out which firmware it runs, back it up, and flash new firmware **from Linux** with `stm32flash` over the same USB-C cable; then run Hiwonder's `ros_robot_controller` ROS 2 node |
| [Lab 03 — Encoder Motors & Speed Control](Lab_03/) | Pins, timers and encoder counts behind the speed control (3960 counts per turn for a JGB37-520), build the firmware on the Pi with GCC, add encoder read-back and a command watchdog, test both motors, and run this lab's own speed controller |

---

## The hardware

| Part | What it does |
|---|---|
| **Raspberry Pi 5** | runs Ubuntu, ROS 2 and your robot code |
| **Hiwonder RRC Lite** | an **STM32F407VET6** microcontroller board: 4 encoder motors, PWM servos, serial bus servos, IMU (QMI8658), buzzer, LED, keys, battery voltage, SBUS and USB gamepad input |
| **USB-A to USB-C data cable** | from the RRC Lite's **UART1** Type-C port to a Pi 5 USB port. A **CH9102F** chip on the board turns it into a serial port: `/dev/ttyACM0` on the Pi |
| **USB-C to USB-C power cable** | from the RRC Lite's **5 V / 5 A PD output** to the Pi 5's power input: the battery powers the Pi |

That one cable does two jobs:

| Job | Who listens on the STM32 side | Speed |
|---|---|---|
| Normal running: ROS 2 ↔ controller | Hiwonder's firmware on USART1 | 1 000 000 baud, `0xAA 0x55` packets (Lab 02, Part 2) |
| Flashing new firmware | the STM32's built-in ROM **bootloader**, on the same USART1 pins (PA9/PA10) | 115 200 baud, ST's AN3155 protocol (Lab 02, Part 5) |

The board's auto-download circuit lets the Pi switch between the two by toggling the
CH9102F's **DTR** and **RTS** lines (RTS → BOOT0, RTS + DTR → RESET), so you don't have
to press the board's **BOOT** and **RST** buttons. Lab 02 walks through the circuit on the
schematic.

---

## Why these versions?

The **Raspberry Pi 5 is not supported by Ubuntu 22.04**: its chips need a newer kernel than
22.04 ships, and Canonical has no plans to add it. Ubuntu's first LTS certified for the
Pi 5 is **24.04 "Noble"**. The ROS 2 release built for 24.04 is **Jazzy Jalisco**, an LTS release
supported until May 2029, with ready-made `apt` packages for **arm64**. So you don't have
to compile ROS 2 from source.

Hiwonder's ROS 2 package (`ros_robot_controller`) is plain Python plus `pyserial`. It was
written for Humble, but it runs on Jazzy unchanged.
