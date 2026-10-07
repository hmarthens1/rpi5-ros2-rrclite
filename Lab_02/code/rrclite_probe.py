#!/usr/bin/env python3
# =============================================================================
# RPi5 Lab 02 - Talk to the Hiwonder RRC Lite over its serial protocol
# =============================================================================
# Answers "what is the board running right now?" without any ROS 2:
#
#   - listens on the serial port at 1 000 000 baud and decodes every frame
#     the firmware sends on its own (battery every ~1 s, IMU ~50 Hz, keys)
#   - optionally sends a buzzer or LED command, so you hear/see it answer
#
# Frame format (both directions), from "RRCLite Communication Protocol with
# the Host Computer Analysis.pdf" and the firmware source (Hiwonder/Misc/packet.c):
#
#   0xAA 0x55 | function (u8) | length (u8) | data (length bytes) | CRC-8
#
#   CRC-8 = Dallas/Maxim CRC-8 (reflected polynomial 0x8C, init 0) over
#           function, length and data. Multi-byte values are little-endian.
#
# USAGE
#   python3 rrclite_probe.py                      # listen 3 s, print a summary
#   python3 rrclite_probe.py --beep               # beep once, then listen
#   python3 rrclite_probe.py --led                # blink the LED 3 times, then listen
#   python3 rrclite_probe.py --seconds 10 --raw   # also print every frame in hex
#   python3 rrclite_probe.py --port /dev/ttyACM0  # another port (default /dev/rrclite,
#                                                 # falling back to /dev/ttyACM0)
#
# Stop the ros_robot_controller node first: only one program can use the port.
# The port is opened with DTR on and RTS off, so BOOT0 stays low (Part 6).
# Needs python3-serial (sudo apt install python3-serial).
# =============================================================================

import argparse
import os
import struct
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial is missing:  sudo apt install python3-serial")

BAUD = 1000000

FUNCS = {
    0: "SYS", 1: "LED", 2: "BUZZER", 3: "MOTOR", 4: "PWM_SERVO", 5: "BUS_SERVO",
    6: "KEY", 7: "IMU", 8: "GAMEPAD", 9: "SBUS", 10: "OLED", 11: "RGB",
}

KEY_EVENTS = {
    0x01: "pressed", 0x02: "long press", 0x04: "long press repeat",
    0x08: "released (long)", 0x10: "released (short)", 0x20: "click",
    0x40: "double click", 0x80: "triple click",
}


def crc8(data):
    """Dallas/Maxim CRC-8, the same values as the table in the Hiwonder SDK."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8C if crc & 1 else crc >> 1
    return crc


def build_frame(func, data):
    body = bytes([func, len(data)]) + bytes(data)
    return b"\xAA\x55" + body + bytes([crc8(body)])


def hexs(b):
    return " ".join("%02X" % x for x in b)


class Parser:
    """Byte-by-byte state machine, like the firmware's packet_recv()."""

    def __init__(self):
        self.state = 0
        self.buf = bytearray()
        self.need = 0
        self.good = 0
        self.bad_crc = 0
        self.junk = 0

    def feed(self, data):
        frames = []
        for b in data:
            if self.state == 0:                     # start byte 1
                if b == 0xAA:
                    self.state = 1
                else:
                    self.junk += 1
            elif self.state == 1:                   # start byte 2
                self.state = 2 if b == 0x55 else 0
            elif self.state == 2:                   # function
                self.buf = bytearray([b])
                self.state = 3
            elif self.state == 3:                   # length
                self.buf.append(b)
                self.need = b
                self.state = 4 if b else 5
            elif self.state == 4:                   # data
                self.buf.append(b)
                self.need -= 1
                if self.need == 0:
                    self.state = 5
            elif self.state == 5:                   # checksum
                if crc8(self.buf) == b:
                    self.good += 1
                    frames.append((self.buf[0], bytes(self.buf[2:]),
                                   b"\xAA\x55" + bytes(self.buf) + bytes([b])))
                else:
                    self.bad_crc += 1
                self.state = 0
        return frames


