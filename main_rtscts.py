"""
Raspberry Pi Pico - Przezroczysty most USB <-> UART z RTS/CTS
==============================================================

Schemat polaczen (bez flow control):
  PC (USB) <---> Pico <---> Urzadzenie

  Pico GP0 TX  (pin 1)  ---->  RX urzadzenia
  Pico GP1 RX  (pin 2)  <----  TX urzadzenia
  Pico GND     (pin 3)  ----   GND urzadzenia

Schemat polaczen (z hardware flow control RTS/CTS):
  Pico GP0 TX  (pin 1)  ---->  RX urzadzenia
  Pico GP1 RX  (pin 2)  <----  TX urzadzenia
  Pico GP2 CTS (pin 4)  <----  RTS urzadzenia   (Pico wejscie)
  Pico GP3 RTS (pin 5)  ---->  CTS urzadzenia   (Pico wyjscie)
  Pico GND     (pin 3)  ----   GND urzadzenia

Dzialanie:
  - Przeźroczysty bridge USB <-> UART
  - Wpisz +++ aby otworzyc menu konfiguracji
  - Menu pozwala zmienic baudrate i wl/wyl RTS/CTS
  - 10s okno startowe dla mpremote, potem blokada Ctrl+C
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
    ( 6,  38400, "Modemy, Bluetooth HC-05/06"),
    ( 7,  57600, "Bluetooth, szybkie moduly"),
    ( 8,  74880, "ESP8266 boot ROM (krzaki przy starcie)"),
    ( 9, 115200, "ESP8266/ESP32 Arduino  [DOMYSLNY]"),
    (10, 230400, "ESP32 szybki transfer"),
]

baudrate   = 115200
flow_ctrl  = False   # True = hardware RTS/CTS wlaczone


def make_uart(baud, flow):
    """Tworzy UART0 z podanym baudrate i opcjonalnym RTS/CTS."""
    if flow:
        return machine.UART(0, baudrate=baud,
                            tx=machine.Pin(0),
                            rx=machine.Pin(1),
                            cts=machine.Pin(2),   # GP2 pin 4  <-- RTS urzadzenia
                            rts=machine.Pin(3),   # GP3 pin 5  --> CTS urzadzenia
                            timeout=0)
    else:
        return machine.UART(0, baudrate=baud,
                            tx=machine.Pin(0),
                            rx=machine.Pin(1),
                            timeout=0)


def usb_print(msg):
    sys.stdout.write(msg + "\r\n")


def show_menu():
    flow_str = "WLACZONY  (GP2=CTS GP3=RTS)" if flow_ctrl else "WYLACZONY"
    usb_print("")
    usb_print("+" + "-" * 56 + "+")
    usb_print("|       PICO USB<->UART BRIDGE - USTAWIENIA             |")
    usb_print("+" + "-" * 56 + "+")
    usb_print(f"|  Baudrate   : {baudrate:<8}                               |")
    usb_print(f"|  RTS/CTS    : {flow_str:<40} |")
    usb_print("+" + "-" * 56 + "+")
    usb_print("|  Nr | Baudrate |  Opis                                |")
    usb_print("|" + "-" * 56 + "|")
    for nr, baud, opis in BAUDRATES:
        marker = " <--" if baud == baudrate else "    "
        usb_print(f"|  {nr:>2} | {baud:>8} | {opis:<38} |{marker}")
    usb_print("+" + "-" * 56 + "+")
    usb_print("|  Wpisz numer (1-10)  - zmiana baudrate                |")
    usb_print("|  Wpisz [rts]         - wlacz/wylacz RTS/CTS           |")
    usb_print("|  Wpisz [go]          - wrocic do trybu bridge         |")
    usb_print("+" + "-" * 56 + "+")
    usb_print("|  Aby wejsc do menu: wpisz +++                         |")
    usb_print("+" + "-" * 56 + "+")


# --- Inicjalizacja ---
uart = make_uart(baudrate, flow_ctrl)
led  = machine.Pin(25, machine.Pin.OUT)   # Pico v1: LED = pin 25

# 6x blysk = Pico gotowe
for _ in range(6):
    led.toggle()
    utime.sleep_ms(100)
led.on()

flow_info = "RTS/CTS: WYL" if not flow_ctrl else "RTS/CTS: WL (GP2/GP3)"
usb_print(f"=== BRIDGE GOTOWY | {baudrate} baud | {flow_info} | wpisz +++ = menu ===")

poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

cmd_mode = False
seq_buf  = ""    # bufor wykrywania +++
cmd_buf  = ""    # bufor wpisywanej komendy

# --- Glowna petla ---
while True:
    try:
        # --- USB → UART lub obsluga menu ---
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
                            flow_info = "RTS/CTS: WL" if flow_ctrl else "RTS/CTS: WYL"
                            usb_print(f"  Bridge aktywny | {baudrate} baud | {flow_info}")
                        elif line.lower() == "rts":
                            # Przelacz RTS/CTS wl/wyl
                            flow_ctrl = not flow_ctrl
                            uart = make_uart(baudrate, flow_ctrl)
                            stan = "WLACZONY  (GP2=CTS, GP3=RTS)" if flow_ctrl else "WYLACZONY"
                            usb_print(f"  RTS/CTS {stan}")
                            show_menu()
                        elif line.isdigit() and 1 <= int(line) <= len(BAUDRATES):
                            nr, new_baud, opis = BAUDRATES[int(line) - 1]
                            baudrate = new_baud
                            uart = make_uart(baudrate, flow_ctrl)
                            usb_print(f"  OK - baudrate zmieniony na {baudrate} ({opis})")
                            usb_print(f"  Wpisz [go] aby wrocic lub numer aby zmienic ponownie.")
                        else:
                            usb_print(f"  Nieznana opcja: '{line}'")
                            usb_print(f"  Wpisz: 1-{len(BAUDRATES)} | rts | go")
                    elif ch == "\x08":   # backspace
                        cmd_buf = cmd_buf[:-1]
                    else:
                        cmd_buf += ch
                        sys.stdout.write(ch)   # lokalny echo
                else:
                    # Tryb bridge: wykryj +++
                    seq_buf += ch
                    if seq_buf.endswith("+++"):
                        seq_buf = ""
                        cmd_mode = True
                        show_menu()
                    else:
                        if len(seq_buf) > 3:
                            pending = seq_buf[:-3]
                            uart.write(pending.encode() if isinstance(pending, str) else pending)
                            seq_buf = seq_buf[-3:]
                        uart.write(ch if isinstance(ch, bytes) else ch.encode())

        # --- UART → USB: dane z urzadzenia do PC ---
        if not cmd_mode:
            n = uart.any()
            if n:
                sys.stdout.buffer.write(uart.read(n))

    except KeyboardInterrupt:
        pass   # Ctrl+C ignorowany, bridge dziala dalej
