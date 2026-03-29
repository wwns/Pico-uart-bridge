"""
Raspberry Pi Pico - prosty UART bridge dla JP1
=============================================

Polaczenie:
  Pico GP0 (TX, pin 1) -> JP1 [4]
  Pico GP1 (RX, pin 2) -> JP1 [6]
  Pico GND  (pin 3)    -> JP1 [3] GND
  JP1 [5] RESET        -> NIE PODLACZONY (lub do 3V3 zeby CPU dzialal)
  Baterie w pilocie    -> zasilaja pilot

  UWAGA: JP1 [5] RESET nie podlaczamy do GND!
  CPU pilota musi byc aktywny zeby EEPROM odpowiadal przez serial.

RMIR: Interface "JP1.X Serial", COM4, 38400 baud
"""

import sys
import utime
import uselect
from machine import UART, Pin

led = Pin(25, Pin.OUT)
led.on()

# Hardware UART0 na GP0(TX)/GP1(RX)
uart = UART(0, baudrate=38400, tx=Pin(0), rx=Pin(1),
            bits=8, parity=None, stop=1, timeout=10)

# Bufor
buf = bytearray(256)

led.off()
utime.sleep_ms(200)
led.on()

# Petla bridge: USB serial <-> hardware UART
while True:
    # USB -> UART (dane od RMIR do pilota)
    if sys.stdin in uselect.select([sys.stdin], [], [], 0)[0]:
        data = sys.stdin.buffer.read(64)
        if data:
            uart.write(data)
            led.toggle()

    # UART -> USB (odpowiedzi pilota do RMIR)
    n = uart.readinto(buf)
    if n:
        sys.stdout.buffer.write(buf[:n])
        led.toggle()
