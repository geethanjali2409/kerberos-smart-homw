/**
 * Central Normalized Security System State Store
 * ----------------------------------------------
 * Manages the single source of truth for:
 * - Security State Machine (ARMED, DISARMED, WARNING, ALARM, RESETTING, FAULT)
 * - Sensors (PIR, HC-SR04 ultrasonic, Door Reed Switch)
 * - Actuators (Servo Lock, Piezo Buzzer)
 * - Door & Multi-Window Protection Zones
 * - Real Laptop / Security Camera Status
 * - ESP32 Telemetry & Blynk Cloud Connection State
 * - Operating Mode (SIMULATION vs LIVE_HARDWARE)
 * - Event Logging Engine
 */

class SecurityStore {
  constructor() {
    this.listeners = new Set();

    this.state = {
      operatingMode: 'SIMULATION', // 'SIMULATION' | 'LIVE_HARDWARE'
      cloudSyncEnabled: true,      // Allow simulation triggers to dispatch Blynk commands

      systemMode: 'ARMED',         // 'ARMED' | 'DISARMED'
      alarmState: 'NORMAL',        // 'NORMAL' | 'WARNING' | 'ALARM' | 'RESETTING' | 'FAULT'

      door: {
        state: 'CLOSED',           // 'CLOSED' | 'OPEN'
        locked: true,
        sensorStatus: 'NORMAL'
      },

      windows: [
        { id: 'FRONT_WINDOW', name: 'Front Living Window', state: 'CLOSED', securityState: 'NORMAL', cameraId: 'CAM_FRONT_WINDOW' },
        { id: 'SIDE_WINDOW', name: 'Side Dining Window', state: 'CLOSED', securityState: 'NORMAL', cameraId: 'CAM_SIDE_WINDOW' },
        { id: 'BEDROOM_WINDOW', name: 'Master Bedroom Window', state: 'CLOSED', securityState: 'NORMAL', cameraId: 'CAM_BEDROOM_WINDOW' },
        { id: 'REAR_WINDOW', name: 'Rear Kitchen Window', state: 'CLOSED', securityState: 'NORMAL', cameraId: 'CAM_REAR_WINDOW' }
      ],

      sensors: {
        pir: {
          state: 'CLEAR',          // 'CLEAR' | 'MOTION'
          value: false
        },
        ultrasonic: {
          distance: 250,           // cm
          state: 'CLEAR'           // 'CLEAR' | 'WARNING' | 'ALARM'
        },
        doorSwitch: {
          state: 'CLOSED',         // 'CLOSED' | 'OPEN'
          value: false
        }
      },

      actuators: {
        servo: {
          state: 'LOCKED',         // 'LOCKED' | 'UNLOCKED'
          angle: 90
        },
        buzzer: {
          state: 'OFF',            // 'OFF' | 'WARNING' | 'ALARM'
          mode: 0                  // 0 = OFF, 1 = BEEP, 2 = SIREN
        }
      },

      cameras: [
        { id: 'CAM_FRONT_DOOR', name: 'Front Entrance Cam', status: 'ONLINE', zone: 'FRONT_DOOR', fov: 90, range: 10, motion: false },
        { id: 'CAM_FRONT_WINDOW', name: 'Front Window Cam', status: 'ONLINE', zone: 'FRONT_WINDOW', fov: 75, range: 8, motion: false },
        { id: 'CAM_SIDE_WINDOW', name: 'Side Yard Cam', status: 'ONLINE', zone: 'SIDE_WINDOW', fov: 75, range: 8, motion: false },
        { id: 'CAM_BEDROOM_WINDOW', name: 'Bedroom Cam', status: 'ONLINE', zone: 'BEDROOM_WINDOW', fov: 75, range: 8, motion: false }
      ],

      localWebcam: {
        active: false,
        hasPermission: false,
        stream: null,
        motionDetected: false,
        error: null
      },

      esp32: {
        online: false,
        wifiRSSI: -68,
        lastSeen: null
      },

      cloud: {
        provider: 'BLYNK',
        online: false,
        authToken: 'YourBlynkAuthTokenHere',
        lastSync: null
      },

      xrayMode: false,
      dayNightMode: 'DAY', // 'DAY' | 'NIGHT'
      selectedObject: null,

      events: []
    };

    // Add initial boot event
    this.addEvent({
      source: 'SYSTEM',
      zone: 'GLOBAL',
      deviceId: 'DIGITAL_TWIN_APP',
      eventType: 'SYSTEM_BOOT',
      severity: 'INFO',
      message: 'Smart Home Security System Digital Twin Initialized'
    });
  }

