import React from 'react';
import { X, Shield, Cpu, Eye, Radio, Lock, Activity, Bell } from 'lucide-react';
import { securityStore } from '../state/securityStore.js';

export default function InfoModal({ selectedObjectId, onClose }) {
  if (!selectedObjectId) return null;

  const state = securityStore.getState();

  const getObjectDetails = () => {
    switch (selectedObjectId) {
      case 'ESP32_CONTROLLER':
        return {
          title: 'ESP32 Security Controller Node',
          category: 'Embedded Microcontroller',
          icon: <Cpu className="w-6 h-6 text-emerald-400" />,
          details: [
            { label: 'Processor', value: 'Dual-Core Tensilica LX6 (240MHz)' },
            { label: 'Status', value: state.esp32.online ? 'ONLINE' : 'OFFLINE (Local Operation)' },
            { label: 'Wi-Fi RSSI', value: `${state.esp32.wifiRSSI} dBm` },
            { label: 'PIR Pin', value: 'GPIO 27 (Input)' },
            { label: 'HC-SR04 Trig/Echo', value: 'GPIO 5 / GPIO 18 (Voltage Divider)' },
            { label: 'Servo Lock Pin', value: 'GPIO 13 (PWM)' },
            { label: 'Alarm Buzzer Pin', value: 'GPIO 14 (Tone Output)' },
            { label: 'Door Switch Pin', value: 'GPIO 25 (INPUT_PULLUP)' }
          ]
        };
      case 'PIR_SENSOR':
        return {
          title: 'PIR Motion Sensor',
          category: 'Front Entrance Intrusion Detection',
          icon: <Activity className="w-6 h-6 text-rose-400" />,
          details: [
            { label: 'GPIO Assignment', value: 'GPIO 27' },
            { label: 'Detection State', value: state.sensors.pir.state },
            { label: 'Field of View', value: '120° Fresnel Cone' },
            { label: 'Detection Range', value: '0.5m - 5.0m' }
          ]
        };
      case 'HC_SR04_SENSOR':
        return {
          title: 'HC-SR04 Ultrasonic Sensor',
          category: 'Sonar Proximity Meter',
          icon: <Radio className="w-6 h-6 text-sky-400" />,
          details: [
            { label: 'GPIO Trig / Echo', value: 'GPIO 5 / GPIO 18' },
            { label: 'Measured Distance', value: `${state.sensors.ultrasonic.distance} cm` },
            { label: 'Proximity Status', value: state.sensors.ultrasonic.state },
            { label: 'Level Shifting', value: '1kΩ / 2kΩ Voltage Divider on Echo' }
          ]
        };
      case 'SERVO_LOCK':
        return {
          title: 'Micro Servo Lock Actuator',
          category: 'Front Door Physical Deadbolt',
          icon: <Lock className="w-6 h-6 text-amber-400" />,
          details: [
            { label: 'GPIO Signal Pin', value: 'GPIO 13' },
            { label: 'Current Lock State', value: state.actuators.servo.state },
            { label: 'Servo Angle', value: `${state.actuators.servo.angle}° (90° = Locked, 0° = Unlocked)` },
            { label: 'Power Supply', value: 'External 5V DC' }
          ]
        };
      case 'ALARM_BUZZER':
        return {
          title: 'Piezo Alarm Siren',
          category: 'Audible Threat Annunciator',
          icon: <Bell className="w-6 h-6 text-purple-400" />,
          details: [
            { label: 'GPIO Output Pin', value: 'GPIO 14' },
            { label: 'Buzzer State', value: state.actuators.buzzer.state },
            { label: 'Siren Frequency', value: state.actuators.buzzer.mode === 2 ? '2400Hz Alarm Tone' : 'Off / Periodic Beep' }
          ]
        };
      case 'FRONT_DOOR_PANEL':
        return {
          title: 'Front Entrance Door Zone',
          category: 'Primary Entry Access Point',
          icon: <Shield className="w-6 h-6 text-indigo-400" />,
          details: [
            { label: 'Physical Door State', value: state.door.state },
            { label: 'Lock Deadbolt', value: state.door.locked ? 'LOCKED' : 'UNLOCKED' },
            { label: 'Reed Magnet Switch', value: state.sensors.doorSwitch.state },
            { label: 'Zone Security Mode', value: state.systemMode }
          ]
        };
      default:
        if (selectedObjectId.startsWith('CAM_')) {
          const cam = state.cameras.find((c) => c.id === selectedObjectId);
          return {
            title: cam ? cam.name : 'Security Camera',
            category: 'CCTV Surveillance Zone',
            icon: <Eye className="w-6 h-6 text-sky-400" />,
            details: [
              { label: 'Camera ID', value: selectedObjectId },
              { label: 'Status', value: cam ? cam.status : 'ONLINE' },
              { label: 'Coverage Zone', value: cam ? cam.zone : 'SURVEILLANCE' },
              { label: 'FOV Angle', value: `${cam ? cam.fov : 75}°` }
            ]
          };
        }
        if (selectedObjectId.endsWith('_WINDOW')) {
          const win = state.windows.find((w) => w.id === selectedObjectId);
          return {
            title: win ? win.name : 'Window Security Zone',
            category: 'Perimeter Window Barrier',
            icon: <Shield className="w-6 h-6 text-amber-400" />,
            details: [
              { label: 'Window ID', value: selectedObjectId },
              { label: 'Physical State', value: win ? win.state : 'CLOSED' },
              { label: 'Security Alarm Status', value: win ? win.securityState : 'NORMAL' },
              { label: 'Linked CCTV', value: win ? win.cameraId : 'N/A' }
            ]
          };
        }
        return {
          title: selectedObjectId,
          category: 'Architectural Component',
          icon: <Shield className="w-6 h-6 text-slate-400" />,
          details: [{ label: 'Object ID', value: selectedObjectId }]
        };
    }
  };

  const obj = getObjectDetails();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-slate-800 rounded-xl border border-slate-700">{obj.icon}</div>
          <div>
            <h3 className="text-base font-bold text-slate-100">{obj.title}</h3>
            <span className="text-xs text-slate-400">{obj.category}</span>
          </div>
        </div>

        <div className="space-y-2 border-t border-b border-slate-800 py-4 my-2 text-xs">
          {obj.details.map((d, i) => (
            <div key={i} className="flex justify-between items-center py-1">
              <span className="text-slate-400 font-medium">{d.label}:</span>
              <span className="text-slate-100 font-mono font-semibold">{d.value}</span>
            </div>
          ))}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-all"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
