/**
 * Blynk Service Layer
 * -------------------
 * Encapsulates all Blynk REST API calls (get datastream value, update datastream value, isConnected).
 * Manages periodic polling in LIVE HARDWARE mode and dispatches Virtual Pin commands.
 */

import { BLYNK_CONFIG } from '../config/blynkConfig.js';
import { securityStore } from '../state/securityStore.js';

class BlynkService {
  constructor() {
    this.authToken = BLYNK_CONFIG.DEFAULT_AUTH_TOKEN;
    this.baseUrl = BLYNK_CONFIG.SERVER_URL;
    this.pollTimer = null;
    this.isPolling = false;
  }

  setAuthToken(token) {
    if (token && token.trim()) {
      this.authToken = token.trim();
      securityStore.setState({
        cloud: { ...securityStore.getState().cloud, authToken: this.authToken }
      });
    }
  }

  getAuthToken() {
    return this.authToken;
  }

  // ============================================================
  // BLYNK API CALLS (HTTP GET / UPDATE)
  // ============================================================

  async getPinValue(vPin) {
    try {
      const url = `${this.baseUrl}/get?token=${this.authToken}&${vPin}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.text();
      return data;
    } catch (err) {
      console.warn(`[BlynkService] Error fetching ${vPin}:`, err.message);
      return null;
    }
  }

  async updatePinValue(vPin, value) {
    try {
      const url = `${this.baseUrl}/update?token=${this.authToken}&${vPin}=${encodeURIComponent(value)}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Blynk update error! status: ${response.status}`);
      
      securityStore.addEvent({
        source: 'BLYNK_SERVICE',
        zone: 'CLOUD',
        eventType: 'COMMAND_DISPATCHED',
        severity: 'INFO',
        message: `Dispatched Blynk command ${vPin} = ${value}`
      });
      return true;
    } catch (err) {
      console.warn(`[BlynkService] Error updating ${vPin}:`, err.message);
      securityStore.addEvent({
        source: 'BLYNK_SERVICE',
        zone: 'CLOUD',
        eventType: 'COMMAND_FAILED',
        severity: 'FAULT',
        message: `Failed to dispatch Blynk command ${vPin}: ${err.message}`
      });
      return false;
    }
  }

  async checkHardwareStatus() {
    try {
      const url = `${this.baseUrl}/isHardwareConnected?token=${this.authToken}`;
      const response = await fetch(url);
      if (!response.ok) return false;
      const text = await response.text();
      return text.trim() === 'true';
    } catch (err) {
      return false;
    }
  }

  // ============================================================
  // POLLING & DATASTREAM SYNC ENGINE
  // ============================================================

  startPolling() {
    if (this.isPolling) return;
    this.isPolling = true;

    this.pollTimer = setInterval(async () => {
      await this.pollBlynkDatastreams();
    }, BLYNK_CONFIG.POLL_INTERVAL_MS);

    securityStore.addEvent({
      source: 'BLYNK_SERVICE',
      zone: 'CLOUD',
      eventType: 'POLLING_STARTED',
      severity: 'INFO',
      message: 'Started polling Blynk Cloud Datastreams'
    });
  }

  stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    this.isPolling = false;

    securityStore.setState({
      cloud: { ...securityStore.getState().cloud, online: false },
      esp32: { ...securityStore.getState().esp32, online: false }
    });

    securityStore.addEvent({
      source: 'BLYNK_SERVICE',
      zone: 'CLOUD',
      eventType: 'POLLING_STOPPED',
      severity: 'INFO',
      message: 'Stopped polling Blynk Cloud'
    });
  }

  async pollBlynkDatastreams() {
    const state = securityStore.getState();
    if (state.operatingMode !== 'LIVE_HARDWARE') return;

    try {
      const isOnline = await this.checkHardwareStatus();
      
      // Fetch telemetry batch
      const pirVal = await this.getPinValue(BLYNK_CONFIG.PINS.PIR_MOTION);
      const distVal = await this.getPinValue(BLYNK_CONFIG.PINS.ULTRASONIC_DIST);
      const doorVal = await this.getPinValue(BLYNK_CONFIG.PINS.DOOR_STATE);
      const servoVal = await this.getPinValue(BLYNK_CONFIG.PINS.SERVO_STATE);
      const buzzerVal = await this.getPinValue(BLYNK_CONFIG.PINS.BUZZER_STATE);
      const armedVal = await this.getPinValue(BLYNK_CONFIG.PINS.SYSTEM_ARMED);
      const rssiVal = await this.getPinValue(BLYNK_CONFIG.PINS.WIFI_RSSI);

      // Update Normalized State from Live Hardware Telemetry
      securityStore.setState({
        cloud: { ...state.cloud, online: true, lastSync: new Date().toLocaleTimeString() },
        esp32: {
          online: isOnline,
          wifiRSSI: rssiVal !== null ? parseInt(rssiVal, 10) || -65 : -65,
          lastSeen: new Date().toLocaleTimeString()
        }
      });

      if (pirVal !== null) securityStore.setPIRMotion(parseInt(pirVal, 10) === 1);
      if (distVal !== null) securityStore.setUltrasonicDistance(parseFloat(distVal) || 250);
      if (doorVal !== null) securityStore.setDoorState(parseInt(doorVal, 10) === 1 ? 'OPEN' : 'CLOSED');
      if (servoVal !== null) securityStore.setDoorLock(parseInt(servoVal, 10) === 1);
      if (buzzerVal !== null) {
        const bMode = parseInt(buzzerVal, 10) || 0;
        securityStore.setBuzzerState(bMode === 0 ? 'OFF' : bMode === 1 ? 'WARNING' : 'ALARM', bMode);
      }
      if (armedVal !== null) {
        const isArmed = parseInt(armedVal, 10) === 1;
        if (state.systemMode !== (isArmed ? 'ARMED' : 'DISARMED')) {
          securityStore.setArmSystem(isArmed);
        }
      }
    } catch (err) {
      securityStore.setState({
        cloud: { ...state.cloud, online: false }
      });
    }
  }

  // ============================================================
  // PUBLIC DASHBOARD COMMAND INTERFACE
  // ============================================================

  async lockDoor(lock) {
    securityStore.setDoorLock(lock);
    const state = securityStore.getState();
    if (state.cloudSyncEnabled || state.operatingMode === 'LIVE_HARDWARE') {
      await this.updatePinValue(BLYNK_CONFIG.PINS.CMD_DOOR_LOCK, lock ? 1 : 0);
    }
  }

  async armSystem(arm) {
    securityStore.setArmSystem(arm);
    const state = securityStore.getState();
    if (state.cloudSyncEnabled || state.operatingMode === 'LIVE_HARDWARE') {
      await this.updatePinValue(BLYNK_CONFIG.PINS.CMD_ARM_SYSTEM, arm ? 1 : 0);
    }
  }

  async triggerBuzzer(mode) {
    securityStore.setBuzzerState(mode === 0 ? 'OFF' : mode === 1 ? 'WARNING' : 'ALARM', mode);
    const state = securityStore.getState();
    if (state.cloudSyncEnabled || state.operatingMode === 'LIVE_HARDWARE') {
      await this.updatePinValue(BLYNK_CONFIG.PINS.CMD_BUZZER, mode);
    }
  }

  async resetAlarm() {
    securityStore.resetSystem();
    const state = securityStore.getState();
    if (state.cloudSyncEnabled || state.operatingMode === 'LIVE_HARDWARE') {
      await this.updatePinValue(BLYNK_CONFIG.PINS.CMD_RESET_ALARM, 1);
    }
  }
}

export const blynkService = new BlynkService();