  // Subscribe to state updates
  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach((listener) => listener(this.state));
  }

  getState() {
    return this.state;
  }

  // Generic State Patch
  setState(updater) {
    if (typeof updater === 'function') {
      this.state = { ...this.state, ...updater(this.state) };
    } else {
      this.state = { ...this.state, ...updater };
    }
    this.notify();
  }

  // ============================================================
  // EVENT LOGGING ENGINE
  // ============================================================
  addEvent({ source = 'SYSTEM', zone = 'GENERAL', deviceId = 'ESP32_MAIN', eventType, severity = 'INFO', message }) {
    const newEvent = {
      eventId: `EVT_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      timestamp: new Date().toLocaleTimeString(),
      isoTime: new Date().toISOString(),
      source,
      zone,
      deviceId,
      eventType,
      severity, // 'INFO' | 'WARNING' | 'ALERT' | 'CRITICAL' | 'FAULT'
      message
    };

    const updatedEvents = [newEvent, ...this.state.events].slice(0, 100); // keep max 100 events
    this.state = { ...this.state, events: updatedEvents };
    this.notify();
  }

  // ============================================================
  // MULTI-SENSOR CORRELATION & SECURITY STATE MACHINE
  // ============================================================

  evaluateSecurityLogic() {
    const { systemMode, sensors, door, windows } = this.state;

    // 1. Check for unauthorized open door/window when ARMED
    const anyWindowOpen = windows.some((w) => w.state === 'OPEN');
    const doorOpen = door.state === 'OPEN' || sensors.doorSwitch.state === 'OPEN';

    if (systemMode === 'ARMED') {
      if (doorOpen && this.state.alarmState !== 'ALARM') {
        this.triggerAlarm('UNAUTHORIZED_ENTRY_DOOR', 'FRONT_DOOR', 'Armed door forced open!');
        return;
      }

      if (anyWindowOpen && this.state.alarmState !== 'ALARM') {
        const openedWin = windows.find((w) => w.state === 'OPEN');
        this.triggerAlarm('UNAUTHORIZED_ENTRY_WINDOW', openedWin ? openedWin.id : 'WINDOW', `Armed window opened: ${openedWin ? openedWin.name : ''}`);
        return;
      }

      // 2. PIR + Ultrasonic Proximity Multi-Sensor Correlation
      const pirActive = sensors.pir.state === 'MOTION';
      const distance = sensors.ultrasonic.distance;

      if (pirActive) {
        if (distance <= 20) {
          // High confidence threat -> ALARM
          if (this.state.alarmState !== 'ALARM') {
            this.triggerAlarm('HIGH_CONFIDENCE_INTRUSION', 'FRONT_DOOR', 'High confidence threat! Motion + Close proximity (<20cm)');
          }
        } else if (distance <= 50) {
          // Warning stage
          if (this.state.alarmState === 'NORMAL') {
            this.setAlarmState('WARNING', 'PROXIMITY_WARNING', 'FRONT_DOOR', 'Suspicious activity detected near front entrance');
            this.setBuzzerState('WARNING', 1);
          }
        }
      } else {
        // Threat cleared naturally
        if (this.state.alarmState === 'WARNING' && distance > 50) {
          this.setAlarmState('NORMAL', 'THREAT_CLEARED', 'FRONT_DOOR', 'Proximity threat cleared');
          this.setBuzzerState('OFF', 0);
        }
      }
    }
  }

  // ============================================================
  // SYSTEM ACTIONS
  // ============================================================

  setOperatingMode(mode) {
    this.setState({ operatingMode: mode });
    this.addEvent({
      source: 'USER',
      zone: 'SYSTEM',
      eventType: 'OPERATING_MODE_CHANGE',
      severity: 'INFO',
      message: `Switched operating mode to ${mode}`
    });
  }

  setCloudSyncEnabled(enabled) {
    this.setState({ cloudSyncEnabled: enabled });
  }

  setArmSystem(arm) {
    const newSystemMode = arm ? 'ARMED' : 'DISARMED';
    this.setState({ systemMode: newSystemMode });
    
    if (!arm && this.state.alarmState !== 'NORMAL') {
      this.clearAlarm();
    }

    this.addEvent({
      source: 'USER',
      zone: 'SYSTEM',
      eventType: arm ? 'SYSTEM_ARMED' : 'SYSTEM_DISARMED',
      severity: arm ? 'INFO' : 'WARNING',
      message: arm ? 'Security System Armed' : 'Security System Disarmed'
    });

    this.evaluateSecurityLogic();
  }

  setDoorLock(lock) {
    this.setState({
      door: { ...this.state.door, locked: lock },
      actuators: {
        ...this.state.actuators,
        servo: { state: lock ? 'LOCKED' : 'UNLOCKED', angle: lock ? 90 : 0 }
      }
    });

    this.addEvent({
      source: 'USER',
      zone: 'FRONT_DOOR',
      eventType: lock ? 'SERVO_LOCKED' : 'SERVO_UNLOCKED',
      severity: 'INFO',
      message: lock ? 'Front door lock engaged (Servo 90°)' : 'Front door lock disengaged (Servo 0°)'
    });
  }

  setDoorState(state) {
    const isOpen = state === 'OPEN';
    this.setState({
      door: { ...this.state.door, state },
      sensors: {
        ...this.state.sensors,
        doorSwitch: { state, value: isOpen }
      }
    });

    this.addEvent({
      source: 'HARDWARE',
      zone: 'FRONT_DOOR',
      eventType: isOpen ? 'DOOR_OPENED' : 'DOOR_CLOSED',
      severity: isOpen ? 'WARNING' : 'INFO',
      message: isOpen ? 'Front door physical switch opened' : 'Front door physical switch closed'
    });

    this.evaluateSecurityLogic();
  }

  setWindowOpen(windowId, isOpen) {
    const updatedWindows = this.state.windows.map((w) =>
      w.id === windowId
        ? {
            ...w,
            state: isOpen ? 'OPEN' : 'CLOSED',
            securityState: isOpen && this.state.systemMode === 'ARMED' ? 'TRIGGERED' : 'NORMAL'
          }
        : w
    );

    this.setState({ windows: updatedWindows });

    this.addEvent({
      source: 'SIMULATION',
      zone: windowId,
      eventType: isOpen ? 'WINDOW_OPENED' : 'WINDOW_CLOSED',
      severity: isOpen ? 'WARNING' : 'INFO',
      message: `${windowId} set to ${isOpen ? 'OPEN' : 'CLOSED'}`
    });

    this.evaluateSecurityLogic();
  }

  setPIRMotion(hasMotion) {
    this.setState({
      sensors: {
        ...this.state.sensors,
        pir: { state: hasMotion ? 'MOTION' : 'CLEAR', value: hasMotion }
      }
    });

    if (hasMotion) {
      this.addEvent({
        source: 'PIR_SENSOR',
        zone: 'FRONT_DOOR',
        eventType: 'MOTION_DETECTED',
        severity: 'WARNING',
        message: 'Motion detected by front entrance PIR sensor'
      });
    }

    this.evaluateSecurityLogic();
  }

  setUltrasonicDistance(distCm) {
    const state = distCm <= 20 ? 'ALARM' : distCm <= 50 ? 'WARNING' : 'CLEAR';
    this.setState({
      sensors: {
        ...this.state.sensors,
        ultrasonic: { distance: distCm, state }
      }
    });

    this.evaluateSecurityLogic();
  }

  setBuzzerState(state, mode = 0) {
    this.setState({
      actuators: {
        ...this.state.actuators,
        buzzer: { state, mode }
      }
    });
  }

  setAlarmState(state, eventType, zone, message) {
    this.setState({ alarmState: state });
    this.addEvent({
      source: 'SECURITY_ENGINE',
      zone,
      eventType,
      severity: state === 'ALARM' ? 'CRITICAL' : state === 'WARNING' ? 'WARNING' : 'INFO',
      message
    });
  }

  triggerAlarm(eventType, zone, message) {
    this.setState({
      alarmState: 'ALARM',
      door: { ...this.state.door, locked: true },
      actuators: {
        servo: { state: 'LOCKED', angle: 90 },
        buzzer: { state: 'ALARM', mode: 2 }
      }
    });

    this.addEvent({
      source: 'SECURITY_ENGINE',
      zone,
      eventType,
      severity: 'CRITICAL',
      message: `[ALARM ACTIVATED] ${message}`
    });
  }

  clearAlarm() {
    this.setState({
      alarmState: 'NORMAL',
      actuators: {
        ...this.state.actuators,
        buzzer: { state: 'OFF', mode: 0 }
      }
    });

    this.addEvent({
      source: 'USER',
      zone: 'GLOBAL',
      eventType: 'ALARM_CLEARED',
      severity: 'INFO',
      message: 'Alarm reset by operator'
    });
  }

  resetSystem() {
    this.setState({
      systemMode: 'ARMED',
      alarmState: 'NORMAL',
      door: { state: 'CLOSED', locked: true, sensorStatus: 'NORMAL' },
      sensors: {
        pir: { state: 'CLEAR', value: false },
        ultrasonic: { distance: 250, state: 'CLEAR' },
        doorSwitch: { state: 'CLOSED', value: false }
      },
      actuators: {
        servo: { state: 'LOCKED', angle: 90 },
        buzzer: { state: 'OFF', mode: 0 }
      }
    });

    this.addEvent({
      source: 'USER',
      zone: 'GLOBAL',
      eventType: 'SYSTEM_RESET',
      severity: 'INFO',
      message: 'Security System fully reset to default armed state'
    });
  }

  toggleXrayMode() {
    this.setState({ xrayMode: !this.state.xrayMode });
  }

  setDayNightMode(mode) {
    this.setState({ dayNightMode: mode });
  }

  setSelectedObject(obj) {
    this.setState({ selectedObject: obj });
  }
}

export const securityStore = new SecurityStore();
