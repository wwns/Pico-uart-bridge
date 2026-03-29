"""
Raspberry Pi Pico - Przezroczysty most USB <-> UART
=====================================================

Schemat polaczen:
  Windows (PuTTY/COM4, 115200) <--USB--> Pico <--UART--> Urzadzenie

  Pico GP0 (TX, pin 1)  ---->  (RX)
  Pico GP1 (RX, pin 2)  <----  (TX)
  Pico GND  (pin 3/38)  ----   GND

JP1 pilot (opcja 6 = 38400):
  Pico GP0 (TX, pin 1)  -> JP1 [4] RX
  Pico GP1 (RX, pin 2)  <- JP1 [6] TX
  Pico GND  (pin 3)     -> JP1 [3] GND
  Pico GP2  (pin 4)     -> JP1 [5] RESET  (puls HIGH przy starcie)
  Baterie w pilocie     -> zasilaja pilot

Pico dziala jako przezroczysty konwerter USB<->UART:
  - LED swieci = uart aktywny; miga = transfer danych
  - Wpisz +++ aby wejsc do menu
"""

import machine
import sys
import utime
import uselect
import micropython

# 10s okno dla mpremote, potem blokuj Ctrl+C
utime.sleep_ms(10000)
micropython.kbd_intr(-1)

# (numer, baudrate, opis urzadzenia)
BAUDRATES = [
    ( 1,   1200, "Stare urzadzenia, czujniki"),
    ( 2,   2400, "Stare urzadzenia"),
    ( 3,   4800, "GPS, stare urzadzenia"),
    ( 4,   9600, "Arduino domyslny, GPS, GSM"),
    ( 5,  19200, "Modemy, sterowniki PLC"),
    ( 6,  38400, "JP1 pilot / Bluetooth HC-05/06"),
    ( 7,  57600, "Bluetooth, szybkie moduly"),
    ( 8,  74880, "ESP8266 boot ROM"),
    ( 9, 115200, "ESP8266/ESP32 Arduino"),
    (10, 230400, "ESP32 szybki transfer"),
]
baudrate = 115200

# RST pin dla JP1 (GP2, pin 4)
rst = machine.Pin(2, machine.Pin.OUT, value=0)

def jp1_reset_pulse():
    rst.value(0)
    utime.sleep_ms(100)
    rst.value(1)
    utime.sleep_ms(1000)

def make_uart(baud):
    return machine.UART(0, baudrate=baud,
                        tx=machine.Pin(0), rx=machine.Pin(1), timeout=0)

def usb_print(msg):
    sys.stdout.write(msg + "\r\n")

def show_menu():
    usb_print("")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|       PICO USB<->UART BRIDGE - USTAWIENIA           |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Aktualny baudrate: {:<6}                          |".format(baudrate))
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Nr | Baudrate |  Opis                               |")
    usb_print("|" + "-" * 54 + "|")
    for nr, baud, opis in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print("|  {:>2} | {:>8} | {:<35} |{}".format(nr, baud, opis, marker))
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Wpisz numer (1-10) i Enter aby zmienic baudrate     |")
    usb_print("|  Wpisz [go]  i Enter aby wrocic do trybu bridge      |")
    usb_print("|  Wpisz [jp1] aby pulsowac RST (GP2) dla pilota JP1   |")
    usb_print("+" + "-" * 54 + "+")
    usb_print("|  Aby wejsc do menu: wpisz +++                        |")
    usb_print("+" + "-" * 54 + "+")

uart = make_uart(baudrate)
led  = machine.Pin(25, machine.Pin.OUT)

for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

usb_print("=== UART GOTOWY | {} baud | GP0->TX GP1->RX | wpisz +++ = menu ===".format(baudrate))

poll     = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False
seq_buf  = ""
cmd_buf  = ""

while True:
    try:
        if poll.poll(0):
            ch = sys.stdin.read(1)
            if ch:
                if cmd_mode:
                    if ch in ("\r", "\n"):
                        line = cmd_buf.strip()
                        cmd_buf = ""
                        if not line:
                            show_menu()
                        elif line.lower() == "go":
                            cmd_mode = False
                            usb_print("  Bridge aktywny | {} baud".format(baudrate))
                        elif line.lower() == "jp1":
                            usb_print("  RST pulse GP2 -> JP1 [5]...")
                            jp1_reset_pulse()
                            usb_print("  Gotowe. Wpisz [go] aby wrocic do bridge.")
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            nr, new_baud, opis = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate)
                            usb_print("  OK - baudrate zmieniony na {} ({})".format(baudrate, opis))
                            usb_print("  Wpisz [go] aby wrocic do bridge lub numer aby zmienic.")
                        else:
                            usb_print("  Nieznana opcja: '{}'  (wpisz numer 1-{} lub 'go')".format(line, len(BAUDRATES)))
                    elif ch == "\x08":
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)
                else:
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        seq_buf = ""
                        cmd_mode = True
                        show_menu()
                    else:
                        if len(seq_buf) > 3:
                            uart.write(seq_buf[:-3].encode() if isinstance(seq_buf[:-3], str) else seq_buf[:-3])
                            seq_buf = seq_buf[-3:]
                        uart.write(ch if isinstance(ch, bytes) else ch.encode())

        if not cmd_mode:
            n = uart.any()
            if n:
                data = uart.read(n)
                sys.stdout.buffer.write(data)
                led.toggle()

    except KeyboardInterrupt:
        pass