def describe(func, data):
    name = FUNCS.get(func, "func %d" % func)
    try:
        if func == 0 and len(data) == 3 and data[0] == 0x04:
            mv = struct.unpack("<H", data[1:])[0]
            return "%s battery %.2f V" % (name, mv / 1000)
        if func == 7 and len(data) == 24:
            ax, ay, az, gx, gy, gz = struct.unpack("<6f", data)
            return "%s accel %.2f %.2f %.2f  gyro %.2f %.2f %.2f" % (name, ax, ay, az, gx, gy, gz)
        if func == 6 and len(data) == 2:
            return "%s key %d %s" % (name, data[0], KEY_EVENTS.get(data[1], hex(data[1])))
    except struct.error:
        pass
    return "%s %d bytes" % (name, len(data))


def main():
    ap = argparse.ArgumentParser(description="Probe the Hiwonder RRC Lite firmware over serial")
    ap.add_argument("--port", default=None, help="serial port (default /dev/rrclite, else /dev/ttyACM0)")
    ap.add_argument("--seconds", type=float, default=3.0, help="how long to listen")
    ap.add_argument("--beep", action="store_true", help="send a 1 kHz, 0.1 s beep first")
    ap.add_argument("--led", action="store_true", help="blink LED 1 three times first")
    ap.add_argument("--raw", action="store_true", help="print every frame in hex")
    a = ap.parse_args()

    port = a.port or ("/dev/rrclite" if os.path.exists("/dev/rrclite") else "/dev/ttyACM0")
    try:
        # Auto-download circuit (Lab 02, Part 6): RTS on = BOOT0 high, and
        # RTS on + DTR off = reset. DTR on + RTS off keeps BOOT0 low and never
        # resets, so a reset while the port is open still boots the firmware.
        # pyserial sets DTR before RTS, so there is no reset glitch on open.
        ser = serial.Serial()
        ser.port, ser.baudrate, ser.timeout = port, BAUD, 0.1
        ser.dtr, ser.rts = True, False
        ser.open()
    except serial.SerialException as e:
        sys.exit("Cannot open %s: %s\n"
                 "  - board plugged into the UART1 Type-C port?  ls -l /dev/ttyACM* /dev/rrclite\n"
                 "  - in the dialout group?  groups   (sudo usermod -aG dialout $USER, log in again)\n"
                 "  - port busy?  sudo fuser -v %s   (stop the ROS 2 node)" % (port, e, port))

    print("Port %s at %d baud" % (port, BAUD))
    ser.reset_input_buffer()

    if a.beep:
        f = build_frame(2, struct.pack("<HHHH", 1000, 100, 900, 1))
        print("-> BUZZER  %s" % hexs(f))
        ser.write(f)
    if a.led:
        f = build_frame(1, struct.pack("<BHHH", 1, 100, 100, 3))
        print("-> LED     %s" % hexs(f))
        ser.write(f)

    p = Parser()
    counts = {}
    last = {}
    nbytes = 0
    t_end = time.time() + a.seconds
    while time.time() < t_end:
        data = ser.read(512)
        nbytes += len(data)
        for func, payload, raw in p.feed(data):
            counts[func] = counts.get(func, 0) + 1
            last[func] = payload
            if a.raw:
                print("<- %-40s %s" % (describe(func, payload), hexs(raw)))
    ser.close()

    print("\nReceived %d bytes in %.1f s: %d good frames, %d bad CRC, %d stray bytes"
          % (nbytes, a.seconds, p.good, p.bad_crc, p.junk))
    for func in sorted(counts):
        rate = counts[func] / a.seconds
        print("  %-10s %5d frames  (%5.1f /s)   last: %s"
              % (FUNCS.get(func, func), counts[func], rate, describe(func, last[func])))

    print()
    if p.good:
        print("RESULT: the board runs firmware that speaks Hiwonder's 0xAA 0x55 protocol at 1 Mbaud.")
        if 0 in counts and 7 in counts:
            print("        Battery + IMU reports match the RosRobotControllerLite 'ros' firmware.")
        return 0
    if nbytes:
        print("RESULT: bytes arrive but no valid frames. Wrong baud rate, or a different firmware.")
    else:
        print("RESULT: nothing received. No firmware, the board is waiting in the bootloader")
        print("        (press RST, or: bash flash_rrclite.sh run), or this is not the RRC Lite's port.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
