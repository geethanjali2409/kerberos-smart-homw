import React, { useRef, useState, useEffect } from 'react';
import { Camera, CameraOff, AlertTriangle, ShieldCheck } from 'lucide-react';
import { securityStore } from '../state/securityStore.js';

export default function CameraManager() {
  const videoRef = useRef(null);
  const [isActive, setIsActive] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [stream, setStream] = useState(null);

  const startCamera = async () => {
    setErrorMsg(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access API is not supported in your browser.');
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 360 }, facingMode: 'user' },
        audio: false
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setIsActive(true);

      securityStore.setState({
        localWebcam: {
          active: true,
          hasPermission: true,
          stream: mediaStream,
          motionDetected: false,
          error: null
        }
      });

      securityStore.addEvent({
        source: 'LOCAL_CAMERA',
        zone: 'CONTROL_CENTER',
        eventType: 'CAMERA_STARTED',
        severity: 'INFO',
        message: 'Local laptop security camera activated'
      });
    } catch (err) {
      console.warn('[CameraManager] Access error:', err);
      const msg = err.name === 'NotAllowedError'
        ? 'Permission denied: Please grant camera access in browser prompt.'
        : err.message || 'Unable to access laptop camera.';
      setErrorMsg(msg);
      setIsActive(false);

      securityStore.setState({
        localWebcam: {
          active: false,
          hasPermission: false,
          stream: null,
          motionDetected: false,
          error: msg
        }
      });

      securityStore.addEvent({
        source: 'LOCAL_CAMERA',
        zone: 'CONTROL_CENTER',
        eventType: 'CAMERA_ERROR',
        severity: 'WARNING',
        message: `Camera access failed: ${msg}`
      });
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);

    securityStore.setState({
      localWebcam: {
        active: false,
        hasPermission: false,
        stream: null,
        motionDetected: false,
        error: null
      }
    });

    securityStore.addEvent({
      source: 'LOCAL_CAMERA',
      zone: 'CONTROL_CENTER',
      eventType: 'CAMERA_STOPPED',
      severity: 'INFO',
      message: 'Local laptop security camera stopped'
    });
  };

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  return (
    <div className="bg-slate-800/90 border border-slate-700/80 rounded-xl p-4 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Camera className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider">Laptop CCTV Feed</h3>
        </div>

        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
          <span className="text-xs font-mono text-slate-300">
            {isActive ? 'LIVE MONITORING' : 'CAMERA OFF'}
          </span>
        </div>
      </div>

      {/* Video Stream Container */}
      <div className="relative w-full h-44 bg-slate-950 rounded-lg overflow-hidden border border-slate-700/50 flex items-center justify-center">
        {isActive ? (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            {/* Security Overlay HUD */}
            <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 flex items-center gap-1 border border-emerald-500/30">
              <ShieldCheck className="w-3 h-3 text-emerald-400" /> REC • LOCAL ONLY
            </div>
            <div className="absolute bottom-2 right-2 text-[10px] font-mono text-slate-400 bg-black/60 px-2 py-0.5 rounded">
              {new Date().toLocaleTimeString()}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center p-4 text-center">
            <CameraOff className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-xs text-slate-400 max-w-[200px]">
              {errorMsg ? (
                <span className="text-rose-400 flex items-center gap-1 justify-center">
                  <AlertTriangle className="w-3 h-3" /> {errorMsg}
                </span>
              ) : (
                'Camera is currently disabled. Click below to grant local preview permission.'
              )}
            </p>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="mt-3 flex items-center justify-between">
        <span className="text-[11px] text-slate-400">
          Privacy Protection: Video feed is never sent to cloud.
        </span>

        {isActive ? (
          <button
            onClick={stopCamera}
            className="px-3 py-1.5 bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-rose-950/40"
          >
            <CameraOff className="w-3.5 h-3.5" /> Stop Camera
          </button>
        ) : (
          <button
            onClick={startCamera}
            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 shadow-lg shadow-indigo-950/40"
          >
            <Camera className="w-3.5 h-3.5" /> Start Camera
          </button>
        )}
      </div>
    </div>
  );
}
