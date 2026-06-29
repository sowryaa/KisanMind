import React, { useState, useRef, useEffect } from 'react';
import { MapPin,
  User, LogOut, CloudSun, IndianRupee, ShieldAlert, Sparkles, FlaskConical,
  MessageSquare, BarChart2, Menu, X, Search, FileText,
} from 'lucide-react';
import { translate } from '../lib/translate';

const LIMIT_DAY = 1400;

const ALL_DISTRICTS = [
  'Anantapur','Alluri Sitharama Raju','Anakapalli','Bapatla','Chittoor',
  'East Godavari','Eluru','Guntur','Kadapa','Konaseema','Krishna','Kurnool',
  'Manyam','Nandyal','Nellore','NTR','Palnadu','Prakasam','Srikakulam',
  'Sri Balaji','Sri Potti Sriramulu Nellore','Sri Sathya Sai','Tirupati',
  'Visakhapatnam','Vizianagaram','West Godavari',
];

function DistrictSelector({ district, onChangeDistrict }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = ALL_DISTRICTS.filter(d => d.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full bg-zinc-900/80 border border-white/5 text-sm p-2.5 rounded-xl outline-none text-gray-200 cursor-pointer flex items-center justify-between"
      >
        <span>{district}</span>
        <span className="text-gray-500 text-xs">▼</span>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-zinc-900 border border-white/10 rounded-xl shadow-xl overflow-hidden">
          <div className="p-2 border-b border-white/5 flex items-center gap-2">
            <Search size={13} className="text-gray-400" />
            <input
              autoFocus
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search district..."
              className="bg-transparent text-sm text-gray-200 outline-none w-full placeholder-gray-500"
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filtered.length === 0 ? (
              <p className="text-xs text-gray-500 p-3">No districts found</p>
            ) : filtered.map(d => (
              <button
                key={d}
                onClick={() => { onChangeDistrict(d); setOpen(false); setSearch(''); }}
                className={`w-full text-left text-sm px-3 py-2 transition-colors ${
                  d === district ? 'bg-green-500/10 text-green-400' : 'text-gray-300 hover:bg-zinc-800'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Sidebar({
  user,
  onLogout,
  district,
  onChangeDistrict,
  incognito,
  onToggleIncognito,
  conversations = [],
  currentConversationId,
  onSelectConversation,
  onNewChat,
  onShowWeather,
  onShowPrices,
  onShowSchemes,
  onShowSoilAnalysis,
  onShowFarmProfile,
  onUseMyLocation,
  language = 'te',
  usedToday = 0,
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const usagePercent = Math.min((usedToday / LIMIT_DAY) * 100, 100);

  const SidebarContent = () => (
    <aside className="w-72 h-full bg-[#121212]/98 border-r border-white/5 flex flex-col justify-between glass">
      <div className="p-4 flex flex-col gap-3.5 overflow-y-auto flex-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌾</span>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-green-400 to-emerald-500 tracking-wide">
              KisanMind
            </h1>
          </div>
          <div className="flex items-center gap-1.5">
            <button onClick={onNewChat} className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-gray-200 transition-colors" title="New Chat">
              <Sparkles size={15} />
            </button>
            <button onClick={() => setMobileOpen(false)} className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-gray-200 transition-colors md:hidden">
              <X size={15} />
            </button>
          </div>
        </div>

        <div className="bg-zinc-900/60 rounded-xl p-3 border border-white/5">
          <div className="flex items-center justify-between mb-1.5 text-xs">
            <div className="flex items-center gap-1.5 text-gray-400">
              <BarChart2 size={12} />
              <span>Today's usage</span>
            </div>
            <span className={`font-mono font-semibold ${usagePercent >= 90 ? 'text-amber-400' : 'text-gray-300'}`}>
              {usedToday} / {LIMIT_DAY}
            </span>
          </div>
          <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                usagePercent >= 90 ? 'bg-amber-500' : usagePercent >= 70 ? 'bg-amber-400/70' : 'bg-farmGreen'
              }`}
              style={{ width: `${usagePercent}%` }}
            />
          </div>
          <p className="text-[10px] text-gray-500 mt-1">{LIMIT_DAY - usedToday} requests remaining</p>
        </div>

        <button
          onClick={onToggleIncognito}
          className={`flex items-center justify-between p-3 rounded-xl border text-sm font-semibold transition-all duration-300 ${
            incognito ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-zinc-900 border-white/5 text-gray-300 hover:bg-zinc-850'
          }`}
        >
          <div className="flex items-center gap-2">
            <ShieldAlert size={15} />
            <span>{translate('incognito', language)}</span>
          </div>
          <div className={`w-8 h-4 rounded-full p-0.5 transition-colors ${incognito ? 'bg-red-500' : 'bg-zinc-700'}`}>
            <div className={`w-3 h-3 rounded-full bg-white transition-transform ${incognito ? 'translate-x-4' : 'translate-x-0'}`} />
          </div>
        </button>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400 ml-1">District</label>
          <DistrictSelector district={district} onChangeDistrict={onChangeDistrict} />
          <button onClick={onUseMyLocation} className="mt-1 w-full flex items-center justify-center gap-1.5 text-xs text-green-400 hover:text-green-300 py-1.5 px-3 rounded-lg bg-green-500/10 hover:bg-green-500/20 transition-colors">
            <MapPin size={12} /> Use my exact location
          </button>
        </div>

        <div className="flex flex-col gap-2">
          <button onClick={onShowWeather} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900/50 hover:bg-zinc-900 border border-white/5 text-gray-300 hover:text-white transition-all">
            <CloudSun size={17} className="text-yellow-500" />
            <span className="text-sm">{translate('weather', language)}</span>
          </button>
          <button onClick={onShowFarmProfile} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900/50 hover:bg-zinc-900 border border-white/5 text-gray-300 hover:text-white transition-all">
            <MapPin size={17} className="text-green-400" />
            <span className="text-sm">My Farm Profile</span>
          </button>
          <button onClick={onShowSoilAnalysis} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900/50 hover:bg-zinc-900 border border-white/5 text-gray-300 hover:text-white transition-all">
            <FlaskConical size={17} className="text-orange-400" />
            <span className="text-sm">Soil Analysis</span>
          </button>
          <button onClick={onShowPrices} className="flex items-center gap-3 p-3 rounded-xl bg-zinc-900/50 hover:bg-zinc-900 border border-white/5 text-gray-300 hover:text-white transition-all">
            <IndianRupee size={17} className="text-green-500" />
            <span className="text-sm">{translate('mandi_prices', language)}</span>
          </button>
        </div>

        <div>
          <p className="text-[10px] font-semibold text-gray-500 mb-2 px-1 tracking-widest uppercase">Recent Chats</p>
          <div className="flex flex-col gap-1 max-h-52 overflow-y-auto">
            {conversations.length === 0 ? (
              <p className="text-xs text-gray-600 px-1">No saved chats yet.</p>
            ) : (
              conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { onSelectConversation(c.id); setMobileOpen(false); }}
                  className={`flex items-center gap-2.5 p-2.5 rounded-xl text-left text-sm transition-all ${
                    c.id === currentConversationId
                      ? 'bg-farmGreen/10 border border-farmGreen/20 text-farmGreen'
                      : 'text-gray-400 hover:bg-zinc-900 hover:text-gray-200'
                  }`}
                >
                  <MessageSquare size={13} />
                  <span className="truncate">{c.title || 'Farming Inquiry'}</span>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-white/5 bg-zinc-900/20">
        {user ? (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
              {user.avatar_url
                ? <img src={user.avatar_url} alt="Profile" className="w-8 h-8 rounded-full" />
                : <div className="w-8 h-8 rounded-full bg-farmGreen/25 flex items-center justify-center text-farmGreen"><User size={16} /></div>
              }
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{user.name || 'Farmer'}</p>
                <p className="text-xs text-gray-400 truncate">{user.email}</p>
              </div>
            </div>
            <button onClick={onLogout} className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors" title="Logout">
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <p className="text-xs text-gray-400 text-center">Login to sync chat history.</p>
        )}
      </div>
    </aside>
  );

  return (
    <>
      <div className="hidden md:flex h-full">
        <SidebarContent />
      </div>
      <button onClick={() => setMobileOpen(true)} className="md:hidden fixed top-3 left-3 z-50 p-2 rounded-xl bg-zinc-900 border border-white/10 text-gray-300 shadow-lg">
        <Menu size={18} />
      </button>
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="flex h-full">
            <SidebarContent />
          </div>
          <div className="flex-1 bg-black/50 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
        </div>
      )}
    </>
  );
}
