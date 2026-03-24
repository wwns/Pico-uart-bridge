# Pico USB ↔ UART Bridge

Przezroczysty konwerter USB-UART dla **Raspberry Pi Pico v1** (RP2040).  
Podłącz dowolne urządzenie UART (ESP8266, ESP32, Arduino, RPi, GPS, GSM...) do PC przez USB.

---

## Schemat połączeń

```
PC (USB) ──── Pico ──── Urządzenie docelowe
               GP0 (TX, pin 1)  ──►  RX
               GP1 (RX, pin 2)  ◄──  TX
               GND  (pin 3/38)  ───  GND
```

> **Tylko logika 3.3V.** Nie podłączaj sygnałów 5V bezpośrednio.

---

## Funkcje

- Przezroczysty most dwukierunkowy — brak narzutu protokołu
- Interaktywne menu zmiany baudrate (wpisz `+++` aby wejść)
- Obsługa 10 prędkości, w tym **74880** dla boot ROM ESP8266
- Wskaźnik LED: świeci = aktywny, miga = transfer danych
- Ctrl+C zablokowany po 10-sekundowym oknie startowym (zapobieganie przypadkowemu przerwaniu działania)
- 10-sekundowe okno po starcie dla `mpremote` do aktualizacji firmware

---

## Obsługiwane prędkości

| Nr | Baudrate | Urządzenie / opis |
|----|----------|-------------------|
| 1 | 1200 | Stare czujniki |
| 2 | 2400 | Stare urządzenia |
| 3 | 4800 | GPS, stare urządzenia |
| 4 | 9600 | Arduino domyślny, GPS, GSM |
| 5 | 19200 | Modemy, sterowniki PLC |
| 6 | 38400 | Modemy, Bluetooth HC-05/06 |
| 7 | 57600 | Bluetooth, szybkie moduły |
| 8 | **74880** | **ESP8266 boot ROM** (krzaki po włączeniu) |
| 9 | **115200** | **ESP8266/ESP32 praca** ← domyślny |
| 10 | 230400 | ESP32 szybki transfer |

---

## Użytkowanie

1. Wgraj `main.py` na Pico przez `mpremote`:
   ```
   mpremote cp main.py :main.py + reset
   ```
2. Otwórz terminal na porcie COM Pico (np. PuTTY, 115200 baud)
3. Podłącz urządzenie UART do GP0/GP1/GND
4. Wpisz `+++` aby otworzyć menu wyboru baudrate

### Menu

```
+++             → otwórz menu
[numer] Enter   → wybierz baudrate
go              → wróć do trybu bridge
```

---

## Wgrywanie / Aktualizacja

Po resecie Pico masz **10 sekund** na użycie `mpremote`:

```powershell
# Naciśnij RUN na Pico (lub odłącz/podłącz USB), potem szybko:
mpremote cp main.py :main.py
```

---

## Wymagania

- Raspberry Pi Pico v1 (RP2040)
- MicroPython v1.20+ — https://micropython.org/download/RPI_PICO/
- PC: `mpremote` do wgrywania, PuTTY / miniterm do terminala

```powershell
pip install mpremote
python -m serial.tools.miniterm COMx 115200
```
