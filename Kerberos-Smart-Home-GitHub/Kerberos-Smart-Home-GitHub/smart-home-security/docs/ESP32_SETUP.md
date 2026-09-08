# ESP32 Hardware Setup & Flashing Manual

This document provides exact hardware wiring instructions, pinout definitions, power distribution rules, and firmware compilation details.

---

## 1. Fixed GPIO Pinout Assignment

> [!IMPORTANT]
> The GPIO assignments listed below are fixed by physical system specification. Do not alter them in firmware.

| Hardware Component | Component Pin | ESP32 GPIO Pin | Mode / Circuit |
| :--- | :--- | :--- | :--- |
| **PIR Motion Sensor** | Output Signal | **GPIO 27** | Digital Input |
| **HC-SR04 Ultrasonic** | Trigger (TRIG) | **GPIO 5** | Digital Output |
| **HC-SR04 Ultrasonic** | Echo (ECHO) | **GPIO 18** | Digital Input *(Requires Voltage Divider)* |
| **Micro Servo Motor** | Signal (PWM) | **GPIO 13** | PWM Output |
| **Piezo Alarm Buzzer** | Positive (+) | **GPIO 14** | Tone / PWM Output |
| **Door Reed Switch** | Signal | **GPIO 25** | `INPUT_PULLUP` (Switch to GND) |

---

## 2. Voltage Divider Warning for HC-SR04 Echo Pin

> [!CAUTION]
> **CRITICAL VOLTAGE PROTECTION REQUIREMENT**:
> The HC-SR04 Ultrasonic Sensor runs on 5V VCC and outputs a **5V logic signal** on its ECHO pin.
> Connecting the 5V ECHO output directly to ESP32 GPIO 18 **can permanently damage the ESP32 input pin**.
>
> You MUST install a resistor voltage divider between HC-SR04 ECHO and ESP32 GPIO 18:
>
> ```
> HC-SR04 ECHO Output (5V)
>          │
>        [1 kΩ]
>          │
>          ├──────────────► Connected to ESP32 GPIO 18 (~3.3V safe)
>          │
>        [2 kΩ]
>          │
>         GND (Common Ground)
> ```

---

## 3. Power Supply & Common Ground Rules

1. **Servo Power**: Servo motors draw peak current spikes during movement. **Do NOT power the Servo VCC directly from the ESP32 3.3V or 5V regulator pin**. Connect Servo VCC to an external 5V 2A power supply.
2. **Common Ground**: Ensure all power supply grounds (External 5V GND, ESP32 GND, Sensor GND, Servo GND) are tied together to a single common ground bus.

---

## 4. Flashing ESP32 Firmware via Arduino IDE

1. Download and install [Arduino IDE](https://www.arduino.cc/en/software).
2. Install the **ESP32 Board Package**:
   - Go to `File` -> `Preferences`.
   - Add URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Open `Tools` -> `Board Manager` -> Search `esp32` -> Click **Install**.
3. Install Required Libraries via Library Manager (`Tools` -> `Manage Libraries`):
   - `Blynk` by Volodymyr Shymanskyy
   - `ESP32Servo` by Kevin Harrington
4. Open `esp32/firmware.ino` in Arduino IDE.
5. Update `WIFI_SSID`, `WIFI_PASS`, and `BLYNK_AUTH_TOKEN` in `esp32/config.h`.
6. Select Board: `DOIT ESP32 DEVKIT V1` and select your COM Port.
7. Click **Upload**. Open Serial Monitor at **115200 baud**.
