# Pico USB ↔ UART Bridge

Transparent USB-to-UART bridge for **Raspberry Pi Pico v1** (RP2040).  
Connect any UART device (ESP8266, ESP32, Arduino, RPi, GPS, GSM...) to your PC via USB.

---

## Wiring

```
PC (USB) ──── Pico ──── Target device
               GP0 (TX, pin 1)  ──►  RX
               GP1 (RX, pin 2)  ◄──  TX
               GND  (pin 3/38)  ───  GND
```

> **3.3V logic only.** Do not connect 5V signals directly.

---

## Features

- Transparent bidirectional bridge — no protocol overhead
- Interactive baud rate menu (type `+++` to enter)
- Supports 10 baud rates including **74880** for ESP8266 boot ROM
- LED indicator: solid = active, blink = data transfer
- Ctrl+C disabled after 10-second startup window (prevents accidental REPL break)
- 10-second window on boot for `mpremote` firmware updates

---

## Supported Baud Rates

| # | Baud rate | Device / Notes |
|---|-----------|----------------|
| 1 | 1200 | Old sensors |
| 2 | 2400 | Old devices |
| 3 | 4800 | GPS, old devices |
| 4 | 9600 | Arduino default, GPS, GSM |
| 5 | 19200 | Modems, PLC |
| 6 | 38400 | Modems, Bluetooth HC-05/06 |
| 7 | 57600 | Bluetooth, fast modules |
| 8 | **74880** | **ESP8266 boot ROM** (fix garbled output) |
| 9 | **115200** | **ESP8266/ESP32 default** ← default |
| 10 | 230400 | ESP32 fast transfer |

---

## Usage

1. Flash `main.py` to Pico using `mpremote`:
   ```
   mpremote cp main.py :main.py + reset
   ```
2. Open terminal on the Pico's COM port (e.g. PuTTY, 115200 baud)
3. Connect the target UART device to GP0/GP1/GND
4. Type `+++` to open the baud rate menu

### Menu

```
+++             → open menu
[number] Enter  → select baud rate
go              → return to bridge mode
```

---

## Flashing / Updating

After reset, there is a **10-second window** to use `mpremote`:

```powershell
# Reset Pico (press RUN button or reconnect USB), then quickly:
mpremote cp main.py :main.py
```

---

## Requirements

- Raspberry Pi Pico v1 (RP2040)
- MicroPython v1.20+ — https://micropython.org/download/RPI_PICO/
- PC: `mpremote` for flashing, PuTTY / miniterm for terminal

```powershell
pip install mpremote
python -m serial.tools.miniterm COMx 115200
```
