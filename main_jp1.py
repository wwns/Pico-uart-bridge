"""
Raspberry Pi Pico - Most USB <-> UART dla JP1 (URC-7120 i inne)
================================================================

ZASTOSOWANIE: programowanie pilotow JP1.x przez RMIR lub Remote Master
BAUDRATE: 9600 (staly — wymagany przez interfejs JP1)
BRAK MENU — czysty most, zaden bajt nie jest przechwytywany

Schemat polaczen:
  Pico GP0 (TX, pin 1) ──────────────────► [6] RXD pilota  (Bialy)
  Pico GP1 (RX, pin 2) ◄────────────────── [4] TXD pilota  (Zielony)
  Pico GND  (pin 3)    ──────────────────── [3] GND pilota  (Czarny)
  Pico GP3  (pin 5)    ──── HIGH ─────────► [2] RTS pilota  (Zolty)  [opcja]

  [1] VDD   pilota — NIE PODLACZAC (pilot ma wlasne baterie)
  [5] RESET pilota — NIE PODLACZAC

Polaczenie z RMIR:
  1. Flashuj ten plik jako main.py na Pico
  2. Podlacz pilot do Pico (4 przewody lub 3)
  3. Otworz RMIR → Interface: "JP1.X Serial" → Port: Pico COM (COM4)
  4. Baudrate w RMIR: 9600

Aby przeflashowac kolejny raz:
  Odlacz i podlacz Pico z wcisnietym BOOTSEL (wchodzi w UF2/DFU)
  lub: mpremote cp nowy.py :main.py  (dziala tylko zaraz po resecie)
"""

import machine
import sys
import utime
import uselect
import micropython

# Zablokuj Ctrl+C natychmiast — RMIR moze wyslac bajt 0x03 (ETX)
micropython.kbd_intr(-1)

# GP3 = HIGH (sygnalizuje gotowsc → pilot pin [2] RTS)
machine.Pin(3, machine.Pin.OUT).on()

# LED
led = machine.Pin(25, machine.Pin.OUT)
led.on()

# UART0: GP0=TX, GP1=RX, 9600 baud (standard JP1), bufor 256B
uart = machine.UART(0, baudrate=9600,
                    tx=machine.Pin(0), rx=machine.Pin(1),
                    rxbuf=256, timeout=0)

# 3x blysk = gotowe
for _ in range(3):
    led.toggle()
    utime.sleep_ms(100)
led.on()

# poll(0) = nieblokujace sprawdzenie czy USB ma dane
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

usb_out = sys.stdout.buffer

while True:
    # --- USB (RMIR/PC) → UART (pilot) ---
    if poll.poll(0):
        b = sys.stdin.buffer.read(1)
        if b:
            uart.write(b)
            led.off()

    # --- UART (pilot) → USB (RMIR/PC) ---
    n = uart.any()
    if n:
        data = uart.read(n)
        if data:
            usb_out.write(data)
            led.off()

    led.on()

