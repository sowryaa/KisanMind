import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { X, Save, Tractor } from 'lucide-react';

const SOIL_TYPES = ['Red Soil', 'Black Cotton Soil', 'Alluvial Soil', 'Sandy Soil', 'Loamy Soil', 'Clay Soil'];
const IRRIGATION_TYPES = ['Drip', 'Sprinkler', 'Canal', 'Borewell', 'Rainfed', 'Tank'];
const COMMON_CROPS = ['Rice', 'Wheat', 'Cotton', 'Sugarcane', 'Maize', 'Groundnut', 'Chilli', 'Tomato', 'Onion', 'Turmeric', 'Tobacco', 'Sunflower', 'Soybean', 'Jowar', 'Bajra'];

export default function FarmProfile({ user, onClose, onSave }) {
  const [profile, setProfile] = useState({
    land_size_acres: '',
    soil_type: '',
    irrigation_type: '',
    current_crops: [],
    previous_crops: [],
    village: '',
    mandal: '',
    district: '',
    challenges: '',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!user) return;
    const load = async () => {
      const { data } = await supabase.from('farm_profiles').select('*').eq('google_id', user.google_id).single();
      if (data) setProfile(data);
    };
    load();
  }, [user]);

  const toggleCrop = (crop, field) => {
    setProfile(prev => ({
      ...prev,
      [field]: prev[field].includes(crop)
        ? prev[field].filter(c => c !== crop)
        : [...prev[field], crop]
    }));
  };

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const { data: dbUser } = await supabase.from('users').select('id').eq('google_id', user.google_id).single();
      if (dbUser) {
        await supabase.from('farm_profiles').upsert({
          ...profile,
          user_id: dbUser.id,
          google_id: user.google_id,
          updated_at: new Date().toISOString(),
        }, { onConflict: 'google_id' });
        setSaved(true);
        if (onSave) onSave(profile);
        setTimeout(() => { setSaved(false); onClose(); }, 1500);
      }
    } catch (err) {
      console.error('Save farm profile error:', err);
    }
    setSaving(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-white/10 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Tractor size={20} className="text-green-400" />
            <h2 className="text-lg font-bold text-white">My Farm Profile</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="p-4 flex flex-col gap-4">
          {/* Land Size */}
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Land Size (Acres)</label>
            <input
              type="number"
              value={profile.land_size_acres}
              onChange={e => setProfile(p => ({ ...p, land_size_acres: e.target.value }))}
              placeholder="e.g. 2.5"
              className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none"
            />
          </div>

          {/* Location */}
          <div className="grid grid-cols-3 gap-2">
            {['village', 'mandal', 'district'].map(field => (
              <div key={field}>
                <label className="text-xs text-gray-400 mb-1 block capitalize">{field}</label>
                <input
                  value={profile[field]}
                  onChange={e => setProfile(p => ({ ...p, [field]: e.target.value }))}
                  placeholder={field}
                  className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none"
                />
              </div>
            ))}
          </div>

          {/* Soil Type */}
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Soil Type</label>
            <div className="flex flex-wrap gap-2">
              {SOIL_TYPES.map(s => (
                <button key={s} onClick={() => setProfile(p => ({ ...p, soil_type: s }))}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${profile.soil_type === s ? 'bg-green-500/20 border-green-500/50 text-green-400' : 'bg-zinc-800 border-white/10 text-gray-300'}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Irrigation */}
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Irrigation Type</label>
            <div className="flex flex-wrap gap-2">
              {IRRIGATION_TYPES.map(i => (
                <button key={i} onClick={() => setProfile(p => ({ ...p, irrigation_type: i }))}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${profile.irrigation_type === i ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' : 'bg-zinc-800 border-white/10 text-gray-300'}`}>
                  {i}
                </button>
              ))}
            </div>
          </div>

          {/* Current Crops */}
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Current Crops</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_CROPS.map(c => (
                <button key={c} onClick={() => toggleCrop(c, 'current_crops')}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${profile.current_crops?.includes(c) ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400' : 'bg-zinc-800 border-white/10 text-gray-300'}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Challenges */}
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Main Challenges</label>
            <textarea
              value={profile.challenges}
              onChange={e => setProfile(p => ({ ...p, challenges: e.target.value }))}
              placeholder="e.g. pest problems, water scarcity, low yield..."
              rows={3}
              className="w-full bg-zinc-800 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none resize-none"
            />
          </div>

          {/* Save */}
          <button onClick={handleSave} disabled={saving}
            className="w-full py-3 bg-green-500 hover:bg-green-600 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2">
            <Save size={16} />
            {saved ? '✅ Saved!' : saving ? 'Saving...' : 'Save Farm Profile'}
          </button>
        </div>
      </div>
    </div>
  );
}
