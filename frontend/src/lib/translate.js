// Simple wrapper for Google Translate or dictionary fallback if no key exists.
const dictionary = {
  te: {
    "namaskaram": "నమస్కారం!",
    "ask_question": "వ్యవసాయం గురించి ఏదైనా అడగండి...",
    "weather": "వాతావరణం",
    "mandi_prices": "మార్కెట్ ధరలు",
    "schemes": "ప్రభుత్వ పథకాలు",
    "offline_mode": "ఆఫ్‌లైన్ మోడ్ యాక్టివ్",
    "voice_listening": "వింటున్నాను...",
    "voice_click": "మాట్లాడటానికి క్లిక్ చేయండి",
    "incognito": "రహస్య చాట్",
    "stop": "ఆపు",
    "send": "పంపు",
    "edit": "సవరించు",
    "language": "భాష",
    "logout": "లాగ్ అవుట్",
    "login": "గూగుల్ తో లాగిన్"
  },
  hi: {
    "namaskaram": "नमस्ते!",
    "ask_question": "खेती के बारे में कुछ भी पूछें...",
    "weather": "मौसम",
    "mandi_prices": "मंडी भाव",
    "schemes": "सरकारी योजनाएं",
    "offline_mode": "ऑफलाइन मोड सक्रिय",
    "voice_listening": "सुन रहा हूँ...",
    "voice_click": "बोलने के लिए क्लिक करें",
    "incognito": "गुप्त चैट",
    "stop": "रोकें",
    "send": "भेजें",
    "edit": "बदलें",
    "language": "भाषा",
    "logout": "लॉग आउट",
    "login": "गूगल से लॉगिन"
  },
  en: {
    "namaskaram": "Hello!",
    "ask_question": "Ask anything about farming...",
    "weather": "Weather",
    "mandi_prices": "Mandi Prices",
    "schemes": "Govt Schemes",
    "offline_mode": "Offline Mode Active",
    "voice_listening": "Listening...",
    "voice_click": "Click to speak",
    "incognito": "Incognito Chat",
    "stop": "Stop",
    "send": "Send",
    "edit": "Edit",
    "language": "Language",
    "logout": "Logout",
    "login": "Login with Google"
  }
};

export function translate(key, lang = 'te') {
  const cleanLang = lang === 'te-IN' || lang === 'te' ? 'te' : (lang === 'hi-IN' || lang === 'hi' ? 'hi' : 'en');
  return dictionary[cleanLang]?.[key] || dictionary['en']?.[key] || key;
}
