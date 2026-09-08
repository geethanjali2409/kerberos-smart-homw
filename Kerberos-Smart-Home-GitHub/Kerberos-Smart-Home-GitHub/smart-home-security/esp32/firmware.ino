/*
 * Distributed Trust-Based Smart Home Security System
 * ESP32 Main Firmware
 * ---------------------------------------------------
 * Features:
 * - Real-time non-blocking sensor acquisition (PIR, HC-SR04, Door Switch)
 * - Local fail-safe security state machine (continues operating if offline)
 * - Bidirectional Blynk Cloud synchronization (Virtual Pins V0-V15)
 * - Servo lock control and Piezo buzzer alarm patterns
 */

#define BLYNK_PRINT Serial

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include <ESP32Servo.h>
#include "config.h"

// System States
enum SystemMode { DISARMED = 0, ARMED = 1 };
enum AlarmState { STATE_NORMAL = 0, STATE_WARNING = 1, STATE_ALARM = 2, STATE_RESETTING = 3, STATE_FAULT = 4 };

// Global State Variables
SystemMode currentSystemMode = ARMED;
AlarmState currentAlarmState = STATE_NORMAL;

bool pirMotionDetected = false;
float ultrasonicDistanceCm = 999.0;
bool doorSwitchOpen = false; // LOW = CLOSED, HIGH = OPEN (INPUT_PULLUP)
bool doorLocked = true;
int buzzerMode = 0; // 0 = OFF, 1 = WARNING BEEP, 2 = ALARM TONE

// Hardware Objects
Servo doorLockServo;
BlynkTimer timer;

// Function Prototypes
void readPIR();
void readUltrasonic();
void readDoorSwitch();
void updateSecurityLogic();
void controlServo(bool lock);
void controlBuzzer(int mode);
void sendTelemetry();
void checkCloudConnection();
void triggerAlarm(const char* reason);
void clearAlarm();
void resetSystem();

// ============================================================
// BLYNK VIRTUAL PIN WRITE HANDLERS (COMMANDS FROM DASHBOARD)
// ============================================================

// V10: Door Lock Command (1 = LOCK, 0 = UNLOCK)
BLYNK_WRITE(VPIN_CMD_DOOR_LOCK) {
    int lockCmd = param.asInt();
    controlServo(lockCmd == 1);
    sendSecurityEvent(doorLocked ? "DOOR_LOCKED" : "DOOR_UNLOCKED", 
                      doorLocked ? "Door locked via Blynk Cloud command" : "Door unlocked via Blynk Cloud command");
}

// V11: System Arm Command (1 = ARM, 0 = DISARM)
BLYNK_WRITE(VPIN_CMD_ARM_SYSTEM) {
    int armCmd = param.asInt();
    currentSystemMode = (armCmd == 1) ? ARMED : DISARMED;
    if (currentSystemMode == DISARMED && currentAlarmState != STATE_NORMAL) {
        clearAlarm();
    }
    Blynk.virtualWrite(VPIN_SYSTEM_ARMED, (int)currentSystemMode);
    sendSecurityEvent(currentSystemMode == ARMED ? "SYSTEM_ARMED" : "SYSTEM_DISARMED",
                      currentSystemMode == ARMED ? "Security System Armed" : "Security System Disarmed");
}

// V12: Buzzer Control Command (0 = OFF, 1 = WARNING, 2 = ALARM)
BLYNK_WRITE(VPIN_CMD_BUZZER) {
    int bCmd = param.asInt();
    controlBuzzer(bCmd);
}

// V13: Reset Alarm Command (1 = RESET)
BLYNK_WRITE(VPIN_CMD_RESET_ALARM) {
    if (param.asInt() == 1) {
        resetSystem();
    }
}

// ============================================================
// HARDWARE DRIVER FUNCTIONS
// ============================================================

void readPIR() {
    int val = digitalRead(PIR_PIN);
    pirMotionDetected = (val == HIGH);
}

