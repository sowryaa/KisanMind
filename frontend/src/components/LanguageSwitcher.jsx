import React from 'react';
import { Languages } from 'lucide-react';

const languages = [
  { code: 'te', name: 'తెలుగు (Telugu)' },
  { code: 'hi', name: 'हिन्दी (Hindi)' },
  { code: 'en', name: 'English' }
];

export default function LanguageSwitcher({ currentLanguage, onChangeLanguage }) {
  return (
    <div className="flex items-center gap-2 bg-zinc-900/80 p-1.5 rounded-xl border border-white/5">
      <Languages size={16} className="text-farmGreen ml-1.5" />
      <select
        value={currentLanguage}
        onChange={(e) => onChangeLanguage(e.target.value)}
        className="bg-transparent text-sm font-medium text-gray-200 outline-none cursor-pointer pr-2 py-0.5"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-[#1a1a1a] text-gray-200">
            {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
}
