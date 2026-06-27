import { useState, useRef } from 'react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function useStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef(null);

  /**
   * startStream — SSE streaming with sources + rate-limit support
   *
   * Callbacks:
   *   onChunk(text)              — called for each text chunk
   *   onSources(sources[])      — called once when sources arrive
   *   onRateLimit(info)         — called if 429 response received
   *   onDone()                  — called when stream completes
   *   onError(err)              — called on network/other errors
   */
  const startStream = async ({
    messages,
    language,
    userId,
    district,
    incognito = false,
    onChunk,
    onSources,
    onRateLimit,
    onDone,
    onError,
  }) => {
    setIsStreaming(true);
    abortControllerRef.current = new AbortController();

    try {
      const endpoint = incognito ? '/api/chat/incognito' : '/api/chat/stream';
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, language, user_id: userId, district }),
        signal: abortControllerRef.current.signal,
      });

      // ── Rate limit response (JSON 429) ──────────────────────────────────
      if (response.status === 429) {
        const info = await response.json();
        if (onRateLimit) onRateLimit(info);
        setIsStreaming(false);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // ── SSE stream ───────────────────────────────────────────────────────
      const reader  = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer    = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep last partial line

        for (const line of lines) {
          const clean = line.trim();
          if (!clean || !clean.startsWith('data: ')) continue;

          const dataStr = clean.slice(6).trim();
          if (dataStr === '[DONE]') {
            if (onDone) onDone();
            break;
          }

          try {
            const parsed = JSON.parse(dataStr);

            if (parsed.sources && onSources) {
              onSources(parsed.sources);
            } else if (parsed.text && onChunk) {
              onChunk(parsed.text);
            }
          } catch (e) {
            console.error('SSE parse error:', clean, e);
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted by user');
      } else {
        console.error('Streaming error:', error);
        if (onError) onError(error);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const stopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  return { isStreaming, startStream, stopStream };
}