void readUltrasonic() {
    digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

    long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000); // 30ms timeout
    if (duration == 0) {
        ultrasonicDistanceCm = 400.0; // Out of range or no target
    } else {
        ultrasonicDistanceCm = (duration * 0.0343) / 2.0;
    }
}

void readDoorSwitch() {
    // Reed switch connected to GND with INPUT_PULLUP
    // HIGH = Magnet away (Door OPEN), LOW = Magnet near (Door CLOSED)
    doorSwitchOpen = (digitalRead(DOOR_SWITCH_PIN) == HIGH);
}

void controlServo(bool lock) {
    doorLocked = lock;
    int targetAngle = doorLocked ? SERVO_LOCK_ANGLE : SERVO_UNLOCK_ANGLE;
    doorLockServo.write(targetAngle);
    Blynk.virtualWrite(VPIN_SERVO_STATE, doorLocked ? 1 : 0);
}

void controlBuzzer(int mode) {
    buzzerMode = mode;
    Blynk.virtualWrite(VPIN_BUZZER_STATE, buzzerMode);
    
    if (buzzerMode == 0) {
        noTone(BUZZER_PIN);
        digitalWrite(BUZZER_PIN, LOW);
    } else if (buzzerMode == 1) {
        // Warning pattern: short beep
        tone(BUZZER_PIN, 1000, 100);
    } else if (buzzerMode == 2) {
        // Alarm pattern: loud continuous siren frequency
        tone(BUZZER_PIN, 2400);
    }
}

// ============================================================
// LOCAL SECURITY STATE MACHINE & SENSOR CORRELATION
// ============================================================

void updateSecurityLogic() {
    readPIR();
    readUltrasonic();
    readDoorSwitch();

    // Local door open protection
    if (doorSwitchOpen && currentSystemMode == ARMED) {
        if (currentAlarmState != STATE_ALARM) {
            triggerAlarm("UNAUTHORIZED_DOOR_OPEN");
        }
        return;
    }

    if (currentSystemMode == DISARMED) {
        if (currentAlarmState != STATE_NORMAL) {
            clearAlarm();
        }
        return;
    }

    // Multi-sensor correlation logic
    if (pirMotionDetected) {
        if (ultrasonicDistanceCm < ULTRASONIC_ALARM_DIST_CM) {
            // High confidence intrusion threat
            if (currentAlarmState != STATE_ALARM) {
                triggerAlarm("HIGH_CONFIDENCE_INTRUSION");
            }
        } else if (ultrasonicDistanceCm < ULTRASONIC_WARN_DIST_CM) {
            // Suspicious proximity warning
            if (currentAlarmState == STATE_NORMAL) {
                currentAlarmState = STATE_WARNING;
                controlBuzzer(1);
                sendSecurityEvent("PROXIMITY_WARNING", "Suspicious object detected near front door");
            }
        }
    } else {
        // No motion and clear ultrasonic -> reset warning if active
        if (currentAlarmState == STATE_WARNING && ultrasonicDistanceCm > ULTRASONIC_WARN_DIST_CM) {
            currentAlarmState = STATE_NORMAL;
            controlBuzzer(0);
            sendSecurityEvent("WARNING_CLEARED", "Proximity threat cleared");
        }
    }
}

void triggerAlarm(const char* reason) {
    currentAlarmState = STATE_ALARM;
    controlServo(true); // Ensure door is locked during alarm
    controlBuzzer(2);   // Active loud siren alarm
    
    char msg[128];
    snprintf(msg, sizeof(msg), "ALARM TRIGGERED: %s", reason);
    sendSecurityEvent("ALARM_TRIGGERED", msg);
}

void clearAlarm() {
    currentAlarmState = STATE_NORMAL;
    controlBuzzer(0);
    sendSecurityEvent("ALARM_CLEARED", "Security Alarm Cleared");
}

