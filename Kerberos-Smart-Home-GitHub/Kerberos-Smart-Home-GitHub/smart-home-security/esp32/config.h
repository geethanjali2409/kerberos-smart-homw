/*
 * ESP32 Smart Home Security System - Configuration Header
 * --------------------------------------------------------
 * GPIO pin definitions, Blynk Virtual Pins, security thresholds,
 * and hardware parameters.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================
// BLYNK CREDENTIALS (DO NOT COMMIT REAL TOKENS TO GIT)
// ============================================================
#define BLYNK_TEMPLATE_ID "TMPLxxxxxx"
#define BLYNK_TEMPLATE_NAME "Smart Home Security Digital Twin"
#define BLYNK_AUTH_TOKEN "YourBlynkAuthTokenHere"

// Wi-Fi Credentials
#define WIFI_SSID "Your_WiFi_SSID"
#define WIFI_PASS "Your_WiFi_Password"

// ============================================================
// GPIO PIN ASSIGNMENTS (FIXED HARDWARE SPECIFICATION)
// DO NOT ALTER THESE PIN DEFINITIONS
// ============================================================
#define PIR_PIN             27  // PIR Motion Sensor Output
#define ULTRASONIC_TRIG_PIN 5   // HC-SR04 Trigger Pin
#define ULTRASONIC_ECHO_PIN 18  // HC-SR04 Echo Pin (Use Voltage Divider: 1k/2k)
#define SERVO_PIN           13  // Servo Motor Signal PWM Pin
#define BUZZER_PIN          14  // Piezo Buzzer Signal Pin
#define DOOR_SWITCH_PIN     25  // Physical Door Reed Switch (INPUT_PULLUP)

// ============================================================
// BLYNK VIRTUAL PIN MAPPINGS
// ============================================================
// Sensor Telemetry
#define VPIN_PIR_MOTION         V0
#define VPIN_ULTRASONIC_DIST    V1
#define VPIN_DOOR_STATE         V2
#define VPIN_WINDOW_STATE       V3
#define VPIN_SERVO_STATE        V4
#define VPIN_BUZZER_STATE       V5
#define VPIN_DOOR_SWITCH        V6
#define VPIN_SYSTEM_ARMED       V7
#define VPIN_ESP32_ONLINE       V8
#define VPIN_WIFI_RSSI          V9

// Dashboard Commands
#define VPIN_CMD_DOOR_LOCK      V10
#define VPIN_CMD_ARM_SYSTEM     V11
#define VPIN_CMD_BUZZER         V12
#define VPIN_CMD_RESET_ALARM    V13

// Camera / Security Event Metadata
#define VPIN_CAMERA_STATUS      V14
#define VPIN_SECURITY_EVENT     V15

// ============================================================
// HARDWARE PARAMETERS & SECURITY THRESHOLDS
// ============================================================
#define SERVO_LOCK_ANGLE        90   // Locked position angle (degrees)
#define SERVO_UNLOCK_ANGLE      0    // Unlocked position angle (degrees)

#define ULTRASONIC_MAX_DIST_CM  400  // Maximum range (cm)
#define ULTRASONIC_WARN_DIST_CM 50   // Distance threshold for Warning (cm)
#define ULTRASONIC_ALARM_DIST_CM 20  // Distance threshold for Alarm (cm)

#define TELEMETRY_INTERVAL_MS   1000 // Telemetry upload period (1 sec)
#define HEARTBEAT_INTERVAL_MS   5000 // Heartbeat update period (5 sec)

#endif // CONFIG_H
