import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Volume2, VolumeX, Edit, Check, Copy, RotateCcw, ChevronDown, ChevronUp, ExternalLink, X } from 'lucide-react';

export default function MessageBubble({
  message,
  onSpeak,
  onStopSpeaking,
  isSpeakingThis,
  onEdit,
  isEditing,
  editValue,
  setEditValue,
  onSaveEdit,
  onCancelEdit,
  onRetry,
  isLastAI = false,
}) {
  const isUser = message.role === 'user';
  const sources = message.sources || [];

  const [copied, setCopied]           = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard not available */
    }
  };

  return (
    <div className={`flex flex-col w-full my-2 animate-fade-in group/msg`}>
      <div className={`flex items-start max-w-[85%] gap-2 ${isUser ? 'self-end flex-row-reverse' : 'self-start'}`}>

        {/* Avatar */}
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 select-none ${
          isUser ? 'bg-farmGreen text-white' : 'bg-zinc-800 text-farmGreen border border-white/5'
        }`}>
          {isUser ? 'You' : 'KM'}
        </div>

        {/* Message body */}
        <div className="flex flex-col min-w-0">

          {/* Bubble */}
          <div className={`rounded-2xl px-4 py-3 text-sm shadow-md transition-all duration-300 ${
            isUser
              ? 'bg-[#1e3a2f] border border-green-900/40 text-gray-100 rounded-tr-none'
              : 'bg-zinc-800/40 border border-white/5 text-gray-100 rounded-tl-none backdrop-blur-sm'
          }`}>
            {isUser && isEditing ? (
              <div className="flex flex-col gap-2 min-w-[220px]">
                <textarea
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="bg-zinc-800 text-gray-200 text-sm p-2 rounded-lg border border-white/10 focus:border-farmGreen outline-none resize-none"
                  rows={3}
                  autoFocus
                />
                <div className="flex justify-end gap-2 text-xs">
                  <button onClick={onCancelEdit} className="flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-700 hover:bg-zinc-600 text-gray-300 transition-colors">
                    <X size={11} /> Cancel
                  </button>
                  <button onClick={onSaveEdit} className="flex items-center gap-1 px-2.5 py-1 rounded bg-farmGreen hover:bg-farmGreenDark text-white transition-colors">
                    <Check size={11} /> Save & Resend
                  </button>
                </div>
              </div>
            ) : (
              <div className="prose prose-invert max-w-none text-[14.5px] leading-relaxed">
                {isUser
                  ? <p className="whitespace-pre-wrap m-0">{message.content}</p>
                  : <ReactMarkdown>{message.content}</ReactMarkdown>
                }
              </div>
            )}
          </div>

          {/* Sources panel (collapsible) */}
          {!isUser && sources.length > 0 && (
            <div className="mt-1.5">
              <button
                onClick={() => setSourcesOpen(o => !o)}
                className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-farmGreen transition-colors px-1 py-0.5"
              >
                {sourcesOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                🔍 {sources.length} source{sources.length > 1 ? 's' : ''} used
              </button>
              {sourcesOpen && (
                <div className="mt-1 flex flex-col gap-1.5 pl-1">
                  {sources.map((s, i) => (
                    <a
                      key={i}
                      href={s.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-1.5 text-xs text-blue-400/80 hover:text-blue-300 transition-colors group/link"
                    >
                      <ExternalLink size={10} className="shrink-0 mt-0.5" />
                      <span className="truncate">{s.title || s.link}</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action buttons (visible on hover) */}
          {!isEditing && (
            <div className={`flex items-center gap-1.5 mt-1 px-1 opacity-0 group-hover/msg:opacity-100 transition-opacity duration-150 ${isUser ? 'justify-end' : 'justify-start'}`}>
              {!isUser && (
                <>
                  {/* Listen */}
                  <button
                    onClick={isSpeakingThis ? onStopSpeaking : onSpeak}
                    className={`p-1 rounded hover:bg-white/5 transition-colors ${isSpeakingThis ? 'text-farmGreen' : 'text-gray-500 hover:text-gray-300'}`}
                    title={isSpeakingThis ? 'Stop speaking' : 'Listen'}
                  >
                    {isSpeakingThis ? <VolumeX size={13} /> : <Volume2 size={13} />}
                  </button>

                  {/* Copy */}
                  <button
                    onClick={handleCopy}
                    className={`p-1 rounded hover:bg-white/5 transition-colors ${copied ? 'text-farmGreen' : 'text-gray-500 hover:text-gray-300'}`}
                    title="Copy response"
                  >
                    {copied ? <Check size={13} /> : <Copy size={13} />}
                  </button>

                  {/* Retry (only on last AI message) */}
                  {isLastAI && onRetry && (
                    <button
                      onClick={onRetry}
                      className="p-1 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
                      title="Regenerate response"
                    >
                      <RotateCcw size={13} />
                    </button>
                  )}
                </>
              )}

              {isUser && (
                <button
                  onClick={onEdit}
                  className="p-1 rounded hover:bg-white/5 text-gray-500 hover:text-gray-300 transition-colors"
                  title="Edit message"
                >
                  <Edit size={12} />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
