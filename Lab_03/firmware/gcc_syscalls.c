/**
 * gcc_syscalls.c - Lab 03: replaces Hiwonder/Misc/syscall.c (Keil ARMCC only)
 * when the firmware is built with arm-none-eabi-gcc + newlib-nano.
 *
 * Like the Keil version, printf() goes to SEGGER RTT channel 0 (read it with a
 * J-Link), NOT to USART1: USART1 carries the 0xAA 0x55 packets to the Pi.
 * Everything else comes from newlib's nosys stubs (--specs=nosys.specs).
 */
#include "SEGGER_RTT.h"

int _write(int fd, char *ptr, int len)
{
    (void)fd;
    SEGGER_RTT_Write(0, ptr, (unsigned)len);
    return len;
}

/* No files on this board: the other system calls newlib may reference just fail.
 * (Defined here so the linker doesn't warn "_read is not implemented".) */
#include <errno.h>
#include <sys/stat.h>

int _close(int fd)                     { (void)fd; errno = EBADF; return -1; }
int _read(int fd, char *p, int n)      { (void)fd; (void)p; (void)n; errno = EBADF; return -1; }
int _lseek(int fd, int off, int dir)   { (void)fd; (void)off; (void)dir; errno = ESPIPE; return -1; }
int _isatty(int fd)                    { return fd <= 2; }
int _fstat(int fd, struct stat *st)    { (void)fd; st->st_mode = S_IFCHR; return 0; }
