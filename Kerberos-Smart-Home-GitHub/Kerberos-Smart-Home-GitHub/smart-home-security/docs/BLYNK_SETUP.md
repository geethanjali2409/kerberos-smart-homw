# Blynk Cloud Setup Guide — Smart Home Security System

This document outlines the step-by-step process for configuring your **Blynk Cloud Account**, **Template**, and **Virtual Pin Datastreams**.

---

## 1. Create Blynk Account & Template

1. Sign in to [Blynk.cloud Console](https://blynk.cloud/).
2. Navigate to **Templates** -> Click **+ New Template**.
3. Fill in the template details:
   - **Name**: `Smart Home Security Digital Twin`
   - **Hardware**: `ESP32`
   - **Connection Type**: `Wi-Fi`
4. Copy your generated `BLYNK_TEMPLATE_ID` and `BLYNK_TEMPLATE_NAME`.

---

## 2. Configure Virtual Pin Datastreams

In your Blynk Template, navigate to the **Datastreams** tab and create the following **16 Virtual Pin Datastreams**:

| Virtual Pin | Name | Data Type | Min | Max | Default | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `V0` | PIR Motion | Integer | 0 | 1 | 0 | Sensor Telemetry |
| `V1` | Ultrasonic Distance | Double / Integer | 0 | 400 | 250 | Proximity (cm) |
| `V2` | Door State | Integer | 0 | 1 | 0 | 0=Closed, 1=Open |
| `V3` | Window State | Integer | 0 | 1 | 0 | 0=Closed, 1=Triggered |
| `V4` | Servo Lock State | Integer | 0 | 1 | 1 | 0=Unlocked, 1=Locked |
| `V5` | Buzzer State | Integer | 0 | 2 | 0 | 0=Off, 1=Beep, 2=Alarm |
| `V6` | Physical Door Switch | Integer | 0 | 1 | 0 | 0=Closed, 1=Open |
| `V7` | System Armed | Integer | 0 | 1 | 1 | 0=Disarmed, 1=Armed |
| `V8` | ESP32 Online | Integer | 0 | 1 | 0 | Heartbeat Status |
| `V9` | WiFi RSSI | Integer | -100 | 0 | -65 | Signal Strength (dBm) |
| `V10` | Door Lock Command | Integer | 0 | 1 | 1 | Dashboard Command |
| `V11` | System Arm Command | Integer | 0 | 1 | 1 | Dashboard Command |
| `V12` | Buzzer Command | Integer | 0 | 2 | 0 | Dashboard Command |
| `V13` | Reset Alarm Command| Integer | 0 | 1 | 0 | Dashboard Command |
| `V14` | Camera Status | String | - | - | "ONLINE"| Local Camera Status |
| `V15` | Security Event Log | String | - | - | "" | Event Metadata Stream |

---

## 3. Obtain Device Credentials

1. Navigate to **Search (Devices)** -> Click **+ New Device** -> Select **From Template**.
2. Select your `Smart Home Security Digital Twin` template.
3. Copy your `BLYNK_AUTH_TOKEN`.
4. Paste the token into `esp32/config.h`:
   ```cpp
   #define BLYNK_AUTH_TOKEN "YourBlynkAuthTokenHere"
   ```
5. Enter the token into the Web Dashboard settings or `.env` file.
