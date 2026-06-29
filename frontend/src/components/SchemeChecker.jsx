import React, { useState } from 'react';
import { X, CheckCircle, Phone, FileText, ChevronDown, ChevronUp } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const categoryColors = {
  income_support: 'bg-green-500/10 text-green-400 border-green-500/20',
  insurance: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  credit: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  subsidy: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  marketing: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

export default function SchemeChecker({ onClose }) {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ farmer_type: 'owner', land_acres: '', caste: 'general', age: '' });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState({});

  const handleCheck = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        farmer_type: form.farmer_type,
        land_acres: form.land_acres || 2,
        caste: form.caste,
        age: form.age || 30,
        state: 'Andhra Pradesh'
      });
      const res = await fetch(`${BACKEND_URL}/api/schemes/check?${params}`);
      const data = await res.json();
      setResults(data);
      setStep(2);
    } catch (e) {
      alert('Failed to check schemes. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-white/10 rounded-3xl w-full max-w-lg relative animate-fade-in max-h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-100">🏛️ Scheme Eligibility Checker</h3>
            <p className="text-xs text-gray-400 mt-0.5">Find AP & Central govt schemes you qualify for</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-6">
          {step === 1 ? (
            <div className="flex flex-col gap-4">
              <p className="text-sm text-gray-300">Answer 4 quick questions to see which schemes you qualify for:</p>

              {/* Farmer Type */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-gray-400 font-medium">Are you a land owner or tenant farmer?</label>
                <div className="grid grid-cols-2 gap-2">
                  {['owner', 'tenant'].map(t => (
                    <button key={t} onClick={() => setForm({...form, farmer_type: t})}
                      className={`p-3 rounded-xl border text-sm font-medium transition-all capitalize ${
                        form.farmer_type === t ? 'bg-green-500/10 border-green-500/40 text-green-400' : 'bg-zinc-800 border-white/5 text-gray-300'
                      }`}>
                      {t === 'owner' ? '🏡 Land Owner' : '🤝 Tenant Farmer'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Land */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-gray-400 font-medium">How many acres of land do you farm?</label>
                <input
                  type="number"
                  placeholder="e.g. 2.5"
                  value={form.land_acres}
                  onChange={e => setForm({...form, land_acres: e.target.value})}
                  className="bg-zinc-800 border border-white/5 rounded-xl p-3 text-sm text-gray-200 outline-none focus:border-green-500/40"
                />
              </div>

              {/* Caste */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-gray-400 font-medium">Community category</label>
                <div className="grid grid-cols-2 gap-2">
                  {[['general', 'General'], ['bc', 'BC'], ['sc', 'SC'], ['st', 'ST']].map(([val, label]) => (
                    <button key={val} onClick={() => setForm({...form, caste: val})}
                      className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                        form.caste === val ? 'bg-green-500/10 border-green-500/40 text-green-400' : 'bg-zinc-800 border-white/5 text-gray-300'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Age */}
              <div className="flex flex-col gap-2">
                <label className="text-xs text-gray-400 font-medium">Your age</label>
                <input
                  type="number"
                  placeholder="e.g. 35"
                  value={form.age}
                  onChange={e => setForm({...form, age: e.target.value})}
                  className="bg-zinc-800 border border-white/5 rounded-xl p-3 text-sm text-gray-200 outline-none focus:border-green-500/40"
                />
              </div>

              <button
                onClick={handleCheck}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-500 text-white font-semibold py-3 rounded-xl transition-all mt-2"
              >
                {loading ? 'Checking...' : '🔍 Check My Eligibility'}
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-green-400">{results.eligible_count}</p>
                <p className="text-sm text-gray-300">schemes you qualify for!</p>
              </div>

              {results.schemes.map(scheme => (
                <div key={scheme.id} className="bg-zinc-800/50 border border-white/5 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setExpanded({...expanded, [scheme.id]: !expanded[scheme.id]})}
                    className="w-full p-4 flex items-center justify-between text-left"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <CheckCircle size={14} className="text-green-400" />
                        <span className="font-semibold text-gray-200 text-sm">{scheme.name}</span>
                      </div>
                      <p className="text-xs text-gray-400">{scheme.description}</p>
                    </div>
                    {expanded[scheme.id] ? <ChevronUp size={16} className="text-gray-400 ml-2" /> : <ChevronDown size={16} className="text-gray-400 ml-2" />}
                  </button>

                  {expanded[scheme.id] && (
                    <div className="px-4 pb-4 flex flex-col gap-2 border-t border-white/5 pt-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${categoryColors[scheme.category] || 'bg-zinc-700 text-gray-300'}`}>
                          {scheme.category.replace('_', ' ')}
                        </span>
                        <span className="text-xs font-semibold text-green-400">{scheme.amount}</span>
                      </div>
                      <div className="flex items-start gap-2 text-xs text-gray-400">
                        <FileText size={12} className="mt-0.5 shrink-0" />
                        <span>{scheme.how_to_apply}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-blue-400">
                        <Phone size={12} />
                        <span>Helpline: {scheme.helpline}</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              <button onClick={() => { setStep(1); setResults(null); }}
                className="text-sm text-gray-400 hover:text-gray-200 text-center mt-2">
                ← Check again with different details
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
