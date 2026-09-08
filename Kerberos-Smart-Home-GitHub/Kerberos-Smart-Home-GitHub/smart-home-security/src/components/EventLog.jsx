import React, { useState } from 'react';
import { History, ShieldAlert, AlertTriangle, Info, CheckCircle2, Zap } from 'lucide-react';

export default function EventLog({ events }) {
  const [filter, setFilter] = useState('ALL');

  const filteredEvents = events.filter((evt) => {
    if (filter === 'ALL') return true;
    return evt.severity === filter;
  });

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-rose-950 text-rose-300 border border-rose-600/50 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-rose-400" /> CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-amber-950 text-amber-300 border border-amber-600/50 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-400" /> WARNING
          </span>
        );
      case 'FAULT':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-purple-950 text-purple-300 border border-purple-600/50 flex items-center gap-1">
            <Zap className="w-3 h-3 text-purple-400" /> FAULT
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-sky-950 text-sky-300 border border-sky-600/50 flex items-center gap-1">
            <Info className="w-3 h-3 text-sky-400" /> INFO
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-4 shadow-xl backdrop-blur-md flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider">Auditable Event Log</h3>
        </div>

        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-700/50 text-[11px]">
          {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-2 py-0.5 rounded font-medium transition-all ${
                filter === type ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Events List Scroll Area */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2 max-h-[300px] scrollbar-thin scrollbar-thumb-slate-700">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">No events recorded in this view.</div>
        ) : (
          filteredEvents.map((evt) => (
            <div
              key={evt.eventId}
              className="bg-slate-900/60 border border-slate-700/40 rounded-lg p-2.5 hover:border-slate-600 transition-all text-xs"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  {getSeverityBadge(evt.severity)}
                  <span className="font-mono text-[11px] text-slate-300 font-semibold">{evt.eventType}</span>
                </div>
                <span className="font-mono text-[10px] text-slate-400">{evt.timestamp}</span>
              </div>
              <p className="text-slate-200 text-xs mt-1">{evt.message}</p>
              <div className="mt-1.5 flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>Source: {evt.source}</span>
                <span>Zone: {evt.zone}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
