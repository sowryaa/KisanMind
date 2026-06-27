import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import LanguageSwitcher from './LanguageSwitcher';
import GoogleAuthButton from './GoogleAuthButton';
import { WifiOff, Sprout, ArrowRight, Mic, MicOff } from 'lucide-react';
import { translate } from '../lib/translate';

export default function ChatWindow({
  messages = [],
  language = 'te',
  onChangeLanguage,
  isOffline,
  user,
  onAuthSuccess,
  onAuthError,
  isStreaming,
  activeSpeechIndex,
  onSpeakMessage,
  onStopSpeakingMessage,
  onEditMessage,
  editingMessageIndex,
  editValue,
  setEditValue,
  onSaveEdit,
  onCancelEdit,
  onSendSuggestion,
  onRetryLast,
  voiceMode,
  onToggleVoiceMode,
}) {
  const scrollRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const lastAIIndex = messages.reduceRight(
    (found, m, i) => (found === -1 && m.role === 'assistant' ? i : found),
    -1
  );

  const suggestions = {
    te: [
      { text: "నా వరి పంటలో ఆకులు పసుపు రంగులోకి మారుతున్నాయి, ఏం చేయాలి?", label: "వరి ఆకులు పసుపు పడటం" },
      { text: "వైఎస్సార్ రైతు భరోసా పథకానికి ఎలా దరఖాస్తు చేసుకోవాలి?", label: "రైతు భరోసా దరఖాస్తు" },
      { text: "గుంటూరు మార్కెట్‌లో మిర్చి ప్రస్తుత ధర ఎంత?", label: "మిర్చి మార్కెట్ ధర" },
      { text: "టమోటా పంటకు డ్రిప్ ఇరిగేషన్ పద్ధతి ఎలా ఉండాలి?", label: "టమోటా డ్రిప్ ఇరిగేషన్" },
    ],
    hi: [
      { text: "धान की पत्तियां पीली हो रही हैं, क्या उपाय करें?", label: "धान के पत्ते पीले होना" },
      { text: "पीएम किसान सम्मान निधि योजना के लिए कैसे आवेदन करें?", label: "पीएम किसान आवेदन" },
      { text: "गुंटूर मंडी में कपास और मिर्च का ताजा भाव क्या है?", label: "मंडी के भाव" },
      { text: "टमाटर की फसल में सिंचाई की कौन सी विधि सबसे अच्छी है?", label: "सिंचाई सलाह" },
    ],
    en: [
      { text: "Paddy leaves are turning yellow, what should I do?", label: "Paddy Yellow Leaves" },
      { text: "How do I apply for the PM-KISAN scheme?", label: "PM-KISAN Application" },
      { text: "What is the current Chilli price in Guntur Mandi?", label: "Chilli Market Price" },
      { text: "What is the best irrigation stage for cotton crop?", label: "Cotton Irrigation" },
    ],
  };

  const currentSuggestions = suggestions[language] || suggestions.en;

  return (
    <div className="flex-1 flex flex-col h-full bg-gradient-to-b from-[#0d0d0d] via-[#101010] to-[#0a0a0a] relative overflow-hidden">

      {/* Header */}
      <header className="h-14 border-b border-white/5 px-4 flex items-center justify-between glass z-10 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-farmGreen animate-pulse" />
          <span className="text-sm font-semibold text-gray-200 hidden sm:block">KisanMind Assistant</span>
          <span className="text-sm font-semibold text-gray-200 sm:hidden">KisanMind</span>
          {isOffline && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs border border-red-500/20">
              <WifiOff size={11} />
              <span>{translate('offline_mode', language)}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Voice mode toggle */}
          <button
            onClick={onToggleVoiceMode}
            title={voiceMode ? 'Disable hands-free voice mode' : 'Enable hands-free voice mode'}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1.5 transition-all ${
              voiceMode
                ? 'bg-farmGreen/15 border-farmGreen/30 text-farmGreen'
                : 'bg-zinc-800/60 border-white/5 text-gray-400 hover:text-gray-200'
            }`}
          >
            {voiceMode ? <Mic size={13} /> : <MicOff size={13} />}
            <span className="hidden sm:block">{voiceMode ? 'Voice ON' : 'Voice'}</span>
          </button>

          <LanguageSwitcher currentLanguage={language} onChangeLanguage={onChangeLanguage} />

          {!user && (
            <div className="w-36 scale-90 hidden sm:block">
              <GoogleAuthButton onAuthSuccess={onAuthSuccess} onAuthError={onAuthError} />
            </div>
          )}
        </div>
      </header>

      {/* Messages / Onboarding */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto text-center py-8">
            <div className="w-16 h-16 rounded-2xl bg-farmGreen/10 flex items-center justify-center text-farmGreen mb-6 border border-farmGreen/20 shadow-xl shadow-green-500/5">
              <Sprout size={32} />
            </div>
            <h2 className="text-2xl font-bold text-gray-100 mb-2">
              {translate('namaskaram', language)}
            </h2>
            <p className="text-sm text-gray-400 max-w-md mb-8">
              Your expert farming advisor. Ask about pests, fertilizers, schemes, weather, or mandi prices.
            </p>

            {/* Quick suggestion chips */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full text-left">
              {currentSuggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendSuggestion(s.text)}
                  className="p-4 rounded-2xl bg-zinc-900/40 border border-white/5 hover:border-farmGreen/20 hover:bg-zinc-900/80 transition-all duration-300 text-left group flex items-start justify-between gap-3 cursor-pointer"
                >
                  <div>
                    <p className="text-xs text-farmGreen font-semibold uppercase tracking-wider mb-1">{s.label}</p>
                    <p className="text-sm text-gray-300 group-hover:text-white transition-colors">{s.text}</p>
                  </div>
                  <ArrowRight size={16} className="text-gray-500 group-hover:text-farmGreen group-hover:translate-x-1 transition-all mt-1 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl w-full mx-auto flex-1 flex flex-col">
            {messages.map((m, idx) => (
              <MessageBubble
                key={idx}
                message={m}
                onSpeak={() => onSpeakMessage(m.content, idx)}
                onStopSpeaking={onStopSpeakingMessage}
                isSpeakingThis={activeSpeechIndex === idx}
                onEdit={() => onEditMessage(idx)}
                isEditing={editingMessageIndex === idx}
                editValue={editValue}
                setEditValue={setEditValue}
                onSaveEdit={onSaveEdit}
                onCancelEdit={onCancelEdit}
                onRetry={onRetryLast}
                isLastAI={idx === lastAIIndex}
              />
            ))}

            {/* Streaming typing indicator */}
            {isStreaming && (
              <div className="flex items-start gap-2 my-2 self-start max-w-[80%]">
                <div className="w-8 h-8 rounded-lg bg-zinc-800 border border-white/5 flex items-center justify-center font-bold text-xs text-farmGreen shrink-0 animate-pulse">
                  KM
                </div>
                <div className="rounded-2xl px-4 py-3 text-sm bg-zinc-800/40 border border-white/5 rounded-tl-none flex items-center gap-1.5 backdrop-blur-sm">
                  <div className="w-1.5 h-1.5 rounded-full bg-farmGreen animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-farmGreen animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 rounded-full bg-farmGreen animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        )}
      </div>
    </div>
  );
}
