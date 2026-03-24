"""
Raspberry Pi Pico - Transparent USB <-> UART Bridge
====================================================

Wiring:
  PC (USB) <---> Pico <---> Target device

  Pico GP0 (TX, pin 1)  ---->  Target RX
  Pico GP1 (RX, pin 2)  <----  Target TX
  Pico GND  (pin 3/38)  ----   Target GND

Operation:
  - All data from USB (PC) is forwarded to UART (target device)
  - All data from UART (target device) is forwarded to USB (PC)
  - LED solid = bridge active; blinking = data transfer
  - Type +++ to open the baud rate configuration menu
  - 10-second startup window for mpremote (firmware update)
  - Ctrl+C disabled after startup window (prevents accidental REPL break)
"""

import machine
import sys
import utime
import uselect
import micropython

# 10-second window on boot for mpremote to access REPL, then disable Ctrl+C
# so it doesn't interrupt the bridge when passing through to target device
utime.sleep_ms(10000)
micropython.kbd_intr(-1)

# Baud rate table: (menu number, baud rate, description)
BAUDRATES = [
    ( 1,   1200, "Old sensors / legacy devices"),
    ( 2,   2400, "Old devices"),
    ( 3,   4800, "GPS modules, old devices"),
    ( 4,   9600, "Arduino default, GPS, GSM modules"),
    ( 5,  19200, "Modems, PLC controllers"),
    ( 6,  38400, "Modems, Bluetooth HC-05/HC-06"),
    ( 7,  57600, "Bluetooth, fast modules"),
    ( 8,  74880, "ESP8266 boot ROM  <<< fixes garbled output on power-on"),
    ( 9, 115200, "ESP8266/ESP32 runtime, Arduino fast  [DEFAULT]"),
    (10, 230400, "ESP32 high-speed transfer"),
]
baudrate = 115200  # default baud rate


def make_uart(baud):
    """Initialize UART0 with given baud rate on GP0 (TX) and GP1 (RX)."""
    return machine.UART(0, baudrate=baud,
                        tx=machine.Pin(0), rx=machine.Pin(1), timeout=0)


def usb_print(msg):
    """Write a line to USB (PC terminal) with CRLF line ending."""
    sys.stdout.write(msg + "\r\n")


def show_menu():
    """Display the baud rate selection menu over USB."""
    usb_print("")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|       PICO USB<->UART BRIDGE - SETTINGS             |")
    usb_print("+" + "-" * 54 + "+")
    usb_print(f"|  Current baud rate: {baudrate:<6}                          |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Nr | Baud rate |  Description                      |")
    usb_print("|" + "-" * 54 + "|")
    for nr, baud, desc in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print(f"|  {nr:>2} | {baud:>9} | {desc:<35} |{marker}")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Type number (1-10) + Enter to change baud rate     |")
    usb_print("|  Type [go]  + Enter to return to bridge mode        |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  To open this menu: type +++                        |")
    usb_print("+" + "-" * 54 + "+")


# --- Initialization ---
uart = make_uart(baudrate)
led  = machine.Pin(25, machine.Pin.OUT)  # Pico v1: onboard LED = pin 25

# 6 quick blinks = Pico ready
for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

usb_print(f"=== BRIDGE READY | {baudrate} baud | GP0->TX GP1->RX | type +++ = menu ===")

# Register USB stdin for polling (non-blocking read)
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False   # True = menu mode, False = transparent bridge mode
seq_buf  = ""      # accumulator for +++ escape sequence detection
cmd_buf  = ""      # accumulator for menu command input

# --- Main loop ---
while True:
    try:
        # --- USB → UART or menu command handling ---
        if poll.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if cmd_mode:
                    # Menu mode: collect full line then process
                    if ch in ("\r", "\n"):
                        line = cmd_buf.strip()
                        cmd_buf = ""
                        if not line:
                            show_menu()
                        elif line.lower() == "go":
                            # Return to transparent bridge mode
                            cmd_mode = False
                            usb_print(f"  Bridge active | {baudrate} baud")
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            # Select baud rate by number
                            nr, new_baud, desc = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate)
                            usb_print(f"  OK - baud rate set to {baudrate} ({desc})")
                            usb_print(f"  Type [go] to return to bridge or a number to change again.")
                        else:
                            usb_print(f"  Unknown option: '{line}'  (type 1-{len(BAUDRATES)} or 'go')")
                    elif ch == "\x08":  # backspace
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)  # local echo
                else:
                    # Bridge mode: detect +++ escape sequence
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        # Enter menu mode
                        seq_buf = ""
                        cmd_mode = True
                        show_menu()
                    else:
                        # Flush buffered bytes to UART (keep last 3 for +++ detection)
                        if len(seq_buf) > 3:
                            pending = seq_buf[:-3]
                            uart.write(pending.encode() if isinstance(pending, str) else pending)
                            seq_buf = seq_buf[-3:]
                        # Forward current byte to UART
                        uart.write(ch if isinstance(ch, bytes) else ch.encode())

        # --- UART → USB: forward data from target device to PC ---
        if not cmd_mode:
            n = uart.any()
            if n:
                sys.stdout.buffer.write(uart.read(n))

    except KeyboardInterrupt:
        pass  # Ctrl+C ignored — bridge continues running
