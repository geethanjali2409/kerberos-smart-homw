import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Lock,
  Unlock,
  Radio,
  Activity,
  Bell,
  Sun,
  Moon,
  Eye,
  Compass,
  Wifi,
  Cloud,
  Zap,
  RotateCcw,
  Sliders,
  Maximize2
} from 'lucide-react';

import { securityStore } from '../state/securityStore.js';
import { blynkService } from '../services/blynkService.js';

import HouseCanvas from '../3d/HouseCanvas.jsx';
import CameraManager from '../camera/CameraManager.jsx';
import EventLog from './EventLog.jsx';
import TestPanel from './TestPanel.jsx';
import InfoModal from './InfoModal.jsx';

export default function Dashboard() {
  const [state, setState] = useState(securityStore.getState());
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [showTestPanel, setShowTestPanel] = useState(true);

  useEffect(() => {
    const unsubscribe = securityStore.subscribe(setState);
    return () => unsubscribe();
  }, []);

  const isArmed = state.systemMode === 'ARMED';
  const isAlarm = state.alarmState === 'ALARM';
  const isWarning = state.alarmState === 'WARNING';
  const isLive = state.operatingMode === 'LIVE_HARDWARE';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* ============================================================ */}
      {/* 1. TOP CONTROL BAR / HEADER                                  */}
      {/* ============================================================ */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-6 py-3 sticky top-0 z-40 backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-indigo-600 to-sky-600 rounded-xl shadow-lg shadow-indigo-950/50">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              SMART HOME SECURITY DIGITAL TWIN
            </h1>
            <p className="text-xs text-slate-400 font-medium">ESP32 • Blynk Cloud • 3D WebGL Engine</p>
          </div>
        </div>

        {/* Global Security State Badges */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Armed / Disarmed Badge */}
          <div className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1.5 shadow-md ${
            isAlarm
              ? 'bg-rose-950/90 border-rose-500 text-rose-200 animate-bounce'
              : isWarning
              ? 'bg-amber-950/90 border-amber-500 text-amber-200'
              : isArmed
              ? 'bg-emerald-950/80 border-emerald-500/80 text-emerald-300'
              : 'bg-slate-800 border-slate-700 text-slate-400'
          }`}>
            {isAlarm ? <ShieldAlert className="w-4 h-4 text-rose-400" /> : <ShieldCheck className="w-4 h-4" />}
            <span>{isAlarm ? 'ALARM TRIGGERED' : isWarning ? 'WARNING ACTIVE' : isArmed ? 'SYSTEM ARMED' : 'SYSTEM DISARMED'}</span>
          </div>

          {/* Operating Mode Switcher */}
          <button
            onClick={() => {
              const nextMode = isLive ? 'SIMULATION' : 'LIVE_HARDWARE';
              securityStore.setOperatingMode(nextMode);
              if (nextMode === 'LIVE_HARDWARE') {
                blynkService.startPolling();
              } else {
                blynkService.stopPolling();
              }
            }}
            className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1.5 transition-all shadow-md ${
              isLive
                ? 'bg-indigo-900/80 border-indigo-500 text-indigo-200 shadow-indigo-950/50'
                : 'bg-emerald-900/80 border-emerald-500 text-emerald-200 shadow-emerald-950/50'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span>MODE: {state.operatingMode}</span>
          </button>

          {/* Blynk Cloud Connection Status */}
          <div className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 ${
            state.cloud.online ? 'bg-sky-950/80 border-sky-500 text-sky-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <Cloud className="w-3.5 h-3.5" />
            <span>BLYNK: {state.cloud.online ? 'ONLINE' : 'OFFLINE'}</span>
          </div>

          {/* ESP32 Hardware Connection Status */}
          <div className={`px-2.5 py-1 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 ${
            state.esp32.online ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300' : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}>
            <Wifi className="w-3.5 h-3.5" />
            <span>ESP32: {state.esp32.online ? 'CONNECTED' : 'LOCAL'}</span>
          </div>
        </div>
      </header>

      {/* ============================================================ */}
      {/* 2. MAIN APPLICATION CONTENT GRID                             */}
      {/* ============================================================ */}
      <main className="flex-1 p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1920px] mx-auto w-full">
        {/* LEFT COLUMN: 3D DIGITAL TWIN VIEWPORT (8 Cols) */}
        <section className="lg:col-span-8 flex flex-col gap-4 min-h-[500px] lg:min-h-[650px]">
          {/* 3D Scene Viewport Card */}
          <div className="relative flex-1 bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
            {/* Viewport Toolbar */}
            <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2 bg-slate-950/80 backdrop-blur-md p-1.5 rounded-xl border border-slate-700/60 shadow-xl">
              {/* Day / Night Toggle */}
              <button
                onClick={() => securityStore.setDayNightMode(state.dayNightMode === 'DAY' ? 'NIGHT' : 'DAY')}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 border border-slate-700"
              >
                {state.dayNightMode === 'DAY' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
                <span>{state.dayNightMode}</span>
              </button>

              {/* X-Ray Semi-Transparent Walls Toggle */}
              <button
                onClick={() => securityStore.toggleXrayMode()}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 border ${
                  state.xrayMode
                    ? 'bg-indigo-600 text-white border-indigo-400 shadow-lg shadow-indigo-950/50'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                }`}
              >
                <Eye className="w-3.5 h-3.5" />
                <span>X-RAY VIEW {state.xrayMode ? 'ON' : 'OFF'}</span>
              </button>

              {/* Toggle Developer Simulator Panel */}
              <button
                onClick={() => setShowTestPanel(!showTestPanel)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 border border-slate-700"
              >
                <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                <span>TEST PANEL</span>
              </button>
            </div>

            {/* 3D WebGL Canvas */}
            <div className="w-full h-full min-h-[500px]">
              <HouseCanvas onSelectObject={(id) => setSelectedObjectId(id)} />
            </div>

            {/* Viewport Info Overlay Footer */}
            <div className="absolute bottom-4 left-4 z-20 text-[11px] font-mono text-slate-400 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800">
              💡 Tip: Left-click + drag to rotate • Right-click to pan • Scroll to zoom • Click objects for hardware diagnostics
            </div>
          </div>

          {/* Interactive Developer Test Panel */}
          {showTestPanel && <TestPanel state={state} />}
        </section>

        {/* RIGHT COLUMN: SECURITY DASHBOARD CONTROLS & LOGS (4 Cols) */}
        <section className="lg:col-span-4 flex flex-col gap-4">
          {/* Quick Action Commands Card */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl backdrop-blur-md">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-400" /> Security Command Center
            </h2>

            <div className="grid grid-cols-2 gap-3">
              {/* ARM / DISARM Button */}
              <button
                onClick={() => blynkService.armSystem(!isArmed)}
                className={`py-3 px-4 rounded-xl font-bold text-xs transition-all shadow-lg flex items-center justify-center gap-2 ${
                  isArmed
                    ? 'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/40'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{isArmed ? 'DISARM SYSTEM' : 'ARM SYSTEM'}</span>
              </button>

              {/* LOCK / UNLOCK DOOR Button */}
              <button
                onClick={() => blynkService.lockDoor(!state.door.locked)}
                className={`py-3 px-4 rounded-xl font-bold text-xs transition-all shadow-lg flex items-center justify-center gap-2 ${
                  state.door.locked
                    ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-950/40'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-950/40'
                }`}
              >
                {state.door.locked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                <span>{state.door.locked ? 'UNLOCK DOOR' : 'LOCK DOOR'}</span>
              </button>

              {/* TEST ALARM Trigger */}
              <button
                onClick={() => blynkService.triggerBuzzer(2)}
                className="py-2.5 px-3 bg-rose-600/90 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition-all shadow-lg shadow-rose-950/40 flex items-center justify-center gap-2"
              >
                <ShieldAlert className="w-4 h-4" /> TEST ALARM
              </button>

              {/* RESET SYSTEM Button */}
              <button
                onClick={() => blynkService.resetAlarm()}
                className="py-2.5 px-3 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-xl text-xs font-semibold transition-all border border-slate-600 flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" /> RESET SYSTEM
              </button>
            </div>
          </div>

          {/* Laptop CCTV Camera Manager */}
          <CameraManager />

          {/* Telemetry Sensor Overview Cards */}
          <div className="bg-slate-800/90 border border-slate-700/80 rounded-2xl p-5 shadow-xl backdrop-blur-md">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" /> Sensor Telemetry Grid
            </h2>

            <div className="grid grid-cols-2 gap-3 text-xs">
              {/* PIR Motion Telemetry */}
              <div className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">PIR Motion</span>
                  <span className={`font-mono font-bold ${state.sensors.pir.state === 'MOTION' ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {state.sensors.pir.state}
                  </span>
                </div>
                <Activity className={`w-5 h-5 ${state.sensors.pir.state === 'MOTION' ? 'text-rose-400 animate-pulse' : 'text-slate-600'}`} />
              </div>

              {/* Ultrasonic Distance Telemetry */}
              <div className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">Ultrasonic Dist</span>
                  <span className="font-mono font-bold text-sky-400">{state.sensors.ultrasonic.distance} cm</span>
                </div>
                <Radio className="w-5 h-5 text-sky-400" />
              </div>

              {/* Front Door Lock Servo */}
              <div className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">Servo Deadbolt</span>
                  <span className="font-mono font-bold text-amber-400">{state.actuators.servo.state}</span>
                </div>
                <Lock className="w-5 h-5 text-amber-400" />
              </div>

              {/* Piezo Buzzer State */}
              <div className="bg-slate-900/60 border border-slate-700/50 p-3 rounded-xl flex items-center justify-between">
                <div>
                  <span className="text-[11px] text-slate-400 block font-medium">Piezo Siren</span>
                  <span className="font-mono font-bold text-purple-400">{state.actuators.buzzer.state}</span>
                </div>
                <Bell className="w-5 h-5 text-purple-400" />
              </div>
            </div>

            {/* Window Security Zones */}
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <span className="text-[11px] font-semibold text-slate-400 block mb-2">Windows Protection Grid</span>
              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                {state.windows.map((w) => (
                  <div key={w.id} className="bg-slate-900/40 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
                    <span className="text-slate-300 truncate">{w.name.split(' ')[0]}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${w.state === 'OPEN' ? 'bg-amber-950 text-amber-300' : 'bg-emerald-950 text-emerald-300'}`}>
                      {w.state}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Event Log Stream */}
          <div className="flex-1 min-h-[250px]">
            <EventLog events={state.events} />
          </div>
        </section>
      </main>

      {/* Detail Info Modal for Clicked 3D Objects */}
      <InfoModal selectedObjectId={selectedObjectId} onClose={() => setSelectedObjectId(null)} />
    </div>
  );
}
