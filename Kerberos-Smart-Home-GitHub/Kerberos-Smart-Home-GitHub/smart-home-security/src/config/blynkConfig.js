/**
 * Blynk Cloud Configuration
 * Single source of truth for Virtual Pin Datastreams and Cloud API endpoints.
 */

export const BLYNK_CONFIG = {
  // Primary Blynk Cloud REST API Server
  SERVER_URL: 'https://blynk.cloud/external/api',
  
  // Default Auth Token (Placeholder - should be set via UI or .env)
  DEFAULT_AUTH_TOKEN: 'YourBlynkAuthTokenHere',
  
  // Virtual Pin Datastream Assignments
  PINS: {
    // Sensor Telemetry
    PIR_MOTION: 'V0',
    ULTRASONIC_DIST: 'V1',
    DOOR_STATE: 'V2',
    WINDOW_STATE: 'V3',
    SERVO_STATE: 'V4',
    BUZZER_STATE: 'V5',
    DOOR_SWITCH: 'V6',
    SYSTEM_ARMED: 'V7',
    ESP32_ONLINE: 'V8',
    WIFI_RSSI: 'V9',

    // Commands (Dashboard -> ESP32)
    CMD_DOOR_LOCK: 'V10',
    CMD_ARM_SYSTEM: 'V11',
    CMD_BUZZER: 'V12',
    CMD_RESET_ALARM: 'V13',

    // Camera & Event Metadata
    CAMERA_STATUS: 'V14',
    SECURITY_EVENT: 'V15'
  },

  // Polling Interval in milliseconds for Live Hardware mode
  POLL_INTERVAL_MS: 1500,

  // Offline Heartbeat Timeout in milliseconds
  HEARTBEAT_TIMEOUT_MS: 6000
};
