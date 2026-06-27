const CACHE_NAME = 'kisanmind-v1'
const OFFLINE_RESPONSES = {
  '/api/offline/disease': {
    common_issues: [
      { crop: 'Paddy', disease: 'Blast', symptoms: 'Diamond-shaped spots on leaves', treatment: 'Tricyclazole 75% WP @ 0.6g/L' },
      { crop: 'Cotton', disease: 'Bollworm', symptoms: 'Holes in bolls', treatment: 'Emamectin benzoate 5% SG @ 0.4g/L' },
      { crop: 'Chilli', disease: 'Anthracnose', symptoms: 'Dark sunken spots on fruits', treatment: 'Carbendazim + Mancozeb @ 2g/L' },
      { crop: 'Tomato', disease: 'Early Blight', symptoms: 'Brown spots with yellow halo', treatment: 'Mancozeb 75% WP @ 2g/L' },
    ]
  },
  '/api/offline/schemes': {
    schemes: [
      { name: 'PM-KISAN', amount: '₹6,000/year', contact: 'pmkisan.gov.in' },
      { name: 'Rythu Bharosa', amount: '₹13,500/year', contact: '1902' },
      { name: 'PMFBY', amount: 'Crop Insurance', contact: 'Nearest bank' },
      { name: 'KCC', amount: 'Loan @ 4%', contact: 'Any nationalized bank' },
    ]
  }
}

self.addEventListener('install', e => e.waitUntil(
  caches.open(CACHE_NAME).then(cache => cache.addAll([
    '/', '/index.html', '/manifest.json'
  ]))
))

self.addEventListener('fetch', e => {
  if (!navigator.onLine) {
    const offlineKey = Object.keys(OFFLINE_RESPONSES).find(k => e.request.url.includes(k))
    if (offlineKey) {
      e.respondWith(new Response(JSON.stringify(OFFLINE_RESPONSES[offlineKey]), {
        headers: { 'Content-Type': 'application/json' }
      }))
      return
    }
  }
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)))
})
