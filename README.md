# Kerberos Smart Home Security

A distributed trust-based smart home security system designed to improve the reliability and security of IoT devices by combining multiple sensors, authentication, freshness verification, trust evaluation, evidence fusion, and security monitoring.

## 🔐 Project Overview

Traditional smart-home security systems may depend heavily on a single sensor or controller. This project uses a distributed security architecture where information from multiple devices and sensors is evaluated before making security decisions.

The system is designed to detect and handle situations such as:

- Sensor spoofing
- Replay attacks
- Stale sensor messages
- Unauthorized commands
- Compromised or suspicious devices
- Conflicting sensor information
- Abnormal device behaviour

## 🏗️ Architecture

The project contains several major components:

- **Sensors** – Provide environmental and security-related events.
- **Kerberos Device Firmware** – Runs on embedded hardware and communicates sensor events.
- **Security Layer** – Handles authentication, nonces, authorization and trust-related operations.
- **Gateway** – Processes incoming device information and coordinates security decisions.
- **Event Logging** – Records security events for verification and auditing.
- **Dashboard** – Provides a visual interface for monitoring the smart-home system.
- **Testing & Simulation** – Contains attack simulations and security evaluation scripts.

## 🛡️ Security Features

### Device Authentication
Devices are authenticated before their messages are trusted.

### Nonce and Freshness Verification
Nonces help prevent attackers from successfully replaying previously captured messages.

### Trust Evaluation
The system evaluates the trustworthiness of participating devices and sensors.

### Evidence Fusion
Information from multiple sources can be combined to make more reliable security decisions.

### Quarantine
Suspicious or compromised devices can be isolated from trusted operation.

### Command Protection
Owner commands are validated before sensitive actions are allowed.

### Attack Simulation
The project includes simulations for security scenarios such as:

- Replay attacks
- Tampering
- Stale messages
- Unauthorized commands
- Device attacks
- Authentication failures

## 📁 Project Structure

```text
Kerberos-Smart-Home-GitHub/
├── dashboard/
├── event_logging/
├── firmware/
│   └── kerberos_device/
├── gateway/
├── security/
├── sensors/
├── smart-home-security/
├── tests/
├── README.md
└── requirements.txt
