import React, { useRef, useEffect } from 'react';
import { Send, Mic, Square } from 'lucide-react';
import { translate } from '../lib/translate';

export default function InputBar({
  inputValue,
  onChangeInput,
  onSubmit,
  isStreaming,
  onStop,
  onStartVoice,
  isRateLimited = false,
  language = 'te',
}) {
  const textareaRef = useRef(null);

  // Auto-resize textarea: shrink/grow up to 5 lines
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    const lineHeight = 22;
    const maxHeight  = lineHeight * 5 + 24; // 5 lines + padding
    ta.style.height  = Math.min(ta.scrollHeight, maxHeight) + 'px';
    ta.style.overflowY = ta.scrollHeight > maxHeight ? 'auto' : 'hidden';
  }, [inputValue]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isRateLimited && inputValue.trim()) onSubmit();
    }
  };

  const canSend = !isStreaming && !isRateLimited && !!inputValue.trim();

  return (
    <div className="p-3 sm:p-4 bg-gradient-to-t from-[#0d0d0d] via-[#0d0d0d]/90 to-transparent border-t border-white/5 shrink-0">
      <div className={`max-w-3xl mx-auto flex items-end gap-2 bg-zinc-900/60 p-2 rounded-2xl border transition-all duration-300 backdrop-blur-md ${
        isRateLimited
          ? 'border-amber-500/30 opacity-60 pointer-events-none'
          : 'border-white/5 focus-within:border-farmGreen/30'
      }`}>

        {/* Voice mic button */}
        <button
          type="button"
          onClick={onStartVoice}
          disabled={isRateLimited}
          className="p-2.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-gray-300 hover:text-farmGreen transition-colors flex items-center justify-center cursor-pointer shrink-0 self-end mb-0.5"
          title="Speak to KisanMind"
        >
          <Mic size={17} />
        </button>

        {/* Auto-resizing textarea */}
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => onChangeInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isRateLimited ? 'Rate limit reached — please wait...' : translate('ask_question', language)}
          rows={1}
          disabled={isStreaming || isRateLimited}
          className="flex-1 bg-transparent border-none outline-none py-2 px-1 text-sm text-gray-100 placeholder-gray-500 resize-none leading-[22px]"
          style={{ minHeight: '36px', overflowY: 'hidden' }}
        />

        {/* Stop or Send button */}
        {isStreaming ? (
          <button
            type="button"
            onClick={onStop}
            className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-colors shrink-0 flex items-center justify-center self-end mb-0.5"
            title="Stop generation"
          >
            <Square size={15} fill="currentColor" />
          </button>
        ) : (
          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSend}
            className={`p-2.5 rounded-xl text-white transition-colors shrink-0 flex items-center justify-center self-end mb-0.5 ${
              canSend ? 'bg-farmGreen hover:bg-farmGreenDark cursor-pointer' : 'bg-zinc-700 cursor-not-allowed opacity-40'
            }`}
            title="Send message"
          >
            <Send size={15} />
          </button>
        )}
      </div>
    </div>
  );
}
