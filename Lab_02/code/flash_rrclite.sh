#!/bin/bash
# =============================================================================
# RPi5 Lab 02 - Flash the Hiwonder RRC Lite (STM32F407) from Linux
# =============================================================================
# The RRC Lite's USB-C "UART1" port is a CH9102F USB-serial chip wired to the
# STM32's USART1 (PA9/PA10). Those are the pins the STM32's built-in ROM
# bootloader listens on (ST AN2606 / AN3155).
#
# Auto-download circuit (schematic "SCH_Ros Robot Controller Lite V1.0",
# sheet 1, serial/download circuit):
#
#   RTS# -> R10 -> Q4 (SS8550, PNP, emitter 3V3) -> R2 -> BOOT0
#            RTS asserted (pin low)  => BOOT0 high
#   DTR# -> R18 -> base of Q5 (SS8050, NPN), Q5 emitter on RTS#,
#            Q5 collector -> D5 -> NRST
#            RTS asserted AND DTR released  => NRST low (reset)
#   NRST has R9 10k to 3V3 and C12 100 nF: it rises slowly (~1 ms).
#   BOOT0 has a 10k pull-down: it falls in microseconds.
#
#   entry  rts&-dtr , dtr , rts  reset with BOOT0 high, then release the reset
#                                (DTR on turns Q5 off) while RTS keeps BOOT0
#                                high -> ROM bootloader. The last ",rts" changes
#                                nothing but waits 100 ms: stm32flash sends 0x7F
#                                right after the sequence, and without the wait
#                                the bootloader isn't listening yet (tested on
#                                the board: no answer without it, 5/5 with it).
#   exit   rts&-dtr , -rts       reset again, then release RTS: BOOT0 drops at
#                                once, NRST rises ~1 ms later -> the firmware
#
# In stm32flash, "rts"/"dtr" ASSERT a line (the CH9102F pin goes LOW),
# "-rts"/"-dtr" release it, "," waits 100 ms, "&" doesn't wait.
#
# The board also has BOOT and RST buttons. --manual skips the DTR/RTS
# sequence: hold BOOT, press and release RST, release BOOT, then continue.
#
# This script wraps stm32flash: chip info, read the flash back (backup),
# compare it with a .hex, write + verify a new .hex, reset into the firmware.
#
# USAGE
#   bash flash_rrclite.sh info                  # reach the bootloader, print chip info
#   bash flash_rrclite.sh backup [file.bin]     # read the whole 512 KB flash to a file
#   bash flash_rrclite.sh compare FIRMWARE.hex  # is FIRMWARE.hex what the board runs?
#   bash flash_rrclite.sh flash FIRMWARE.hex    # erase, write, verify, run
#   bash flash_rrclite.sh run                   # just reset the board into its firmware
#
# OPTIONS (before the command)
#   --port /dev/ttyACM0   serial port (default /dev/rrclite, else /dev/ttyACM0)
#   --baud 115200         bootloader baud rate (default 115200)
#   --seq 'ENTRY:EXIT'    another stm32flash -i sequence (for a different board)
#   --manual              no DTR/RTS sequence: you put the board in the
#                         bootloader with the BOOT + RST buttons
#   --yes                 don't ask before writing
#
# Run it ON THE PI, as your normal user (in the dialout group). The USB cable
# alone powers the STM32. Stop the ros_robot_controller node first.
# Needs: sudo apt install stm32flash python3
# =============================================================================

# ----------------------------- SETTINGS --------------------------------------
BAUD=115200                      # the ROM bootloader auto-detects the speed;
                                 # 115200 is what Hiwonder's tools use
FLASH_START=0x08000000           # STM32F407VE: 512 KB of flash from here
FLASH_SIZE=524288
SEQ="rts&-dtr,dtr,rts:rts&-dtr,-rts" # entry:exit, from the schematic (see above)
# -----------------------------------------------------------------------------

set -u
say()  { echo -e "\n\033[1;36m==> $*\033[0m"; }
ok()   { echo -e "    \033[1;32mOK\033[0m  $*"; }
warn() { echo -e "    \033[1;33m!!\033[0m  $*"; }
die()  { echo -e "\n\033[1;31mERROR:\033[0m $*\n" >&2; exit 1; }

