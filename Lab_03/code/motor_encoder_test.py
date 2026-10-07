#!/usr/bin/env python3
# =============================================================================
# RPi5 Lab 03 - Test the RRC Lite's encoder motors and speed control
# =============================================================================
# Needs the Lab 03 firmware (build/rrclite_lab03.hex): it adds an encoder report
# to Hiwonder's protocol. The factory firmware has no way to read the encoders.
#
# For each motor it checks, at a few target speeds:
#   - the encoder counts move, and in the commanded direction
#   - ONLY that motor's encoder moves      (catches swapped motor plugs)
#   - the measured speed settles on the target (the PID works)
#   - counts/s / ticks_per_circle agrees with the firmware's rps
#
# USAGE (wheels OFF the ground)
#   python3 motor_encoder_test.py                      # M1 and M2, JGB37-520 motors
#   python3 motor_encoder_test.py --motors 1 2 3 4
#   python3 motor_encoder_test.py --turns 1 --motors 1 # one wheel turn by counting:
#                                                      # mark the wheel and watch
#   python3 motor_encoder_test.py --type JGA27         # another motor profile
#
# Safety: a motor that races past its target (wrong encoder direction, wrong
# PID sign) is stopped and the board is reset, which switches the driver off.
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

# Motor profiles in Hiwonder's firmware (Hiwonder/Portings/motors_param.h),
# selected with motor sub-command 5. ticks = encoder counts per output-shaft turn.
PROFILES = {
    "JGB520": (0, 3960),   # JGB37-520, 1:90, 11-line encoder: 11 x 4 x 90
    "JGB37":  (1, 1980),
    "JGA27":  (2, 1040),
    "JGB528": (3, 5764),
}
FUNC_MOTOR = 3
REPORT_MS = 50
WATCHDOG_MS = 300   # firmware stops all motors if no command arrives for this long


def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8C if crc & 1 else crc >> 1
    return crc


def frame(func, data):
    body = bytes([func, len(data)]) + bytes(data)
    return b"\xAA\x55" + body + bytes([crc8(body)])


class Board:
    def __init__(self, port):
        self.s = serial.Serial()
        self.s.port, self.s.baudrate, self.s.timeout = port, 1000000, 0.02
        self.s.dtr, self.s.rts = True, False        # BOOT0 low, no reset (Lab 02, Part 6.2)
        self.s.open()
        self.buf = bytearray()
        self.last = None                            # last encoder report
        self.battery = None

    def send(self, data):
        self.s.write(frame(FUNC_MOTOR, data))

    def poll(self):
        """Read what has arrived; keep the newest encoder report."""
        self.buf += self.s.read(4096)
        out = []
        while True:
            i = self.buf.find(b"\xAA\x55")
            if i < 0:
                del self.buf[:-1]
                return out
            if len(self.buf) < i + 5:
                del self.buf[:i]
                return out
            func, n = self.buf[i + 2], self.buf[i + 3]
            end = i + 4 + n + 1
            if len(self.buf) < end:
                del self.buf[:i]
                return out
            body, crc = bytes(self.buf[i + 2:end - 1]), self.buf[end - 1]
            del self.buf[:end]
            if crc8(body) != crc:
                continue
            data = body[2:]
            if func == FUNC_MOTOR and len(data) == 57 and data[0] == 0x10:
                m = [struct.unpack_from("<iffh", data, 1 + 14 * k) for k in range(4)]
                self.last = (time.time(), m)
                out.append(self.last)
            elif func == 0 and len(data) == 3 and data[0] == 4:
                self.battery = struct.unpack("<H", data[1:])[0] / 1000

    def collect(self, secs, guard=None, keepalive=None):
        rows, end, next_ka = [], time.time() + secs, 0
        while time.time() < end:
            if keepalive and time.time() >= next_ka:   # resend the command: feeds the watchdog
                keepalive()
                next_ka = time.time() + 0.1
            for r in self.poll():
                rows.append(r)
                if guard:
                    guard(r)
        return rows

    def speed(self, motor, rps):
        self.send(struct.pack("<BBf", 0x00, motor - 1, rps))

    def stop_all(self):
        self.send([0x03, 0x0F])

    def reset(self):
        """Emergency stop: reset the STM32. Motors stay off until the next motor command."""
        self.s.rts, self.s.dtr = True, False
        time.sleep(0.1)
        self.s.rts = False
        time.sleep(0.1)
        self.s.dtr = True


class Runaway(Exception):
    pass


