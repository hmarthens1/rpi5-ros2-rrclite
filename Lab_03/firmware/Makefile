# Lab 03 - build the Hiwonder RRC Lite "ros" firmware on Linux with arm-none-eabi-gcc,
# plus encoder_report.c (encoder read-back over the serial protocol, M4 encoder fix).
#
#   sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi make
#   make SRC=~/rrclite/RosRobotControllerLite_ros_250811      # -> build/rrclite_lab03.hex
#
#   make SRC=... SPEED_LOOP=lab03                            # -> build/rrclite_lab03_sc.hex
#     uses speed_control.c (this lab's own pins/timers/PID setup) instead of Hiwonder's loop
#
# SRC is Hiwonder's source folder from the Appendix (Source Code/...). It is only read:
# nothing in it is changed, and all build output goes to ./build.

SRC     ?= $(HOME)/rrclite/RosRobotControllerLite_ros_250811
BUILD   ?= build
TARGET  ?= rrclite_lab03
PREFIX  ?= arm-none-eabi-

CC      = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
SIZE    = $(PREFIX)size

include srcs_list.mk

C_SOURCES  = $(addprefix $(SRC)/,$(HIWONDER_C)) \
             $(SRC)/Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F/port.c \
             gcc_syscalls.c encoder_report.c
ASM_SOURCES = $(SRC)/Core/Startup/startup_stm32f407vetx.s

INCLUDES = Core/Inc Drivers/STM32F4xx_HAL_Driver/Inc Drivers/STM32F4xx_HAL_Driver/Inc/Legacy \
  Middlewares/Third_Party/FreeRTOS/Source/include Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2 \
  Middlewares/Third_Party/FreeRTOS/Source/portable/GCC/ARM_CM4F \
  Drivers/CMSIS/Device/ST/STM32F4xx/Include Drivers/CMSIS/Include \
  Third_Party/Fusion/Fusion Third_Party/U8g2 Third_Party/RTT Third_Party/Lw Third_Party \
  Hiwonder/LVGL_UI/guider_customer_fonts Hiwonder/LVGL_UI/guider_fonts Hiwonder/LVGL_UI/images Hiwonder/LVGL_UI \
  Hiwonder/Peripherals Hiwonder/Portings Hiwonder/Chassis Hiwonder/System Hiwonder/Misc

WRAPS   = -Wl,--wrap=packet_handle_init -Wl,--wrap=motors_init
DEFS    =
ifeq ($(SPEED_LOOP),lab03)
  C_SOURCES += speed_control.c
  DEFS      += -DLAB03_SPEED_LOOP
  # Hiwonder's TIM7_IRQHandler (stm32f4xx_it.c) is made weak in its object file, so the
  # strong one in speed_control.c replaces it. (--wrap can't: the vector table in the
  # startup file defines the name itself.)
  WEAKEN    = $(BUILD)/src/Core/Src/stm32f4xx_it.o
  TARGET    := $(TARGET)_sc
  BUILD     := $(BUILD)/sc
endif

MCU     = -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CFLAGS  = $(MCU) -DUSE_HAL_DRIVER -DSTM32F407xx $(DEFS) $(addprefix -I$(SRC)/,$(INCLUDES)) \
          -O2 -g -std=gnu11 -fno-strict-aliasing -ffunction-sections -fdata-sections -fno-common \
          -Wall -Wno-unused-variable -Wno-unused-but-set-variable -Wno-unused-function \
          -Wno-pointer-sign -Wno-missing-braces -MMD -MP
LDFLAGS = $(MCU) -T STM32F407VETx_FLASH.ld --specs=nano.specs --specs=nosys.specs \
          -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map -Wl,--print-memory-usage \
          $(WRAPS) -lm

# Object names keep the source path, so two files with the same name can't clash.
OBJS = $(patsubst $(SRC)/%,$(BUILD)/src/%,$(patsubst %.c,%.o,$(filter $(SRC)/%,$(C_SOURCES)))) \
       $(addprefix $(BUILD)/lab03/,$(patsubst %.c,%.o,$(filter-out $(SRC)/%,$(C_SOURCES)))) \
       $(patsubst $(SRC)/%.s,$(BUILD)/src/%.o,$(ASM_SOURCES))

all: check $(BUILD)/$(TARGET).hex

check:
	@test -f $(SRC)/MDK-ARM/RosRobotControllerM4.uvprojx || \
	  { echo "SRC=$(SRC) is not Hiwonder's RosRobotControllerLite source folder"; exit 1; }
	@command -v $(CC) >/dev/null || { echo "$(CC) missing: sudo apt install gcc-arm-none-eabi libnewlib-arm-none-eabi"; exit 1; }

$(BUILD)/src/%.o: $(SRC)/%.c
	@mkdir -p $(dir $@)
	@echo "  CC  $*.c"
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/lab03/%.o: %.c
	@mkdir -p $(dir $@)
	@echo "  CC  $< (lab03)"
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/src/%.o: $(SRC)/%.s
	@mkdir -p $(dir $@)
	@echo "  AS  $*.s"
	@$(CC) $(MCU) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS) STM32F407VETx_FLASH.ld
	@echo "  LD  $@"
	$(if $(WEAKEN),@$(OBJCOPY) --weaken-symbol=TIM7_IRQHandler $(WEAKEN))
	@$(CC) $(OBJS) $(LDFLAGS) -o $@
	@$(SIZE) $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	@$(OBJCOPY) -O ihex $< $@
	@echo "  HEX $@"

clean:
	rm -rf $(BUILD)

.PHONY: all check clean
-include $(OBJS:.o=.d)