PORT=""
MANUAL=0
ASSUME_YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --port)   PORT="$2"; shift 2 ;;
    --baud)   BAUD="$2"; shift 2 ;;
    --seq)    SEQ="$2";  shift 2 ;;
    --manual) MANUAL=1;  shift ;;
    --yes)    ASSUME_YES=1; shift ;;
    -h|--help) sed -n '2,56p' "$0"; exit 0 ;;
    *) break ;;
  esac
done
CMD="${1:-info}"
ARG="${2:-}"

[ "$(id -u)" -ne 0 ] || warn "Running as root. Better: run as your user, in the dialout group."
command -v stm32flash >/dev/null || die "stm32flash is missing:  sudo apt install stm32flash"
command -v python3 >/dev/null    || die "python3 is missing"

if [ -z "$PORT" ]; then
  if [ -e /dev/rrclite ]; then PORT=/dev/rrclite; else PORT=/dev/ttyACM0; fi
fi
[ -e "$PORT" ] || die "$PORT does not exist. Is the board plugged into the UART1 Type-C port? (lsusb | grep 1a86:55d4)"
[ -r "$PORT" ] && [ -w "$PORT" ] || die "No permission on $PORT. sudo usermod -aG dialout \$USER, then log out and in again (Lab 02, Part 2.2)."
if command -v fuser >/dev/null && fuser "$PORT" >/dev/null 2>&1; then
  die "$PORT is in use by another program (the ros_robot_controller node, a serial terminal?):\n$(fuser -v "$PORT" 2>&1 | grep -v "Cannot stat")"
fi

# Common stm32flash options. -R at the end of every command runs the exit
# sequence (with --manual: a reset from the bootloader, BOOT already released),
# so the firmware starts again.
if [ "$MANUAL" -eq 1 ]; then
  STM=(stm32flash -b "$BAUD")
else
  STM=(stm32flash -b "$BAUD" -i "$SEQ")
fi

buttons() {
  say "$1hold BOOT, press and release RST, release BOOT - then press Enter"
  read -r _
}

# Check that the bootloader answers before doing anything else.
connect() {
  if [ "$MANUAL" -eq 1 ]; then
    buttons "Manual mode: "
  else
    say "Entering the bootloader with DTR/RTS:  -i '$SEQ'"
  fi
  # capture first: "stm32flash | grep -q" could kill stm32flash before its reset
  OUT=$("${STM[@]}" -R "$PORT" 2>&1)
  if echo "$OUT" | grep -q "Device ID"; then
    ok "bootloader answered ($(echo "$OUT" | sed -n 's/^Device ID *: *//p'))"
    # manual mode: -R above left the bootloader; go back in for the real command
    if [ "$MANUAL" -eq 1 ] && [ "$CMD" != "info" ] && [ "$CMD" != "run" ]; then
      buttons "Once more: "
    fi
    return
  fi
  echo
  echo "$OUT" | sed 's/^/    | /'
  die "The bootloader did not answer. Check (Lab 02, Troubleshooting):
  - the cable is in the UART1 Type-C port (the only port that can flash)
  - nothing else has the port open
  - try again: Hiwonder's guide says a retry often fixes COM_CMD_TIMEOUT
  - try the buttons instead:  bash $0 --manual $CMD ${ARG}"
}

# Intel HEX -> raw binary. Prints "<start address> <length>" and writes $2.
hex2bin() {
  python3 - "$1" "$2" <<'PY'
import sys
mem, base = {}, 0
for n, line in enumerate(open(sys.argv[1]), 1):
    line = line.strip()
    if not line:
        continue
    if line[0] != ':':
        sys.exit("line %d is not Intel HEX" % n)
    b = bytes.fromhex(line[1:])
    if sum(b) & 0xFF:
        sys.exit("checksum error on line %d" % n)
    ln, addr, typ, data = b[0], (b[1] << 8) | b[2], b[3], b[4:4 + b[0]]
    if typ == 0:
        for i, x in enumerate(data):
            mem[base + addr + i] = x
    elif typ == 2:
        base = ((data[0] << 8) | data[1]) << 4
    elif typ == 4:
        base = ((data[0] << 8) | data[1]) << 16
    elif typ == 1:
        break
if not mem:
    sys.exit("no data in the HEX file")
lo, hi = min(mem), max(mem) + 1
out = bytearray(b"\xFF" * (hi - lo))
for a, x in mem.items():
    out[a - lo] = x
open(sys.argv[2], "wb").write(out)
print("0x%08X %d" % (lo, hi - lo))
PY
}