void resetSystem() {
    currentSystemMode = ARMED;
    currentAlarmState = STATE_NORMAL;
    controlServo(true);
    controlBuzzer(0);
    sendSecurityEvent("SYSTEM_RESET", "Security System Reset Complete");
}

// ============================================================
// TELEMETRY & BLYNK CLOUD SYNC
// ============================================================

void sendTelemetry() {
    if (Blynk.connected()) {
        Blynk.virtualWrite(VPIN_PIR_MOTION, pirMotionDetected ? 1 : 0);
        Blynk.virtualWrite(VPIN_ULTRASONIC_DIST, (int)ultrasonicDistanceCm);
        Blynk.virtualWrite(VPIN_DOOR_STATE, doorSwitchOpen ? 1 : 0);
        Blynk.virtualWrite(VPIN_SERVO_STATE, doorLocked ? 1 : 0);
        Blynk.virtualWrite(VPIN_BUZZER_STATE, buzzerMode);
        Blynk.virtualWrite(VPIN_DOOR_SWITCH, doorSwitchOpen ? 1 : 0);
        Blynk.virtualWrite(VPIN_SYSTEM_ARMED, (int)currentSystemMode);
        Blynk.virtualWrite(VPIN_ESP32_ONLINE, 1);
        Blynk.virtualWrite(VPIN_WIFI_RSSI, WiFi.RSSI());
    }
}

void sendSecurityEvent(const char* eventType, const char* message) {
    Serial.print("[SECURITY EVENT] ");
    Serial.print(eventType);
    Serial.print(" - ");
    Serial.println(message);

    if (Blynk.connected()) {
        char buffer[160];
        snprintf(buffer, sizeof(buffer), "%s|%s", eventType, message);
        Blynk.virtualWrite(VPIN_SECURITY_EVENT, buffer);
    }
}

void checkCloudConnection() {
    if (!Blynk.connected()) {
        Serial.println("BLYNK OFFLINE - Continuing Local Security Monitoring");
    }
}

// ============================================================
// INITIALIZATION & MAIN LOOP
// ============================================================

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("\n=================================");
    Serial.println("ESP32 STARTING");
    Serial.println("Distributed Security System v1.0");
    Serial.println("=================================");

    // GPIO Setup
    pinMode(PIR_PIN, INPUT);
    pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
    pinMode(ULTRASONIC_ECHO_PIN, INPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(DOOR_SWITCH_PIN, INPUT_PULLUP);

    digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    Serial.println("Sensors initialized");

    // Servo Setup
    doorLockServo.attach(SERVO_PIN);
    controlServo(true); // Lock door on startup
    Serial.println("Servo initialized");

    // Buzzer Setup
    controlBuzzer(0);
    Serial.println("Buzzer initialized");

    // Wi-Fi Connection
    Serial.print("WiFi connecting...");
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 15) {
        delay(500);
        Serial.print(".");
        retries++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());

        // Blynk Cloud Connection
        Serial.println("Blynk connecting...");
        Blynk.config(BLYNK_AUTH_TOKEN);
        Blynk.connect(5000); // 5 sec connection timeout

        if (Blynk.connected()) {
            Serial.println("Blynk connected");
        } else {
            Serial.println("Blynk connection timed out - Operating in offline local mode");
        }
    } else {
        Serial.println("\nWiFi connection failed - Operating in offline local mode");
    }

    // Timed Non-blocking Callbacks
    timer.setInterval(100L, updateSecurityLogic);   // Fast sensor acquisition & state machine (100ms)
    timer.setInterval(1000L, sendTelemetry);        // Telemetry upload (1 sec)
    timer.setInterval(5000L, checkCloudConnection);  // Heartbeat check (5 sec)

    Serial.println("Security system ready\n");
}

void loop() {
    if (Blynk.connected()) {
        Blynk.run();
    }
    timer.run();
}
