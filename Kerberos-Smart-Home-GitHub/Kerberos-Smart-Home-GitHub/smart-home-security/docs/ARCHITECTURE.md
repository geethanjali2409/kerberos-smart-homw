# System Architecture — Distributed Trust-Based Smart Home Security System

This document describes the end-to-end hardware, cloud, state model, and WebGL digital twin architecture.

---

## 1. System Architecture Topology

```
                  +-----------------------------------+
                  |            BLYNK CLOUD            |
                  |     (REST API & Datastreams)      |
                  +-----------------------------------+
                            ▲               │
     Sensor Telemetry (V0-V9)|               │ Commands (V10-V13)
                            │               ▼
 +----------------------------------+   +----------------------------------+
 |        ESP32 MICROCONTROLLER     |   |      WEB APPLICATION & TWIN      |
 |  - GPIO 27: PIR Motion           |   |  - Central Security Store        |
 |  - GPIO 5/18: Ultrasonic Meter   |   |  - Three.js WebGL 3D Digital Twin|
 |  - GPIO 25: Physical Reed Switch |   |  - Security Command Dashboard    |
 |  - GPIO 13: Servo Door Lock      |   |  - Laptop Webcam CCTV Stream     |
 |  - GPIO 14: Piezo Siren          |   |  - Developer Hardware Simulator  |
 +----------------------------------+   +----------------------------------+
                 │                                       │
                 ▼                                       ▼
 +----------------------------------+   +----------------------------------+
 |       LOCAL HARDWARE FAIL-SAFE   |   |        SIMULATION ENGINE         |
 | (Runs security logic offline     |   | (Injects sensor triggers & syncs |
 |  if Wi-Fi/Blynk connection drops)|   |  cloud commands to real hardware)|
 +----------------------------------+   +----------------------------------+
```

---

## 2. Telemetry Flow (Physical Hardware ──► Digital Twin)

1. Physical sensors (PIR motion sensor, HC-SR04 ultrasonic distance meter, Door magnetic switch) generate signal pulses.
2. ESP32 non-blocking loop samples GPIO states every 100ms.
3. ESP32 publishes sensor telemetry to Blynk Virtual Pins (`V0`-`V9`) via BlynkTimer every 1000ms.
4. The Web Application polls Blynk REST API endpoints.
5. Telemetry updates the **Central Normalized State Store** (`securityStore.js`).
6. Three.js WebGL 3D Digital Twin automatically animates door opening angles, PIR detection cone highlights, ultrasonic sonar beam lengths, and servo deadbolt positions in real time.

---

## 3. Reverse Command Flow (Dashboard ──► Physical Hardware)

1. Operator clicks **LOCK DOOR** or **ARM SYSTEM** in the Dashboard UI.
2. `blynkService.js` dispatches HTTP GET requests to update Virtual Pins (`V10` or `V11`).
3. Blynk Cloud forwards the callback to the ESP32 firmware via `BLYNK_WRITE(V10)`.
4. ESP32 executes physical actuator action (PWM signal moves Servo motor angle to 90°).
5. ESP32 confirms telemetry update back to Blynk (`V4 = 1`).
6. 3D Digital Twin updates servo horn position to LOCKED.

---

## 4. Local Fail-Safe Security Logic

If Wi-Fi connection drops or Blynk Cloud is offline:
- **Physical Security is NEVER disabled**.
- ESP32 continues running local sensor acquisition and state machine locally.
- If PIR motion + Ultrasonic proximity < 20cm or Door switch opens while ARMED:
  - Local Piezo Siren (GPIO 14) sounds full alarm tone.
  - Servo Lock (GPIO 13) forces door deadbolt locked.
- Upon reconnection to Wi-Fi/Blynk, ESP32 synchronizes current hardware state to cloud.
