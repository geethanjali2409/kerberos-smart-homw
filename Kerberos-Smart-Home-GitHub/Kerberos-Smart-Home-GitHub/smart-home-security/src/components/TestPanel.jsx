import React from 'react';
import { Sliders, Activity, Radio, Lock, Unlock, Volume2, ShieldAlert, RotateCcw } from 'lucide-react';
import { securityStore } from '../state/securityStore.js';
import { blynkService } from '../services/blynkService.js';

export default function TestPanel({ state }) {
  const isArmed = state.systemMode === 'ARMED';
  const isLocked = state.door.locked;
  const isPirMotion = state.sensors.pir.state === 'MOTION';
  const distance = state.sensors.ultrasonic.distance;
  const doorState = state.door.state;

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-4 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider">Developer Test Panel</h3>
        </div>
        <span className="text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded">
          HARDWARE SIMULATOR
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* 1. PIR Motion Injector */}
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
          <div className="text-slate-400 font-semibold mb-2 flex items-center justify-between">
            <span>PIR Motion Sensor</span>
            <Activity className={`w-4 h-4 ${isPirMotion ? 'text-rose-400 animate-pulse' : 'text-slate-500'}`} />
          </div>
          <button
            onClick={() => {
              const nextVal = !isPirMotion;
              securityStore.setPIRMotion(nextVal);
            }}
            className={`w-full py-2 px-3 rounded font-medium transition-all ${
              isPirMotion ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
            }`}
          >
            {isPirMotion ? 'Simulating Motion (HIGH)' : 'Simulate Motion (TRIGGER)'}
          </button>
        </div>

        {/* 2. HC-SR04 Ultrasonic Distance Slider */}
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
          <div className="text-slate-400 font-semibold mb-1 flex items-center justify-between">
            <span>Ultrasonic Proximity</span>
            <Radio className="w-4 h-4 text-sky-400" />
          </div>
          <div className="flex justify-between font-mono text-xs text-sky-300 font-bold mb-1">
            <span>Distance:</span>
            <span>{distance} cm</span>
          </div>
          <input
            type="range"
            min="5"
            max="250"
            value={distance}
            onChange={(e) => securityStore.setUltrasonicDistance(parseInt(e.target.value, 10))}
            className="w-full accent-sky-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
          />
        </div>

        {/* 3. Door & Physical Reed Switch Injector */}
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
          <div className="text-slate-400 font-semibold mb-2 flex items-center justify-between">
            <span>Front Door Switch</span>
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${doorState === 'OPEN' ? 'bg-rose-950 text-rose-300' : 'bg-emerald-950 text-emerald-300'}`}>
              {doorState}
            </span>
          </div>
          <button
            onClick={() => {
              const nextState = doorState === 'OPEN' ? 'CLOSED' : 'OPEN';
              securityStore.setDoorState(nextState);
            }}
            className="w-full py-2 px-3 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium rounded transition-all"
          >
            Toggle Door {doorState === 'OPEN' ? 'CLOSE' : 'OPEN'}
          </button>
        </div>

        {/* 4. Windows Security Zone Simulator */}
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
          <div className="text-slate-400 font-semibold mb-2">Simulate Windows</div>
          <div className="grid grid-cols-2 gap-1 text-[10px]">
            {state.windows.map((w) => (
              <button
                key={w.id}
                onClick={() => securityStore.setWindowOpen(w.id, w.state !== 'OPEN')}
                className={`py-1 px-1.5 rounded text-center truncate transition-all ${
                  w.state === 'OPEN' ? 'bg-amber-600 text-white font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {w.name.split(' ')[0]}: {w.state}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