check_hex() {
  [ -n "$ARG" ] || die "Give the firmware file:  bash $0 $CMD FIRMWARE.hex"
  [ -f "$ARG" ] || die "$ARG not found"
  TMPBIN=$(mktemp --suffix=.bin)
  read -r HEX_START HEX_LEN < <(hex2bin "$ARG" "$TMPBIN") || die "$ARG is not a valid Intel HEX file"
  [ -n "${HEX_LEN:-}" ] || die "$ARG is not a valid Intel HEX file"
  [ $((HEX_START)) -ge $((FLASH_START)) ] && [ $((HEX_START + HEX_LEN)) -le $((FLASH_START + FLASH_SIZE)) ] \
    || die "$ARG covers $HEX_START + $HEX_LEN bytes - outside the STM32F407VE's flash"
  [ $((HEX_START)) -eq $((FLASH_START)) ] \
    || warn "$ARG starts at $HEX_START, not $FLASH_START: it expects a bootloader of its own below it"
  ok "$(basename "$ARG"): $HEX_LEN bytes at $HEX_START, md5 $(md5sum < "$ARG" | cut -c1-32)"
}

case "$CMD" in
  info)
    connect
    say "Chip information"
    echo "$OUT" | sed -n '/Interface/,/Option 2/p'
    echo
    echo "The board was reset back into its firmware. Next: bash $0 backup"
    ;;

  backup)
    connect
    FILE="${ARG:-rrclite_backup_$(date +%Y%m%d_%H%M%S).bin}"
    say "Reading $FLASH_SIZE bytes from $FLASH_START into $FILE (about 1 minute)"
    "${STM[@]}" -r "$FILE" -S "$FLASH_START:$FLASH_SIZE" -R "$PORT" \
      || die "Read failed. 'Failed to read memory' = the chip is read-protected (RDP): no backup is possible (Lab 02, Part 4.2)."
    ok "saved $FILE  (md5 $(md5sum < "$FILE" | cut -c1-32))"
    ;;

  compare)
    check_hex
    connect
    say "Reading the same $HEX_LEN bytes back from the board"
    TMPREAD=$(mktemp --suffix=.bin)
    "${STM[@]}" -r "$TMPREAD" -S "$HEX_START:$HEX_LEN" -R "$PORT" >/dev/null 2>&1 \
      || die "Read failed (read-protected chip?)"
    if cmp -s "$TMPBIN" "$TMPREAD"; then
      ok "IDENTICAL: the board runs $(basename "$ARG")"
    else
      warn "DIFFERENT: the board does not run $(basename "$ARG") ($(cmp -l "$TMPBIN" "$TMPREAD" | wc -l) bytes differ)"
    fi
    rm -f "$TMPBIN" "$TMPREAD"
    ;;

  flash)
    check_hex
    connect
    if [ "$ASSUME_YES" -ne 1 ]; then
      echo
      echo "    This ERASES the firmware on the board and writes $(basename "$ARG")."
      echo "    Made a backup first?  (bash $0 backup)"
      read -r -p "    Type 'yes' to flash: " ANSWER
      [ "$ANSWER" = "yes" ] || die "Cancelled - nothing was changed"
    fi
    say "Erasing, writing and verifying (about 30-60 s). Don't unplug the board."
    "${STM[@]}" -w "$ARG" -v -R "$PORT" \
      || die "Flashing failed. The old firmware may be partly erased: the board stays usable in the
  bootloader, so fix the cause (Lab 02, Troubleshooting) and run this command again."
    rm -f "$TMPBIN"
    ok "written and verified - the board was reset into the new firmware"
    echo
    echo "Check it talks:  python3 rrclite_probe.py --beep"
    ;;

  run)
    connect
    ok "board reset into its firmware"
    ;;

  *)
    die "Unknown command '$CMD'. Use: info | backup [file] | compare FILE.hex | flash FILE.hex | run"
    ;;
esac
