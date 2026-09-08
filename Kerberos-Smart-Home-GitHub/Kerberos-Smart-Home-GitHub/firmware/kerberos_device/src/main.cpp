#include <Arduino.h>
#include <ESP32Servo.h>

Servo lockServo;

constexpr int SERVO_PIN = 25;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println("=================================");
    Serial.println("KERBEROS ESP32 SERVO TEST");
    Serial.println("=================================");

    lockServo.setPeriodHertz(50);
    lockServo.attach(SERVO_PIN, 500, 2400);

    Serial.println("[SERVO] Attached to GPIO25");
}

void loop() {
    Serial.println("[SERVO] LOCK position: 0 degrees");
    lockServo.write(0);
    delay(2000);

    Serial.println("[SERVO] UNLOCK position: 90 degrees");
    lockServo.write(90);
    delay(2000);

    Serial.println("[SERVO] Returning to LOCK: 0 degrees");
    lockServo.write(0);
    delay(2000);
}