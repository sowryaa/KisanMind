import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';
import VoiceModal from './components/VoiceModal';
import RateLimitBanner from './components/RateLimitBanner';
import { useVoice } from './hooks/useVoice';
import { useStream } from './hooks/useStream';
import { useOffline } from './hooks/useOffline';
import { supabase } from './lib/supabase';
import { getWeather, getPrices } from './lib/api';
import { Wifi, X } from 'lucide-react';

// ── Rate limit localStorage keys ─────────────────────────────────────────────
const LS_USED_TODAY   = 'km_used_today';
const LS_DAY_RESET    = 'km_day_reset_at';   // ISO date string (YYYY-MM-DD)

function getTodayUsed() {
  const today = new Date().toISOString().slice(0, 10);
  const saved = localStorage.getItem(LS_DAY_RESET);
  if (saved !== today) {
    localStorage.setItem(LS_DAY_RESET, today);
    localStorage.setItem(LS_USED_TODAY, '0');
    return 0;
  }
  return parseInt(localStorage.getItem(LS_USED_TODAY) || '0', 10);
}

function incrementUsed() {
  const today = new Date().toISOString().slice(0, 10);
  localStorage.setItem(LS_DAY_RESET, today);
  const current = getTodayUsed();
  const next = current + 1;
  localStorage.setItem(LS_USED_TODAY, String(next));
  return next;
}

// ─────────────────────────────────────────────────────────────────────────────

