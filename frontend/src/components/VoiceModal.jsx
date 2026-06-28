import React, { useEffect } from 'react';
import { Mic, MicOff, X } from 'lucide-react';
import { translate } from '../lib/translate';

export default function VoiceModal({ isOpen, onClose, language = 'te', isListening, onStart, onStop }) {
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => onStart?.(), 300);
      return () => { clearTimeout(timer); };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative glass border border-white/10 p-8 rounded-3xl w-80 max-w-full flex flex-col items-center shadow-2xl glow-green">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors">
          <X size={20} />
        </button>

        <h3 className="text-xl font-semibold text-gray-200 mt-2 mb-6">
          {isListening ? translate('voice_listening', language) : 'Tap mic to speak'}
        </h3>

        <div className="relative flex items-center justify-center w-28 h-28">
          {isListening && (
            <>
              <div className="absolute inset-0 rounded-full bg-farmGreen/20 animate-ping duration-1000"></div>
              <div className="absolute -inset-2 rounded-full bg-farmGreen/10 animate-pulse"></div>
            </>
          )}
          <button
            onClick={isListening ? onStop : onStart}
            className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-all ${
              isListening ? 'bg-red-500 shadow-red-500/50' : 'bg-farmGreen shadow-green-500/50'
            }`}
          >
            {isListening ? <MicOff size={36} className="text-white" /> : <Mic size={36} className="text-white" />}
          </button>
        </div>

        <p className="text-sm text-gray-400 mt-8 text-center">
          {isListening ? 'Listening... tap to stop' : translate('voice_click', language)}
        </p>
      </div>
    </div>
  );
}