def main():
    ap = argparse.ArgumentParser(description="RRC Lite encoder motor test (Lab 03 firmware)")
    ap.add_argument("--port", default="/dev/rrclite" if os.path.exists("/dev/rrclite") else "/dev/ttyACM0")
    ap.add_argument("--motors", type=int, nargs="+", default=[1, 2], choices=[1, 2, 3, 4])
    ap.add_argument("--type", default="JGB520", choices=PROFILES, help="motor profile (default JGB520 = JGB37-520)")
    ap.add_argument("--speeds", type=float, nargs="+", default=[0.3, 0.5, -0.5], help="targets in rev/s")
    ap.add_argument("--secs", type=float, default=3.0, help="seconds per step")
    ap.add_argument("--turns", type=float, default=0, help="instead: turn each motor this many turns by counting")
    a = ap.parse_args()

    type_id, tpc = PROFILES[a.type]
    b = Board(a.port)
    try:
        b.send([0x10, REPORT_MS])                   # encoder report on (also sets up the motors)
        time.sleep(0.2)
        b.send([0x11] + list(struct.pack("<H", WATCHDOG_MS)))   # stop the motors if we go quiet
        b.send([0x05, type_id])                     # motor profile - ALWAYS before any speed
        b.stop_all()                                # hard stop: PWM 0, PID cleared
        idle = b.collect(1.0)
        if not idle:
            sys.exit("No encoder report. Is the Lab 03 firmware flashed? (bash flash_rrclite.sh compare build/rrclite_lab03.hex)")
        print("Port %s, profile %s (%d counts per turn), battery %s V, %d reports/s"
              % (a.port, a.type, tpc, b.battery, len(idle)))
        moving = [k + 1 for k in range(4) if idle[-1][1][k][0] != idle[0][1][k][0]]
        if moving:
            print("!! encoders M%s count while idle - motor turning, or noise on the encoder lines" % moving)

        def guard_for(motor, target):
            state = {"since": None}

            def guard(r):
                rps = r[1][motor - 1][1]
                bad = abs(rps) > abs(target) * 1.8 + 0.4 or (abs(rps) > 0.3 and rps * target < 0)
                if bad:
                    state["since"] = state["since"] or r[0]
                    if r[0] - state["since"] > 0.6:
                        raise Runaway("M%d at %.2f rev/s for target %.2f" % (motor, rps, target))
                else:
                    state["since"] = None
            return guard

        results = []
        for motor in a.motors:
            k = motor - 1
            if a.turns:
                target = 0.4 if a.turns > 0 else -0.4
                start = b.collect(0.3)[-1][1][k][0]
                goal = int(abs(a.turns) * tpc)
                input("M%d: mark the wheel, then press Enter to turn it %.2f turn(s) (%d counts) " % (motor, a.turns, goal))
                b.speed(motor, target)
                guard = guard_for(motor, target)
                t_end = time.time() + abs(a.turns) / 0.4 * 2 + 3
                done = 0
                next_ka = 0
                while time.time() < t_end:
                    if time.time() >= next_ka:
                        b.speed(motor, target)
                        next_ka = time.time() + 0.1
                    for r in b.poll():
                        guard(r)
                        done = abs(r[1][k][0] - start)
                    if done >= goal:
                        break
                b.speed(motor, 0)
                rest = b.collect(1.0)
                total = abs(rest[-1][1][k][0] - start)
                print("M%d: stopped at %d counts, coasted to %d = %.3f turns. Did the mark come back round?"
                      % (motor, done, total, total / tpc))
                continue

            for target in a.speeds:
                b.speed(motor, target)
                rows = b.collect(a.secs, guard_for(motor, target), lambda: b.speed(motor, target))
                b.speed(motor, 0)
                b.collect(0.8)
                steady = [r for r in rows if r[0] - rows[0][0] > 1.0]       # skip the first second
                if len(steady) < 5:
                    results.append((motor, target, "FAIL", "no reports while running"))
                    continue
                t0, m0 = steady[0]
                t1, m1 = steady[-1]
                counts = m1[k][0] - m0[k][0]
                cps = counts / (t1 - t0)
                rps_counts = cps / tpc
                rps_fw = sum(r[1][k][1] for r in steady) / len(steady)
                pwm = sum(r[1][k][3] for r in steady) / len(steady)
                others = [j + 1 for j in range(4) if j != k and abs(m1[j][0] - m0[j][0]) > 20]
                err = rps_counts - target
                ok = abs(err) <= max(0.1 * abs(target), 0.05) and counts * target > 0 and not others
                note = "counts/s %7.0f  rps(counts) %6.3f  rps(fw) %6.3f  pwm %5.0f" % (cps, rps_counts, rps_fw, pwm)
                if others:
                    note += "  !! encoder of M%s moved too: plugs swapped?" % others
                if counts * target <= 0:
                    note += "  !! encoder counts the wrong way or not at all"
                results.append((motor, target, "PASS" if ok else "FAIL", note))
                print("M%d target %+5.2f r/s: %s  %s" % (motor, target, results[-1][2], note), flush=True)
        b.stop_all()
        if results:
            fails = [r for r in results if r[2] != "PASS"]
            print("\nRESULT: %d/%d steps passed%s" % (len(results) - len(fails), len(results),
                  "" if not fails else " - see the !! notes"))
    except Runaway as e:
        print("\n!! RUNAWAY: %s - resetting the board (motor driver off)" % e)
        b.reset()
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted - stopping")
    finally:
        try:
            b.stop_all()
            b.send([0x10, 0])                       # report off
            b.send([0x11, 0, 0])                    # watchdog off (factory behaviour)
            time.sleep(0.2)
        finally:
            b.s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