export default function App() {
  const [user, setUser]                             = useState(null);
  const [conversations, setConversations]           = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages]                     = useState([]);
  const [inputValue, setInputValue]                 = useState('');
  const [language, setLanguage]                     = useState('te');
  const [district, setDistrict]                     = useState('Kurnool');
  const [incognito, setIncognito]                   = useState(false);
  const [isVoiceOpen, setIsVoiceOpen]               = useState(false);
  const [activeSpeechIndex, setActiveSpeechIndex]   = useState(null);
  const [voiceMode, setVoiceMode]                   = useState(false);

  // Rate limit state
  const [usedToday, setUsedToday]                   = useState(() => getTodayUsed());
  const [rateLimitInfo, setRateLimitInfo]           = useState(null); // {type, reset_at, ...}

  // Weather / prices overlays
  const [weatherInfo, setWeatherInfo]               = useState(null);
  const [priceInfo, setPriceInfo]                   = useState(null);

  const isOffline = useOffline();
  const { isStreaming, startStream, stopStream } = useStream();

  const { isListening, startListening, stopListening, speak, stopSpeaking, isSpeaking } = useVoice({
    language,
    onTranscript: (transcript) => {
      setInputValue(transcript);
      setIsVoiceOpen(false);
    },
  });

  // Sync isSpeaking → activeSpeechIndex
  useEffect(() => {
    if (!isSpeaking) setActiveSpeechIndex(null);
  }, [isSpeaking]);

  // Load session from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('km_user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);
      loadConversations(parsed.google_id);
    }
  }, []);

  // ── Rate limit: auto-clear when reset_at passes ───────────────────────────
  const rateLimitTimerRef = useRef(null);
  useEffect(() => {
    if (!rateLimitInfo?.reset_at) return;
    const delay = rateLimitInfo.reset_at - Date.now();
    if (delay <= 0) { setRateLimitInfo(null); return; }
    rateLimitTimerRef.current = setTimeout(() => setRateLimitInfo(null), delay + 500);
    return () => clearTimeout(rateLimitTimerRef.current);
  }, [rateLimitInfo]);

  // ── Supabase helpers ─────────────────────────────────────────────────────
  const loadConversations = async (googleId) => {
    if (isOffline) return;
    try {
      const { data: dbUser } = await supabase.from('users').select('id').eq('google_id', googleId).single();
      if (dbUser) {
        const { data: convs } = await supabase
          .from('conversations')
          .select('*')
          .eq('user_id', dbUser.id)
          .eq('is_incognito', false)
          .order('updated_at', { ascending: false });
        if (convs) setConversations(convs);
      }
    } catch (err) { console.error('loadConversations:', err); }
  };

  const loadMessages = async (convId) => {
    if (isOffline || !convId) return;
    try {
      const { data: msgs } = await supabase
        .from('messages').select('*').eq('conversation_id', convId).order('created_at', { ascending: true });
      if (msgs) setMessages(msgs.map(m => ({ role: m.role, content: m.content, sources: m.sources || [] })));
    } catch (err) { console.error('loadMessages:', err); }
  };

  const handleAuthSuccess = async (googleUser) => {
    setUser(googleUser);
    localStorage.setItem('km_user', JSON.stringify(googleUser));
    if (!isOffline) {
      try {
        const { data: existing } = await supabase.from('users').select('*').eq('google_id', googleUser.google_id).single();
        if (!existing) {
          await supabase.from('users').insert({
            google_id: googleUser.google_id, email: googleUser.email,
            name: googleUser.name, avatar_url: googleUser.avatar_url,
            preferred_language: language, district,
          });
        }
        loadConversations(googleUser.google_id);
      } catch (err) { console.error('handleAuthSuccess:', err); }
    }
  };

  const handleLogout = () => {
    setUser(null); setConversations([]); setMessages([]); setCurrentConversationId(null);
    localStorage.removeItem('km_user');
  };

  const saveMessageToDb = async (convId, role, content, sources = []) => {
    if (isOffline || incognito || !user || !convId) return;
    try {
      await supabase.from('messages').insert({ conversation_id: convId, role, content, language, sources });
    } catch (err) { console.error('saveMessage:', err); }
  };

  // ── Image analysis handler ────────────────────────────────────────────────
  const handleImageUpload = async (base64, filename) => {
    const userMsg = { role: "user", content: `📷 పంట ఫోటో విశ్లేషణ కోసం పంపాను: ${filename}` };
    setMessages(prev => [...prev, userMsg]);
    setMessages(prev => [...prev, { role: "assistant", content: "🔍 మీ పంట ఫోటోను విశ్లేషిస్తున్నాను..." }]);
    try {
      const res = await fetch(`https://kisanmind-production.up.railway.app/api/chat/analyze-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: base64, language, user_id: user?.google_id }),
      });
      const data = await res.json();
      setMessages(prev => [...prev.slice(0, -1), { role: "assistant", content: data.analysis || "విశ్లేషణ విఫలమైంది." }]);
    } catch (err) {
      setMessages(prev => [...prev.slice(0, -1), { role: "assistant", content: "చిత్రం విశ్లేషించడంలో సమస్య ఏర్పడింది." }]);
    }
  };

  // ── Main send handler ────────────────────────────────────────────────────
  const handleSendMessage = async (textToSend = inputValue) => {
    const text = textToSend.trim();
    if (!text || rateLimitInfo) return;

    stopSpeaking();

    const updatedMessages = [...messages, { role: 'user', content: text }];
    setMessages(updatedMessages);
    setInputValue('');

    // Supabase conversation create
    let activeConvId = currentConversationId;
    if (!isOffline && !incognito && user && !activeConvId) {
      try {
        const { data: dbUser } = await supabase.from('users').select('id').eq('google_id', user.google_id).single();
        if (dbUser) {
          const { data: newConv } = await supabase.from('conversations')
            .insert({ user_id: dbUser.id, title: text.substring(0, 30) + (text.length > 30 ? '…' : ''), is_incognito: false })
            .select().single();
          if (newConv) {
            activeConvId = newConv.id;
            setCurrentConversationId(activeConvId);
            setConversations(prev => [newConv, ...prev]);
          }
        }
      } catch (err) { console.error('createConversation:', err); }
    }
    if (activeConvId) await saveMessageToDb(activeConvId, 'user', text);

    // Stream
    let aiResponse = '';
    let aiSources  = [];
    const messagesRef = updatedMessages;

    await startStream({
      messages: updatedMessages,
      language,
      userId: user?.google_id || null,
      district,
      incognito,

      onSources: (srcs) => {
        aiSources = srcs;
      },

      onChunk: (chunk) => {
        aiResponse += chunk;
        setMessages([
          ...messagesRef,
          { role: 'assistant', content: aiResponse, sources: aiSources },
        ]);
      },

      onRateLimit: (info) => {
        // Backend said 429 — surface the info
        setRateLimitInfo(info);
        setMessages([
          ...messagesRef,
          {
            role: 'assistant',
            content:
              info.type === 'minute'
                ? '⏱️ Minute limit reached. The chat will auto-re-enable shortly.'
                : '📅 Daily limit reached. Please try again tomorrow or wait for reset.',
            sources: [],
          },
        ]);
      },

      onDone: async () => {
        // Increment local usage counter
        const newCount = incrementUsed();
        setUsedToday(newCount);

        // Save to DB
        if (activeConvId) await saveMessageToDb(activeConvId, 'assistant', aiResponse, aiSources);

        // Voice mode: auto-speak after response
        if (voiceMode && aiResponse) {
          speak(aiResponse, language);
          // After speaking, auto-activate mic
          setTimeout(() => {
            if (voiceMode) {
              setIsVoiceOpen(true);
              startListening();
            }
          }, 500);
        }
      },

      onError: () => {
        setMessages([...messagesRef, { role: 'assistant', content: 'Problem connecting to assistant. Please check your internet.', sources: [] }]);
      },
    });
  };

  // ── Edit message ─────────────────────────────────────────────────────────
  const [editingIndex, setEditingIndex] = useState(null);
  const [editValue, setEditValue]       = useState('');

  const startEditMessage = (idx) => { setEditingIndex(idx); setEditValue(messages[idx].content); };
  const saveEditMessage  = async () => {
    const base = [...messages.slice(0, editingIndex), { ...messages[editingIndex], content: editValue }];
    setMessages(base);
    setEditingIndex(null);
    setEditValue('');
    await handleSendMessage(editValue);
  };

  // ── Retry last AI response ────────────────────────────────────────────────
  const handleRetryLast = async () => {
    // Remove last assistant message and re-send the last user message
    const withoutLastAI = [...messages];
    while (withoutLastAI.length && withoutLastAI[withoutLastAI.length - 1].role === 'assistant') {
      withoutLastAI.pop();
    }
    if (!withoutLastAI.length) return;
    const lastUser = withoutLastAI[withoutLastAI.length - 1].content;
    setMessages(withoutLastAI.slice(0, -1)); // remove user too, re-send will re-add
    await handleSendMessage(lastUser);
  };

  // ── Weather / Prices ─────────────────────────────────────────────────────
  const handleShowWeather = async () => { setWeatherInfo({ loading: true }); setWeatherInfo(await getWeather(district)); };

  const handleUseMyLocation = () => {
    if (!navigator.geolocation) return alert("Geolocation not supported");
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const { latitude, longitude } = pos.coords;
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
      const data = await res.json();
      const place = data.address.village || data.address.town || data.address.city || data.address.county || district;
      setDistrict(place);
    }, () => alert("Location access denied"));
  };
  const handleShowPrices  = async () => { setPriceInfo({ loading: true }); setPriceInfo(await getPrices()); };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen w-screen bg-[#0d0d0d] text-gray-200 overflow-hidden font-sans">

      <Sidebar
        user={user}
        onLogout={handleLogout}
        district={district}
        onChangeDistrict={setDistrict}
        incognito={incognito}
        onToggleIncognito={() => setIncognito(v => !v)}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={(id) => { setCurrentConversationId(id); loadMessages(id); }}
        onNewChat={() => { setCurrentConversationId(null); setMessages([]); }}
        onShowWeather={handleShowWeather}
        onUseMyLocation={handleUseMyLocation}
        onShowPrices={handleShowPrices}
        language={language}
        usedToday={usedToday}
      />

      {/* Main chat viewport */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">

        {/* Rate limit banner (top of chat area) */}
        <RateLimitBanner
          usedToday={usedToday}
          rateLimitInfo={rateLimitInfo}
          onExpired={() => setRateLimitInfo(null)}
        />

        <ChatWindow
          messages={messages}
          language={language}
          onChangeLanguage={setLanguage}
          isOffline={isOffline}
          user={user}
          onAuthSuccess={handleAuthSuccess}
          onAuthError={(err) => alert(err)}
          isStreaming={isStreaming}
          activeSpeechIndex={activeSpeechIndex}
          onSpeakMessage={(text, idx) => { setActiveSpeechIndex(idx); speak(text, language); }}
          onStopSpeakingMessage={() => { setActiveSpeechIndex(null); stopSpeaking(); }}
          onEditMessage={startEditMessage}
          editingMessageIndex={editingIndex}
          editValue={editValue}
          setEditValue={setEditValue}
          onSaveEdit={saveEditMessage}
          onCancelEdit={() => setEditingIndex(null)}
          onSendSuggestion={(text) => handleSendMessage(text)}
          onRetryLast={handleRetryLast}
          voiceMode={voiceMode}
          onToggleVoiceMode={() => setVoiceMode(v => !v)}
        />

        <InputBar
          inputValue={inputValue}
          onChangeInput={setInputValue}
          onSubmit={() => handleSendMessage()}
          isStreaming={isStreaming}
          onStop={stopStream}
          onStartVoice={() => { setIsVoiceOpen(true); startListening(); }}
          onImageUpload={handleImageUpload}
          isRateLimited={!!rateLimitInfo}
          language={language}
        />
      </div>

      <VoiceModal
        isOpen={isVoiceOpen}
        onClose={() => { setIsVoiceOpen(false); stopListening(); }}
        language={language}
        isListening={isListening}
        onStart={startListening}
        onStop={stopListening}
      />

      {/* Weather overlay */}
      {weatherInfo && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-white/10 p-6 rounded-3xl w-full max-w-lg relative animate-fade-in">
            <button onClick={() => setWeatherInfo(null)} className="absolute top-4 right-4 text-gray-400 hover:text-white"><X size={20} /></button>
            <h3 className="text-xl font-bold text-gray-100 mb-4">☀️ Weather: {weatherInfo.district || district}</h3>
            {weatherInfo.loading ? (
              <p className="text-sm text-gray-400">Loading forecast...</p>
            ) : weatherInfo.forecasts ? (
              <div className="flex flex-col gap-3 max-h-[400px] overflow-y-auto pr-1">
                {weatherInfo.forecasts.map((f, i) => (
                  <div key={i} className="flex justify-between items-center bg-zinc-800/40 p-3 rounded-xl border border-white/5 text-sm">
                    <div>
                      <p className="font-semibold text-gray-300">{f.time.split(' ')[1]?.slice(0, 5)} — {f.time.split(' ')[0]}</p>
                      <p className="text-xs text-gray-400 capitalize">{f.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-farmGreen">{f.temp}°C</p>
                      <p className="text-xs text-gray-400">Humid: {f.humidity}% | Rain: {f.rain_mm}mm</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-red-400">Error loading weather.</p>}
          </div>
        </div>
      )}

      {/* Prices overlay */}
      {priceInfo && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-white/10 p-6 rounded-3xl w-full max-w-lg relative animate-fade-in">
            <button onClick={() => setPriceInfo(null)} className="absolute top-4 right-4 text-gray-400 hover:text-white"><X size={20} /></button>
            <h3 className="text-xl font-bold text-gray-100 mb-4">🌾 Mandi Prices (APMC)</h3>
            {priceInfo.loading ? (
              <p className="text-sm text-gray-400">Loading prices...</p>
            ) : priceInfo.records && priceInfo.records.length > 0 ? (
              <div className="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-1">
                <p className="text-xs text-gray-500 mb-1">{priceInfo.source === "live" ? "🟢 Live data" : "🟡 Cached data"} — {priceInfo.district}</p>
                {priceInfo.records.map((r, i) => (
                  <div key={i} className="bg-zinc-800/40 p-3.5 rounded-xl border border-white/5 flex justify-between items-center text-sm">
                    <div>
                      <span className="font-bold text-gray-200">{r.commodity}</span>
                      <p className="text-xs text-gray-400">{r.market} · {r.arrival_date}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-farmGreen">₹{r.modal_price}/q</p>
                      <p className="text-xs text-gray-500">₹{r.min_price}–₹{r.max_price}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-red-400">No price data available for this district.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
