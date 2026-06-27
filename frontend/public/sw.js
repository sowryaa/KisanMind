/**
 * KisanMind Service Worker
 * Provides offline fallback responses for common farming queries.
 * Cache-first for assets; network-first for API calls.
 */

const CACHE_NAME = 'kisanmind-v1';

// ── Static assets to pre-cache ───────────────────────────────────────────────
const PRECACHE_URLS = ['/', '/index.html', '/manifest.json'];

// ── Offline farming knowledge cache ─────────────────────────────────────────
const OFFLINE_RESPONSES = {
  crop_disease: `
🌾 Common Crop Disease Quick Reference (AP/Telangana)

PADDY:
• Blast — Brown/grey lesions on leaves. Use: Tricyclazole 75WP @ 0.6g/L water. Act within 3 days.
• Brown Plant Hopper — Yellow patches, "hopper burn". Use: Imidacloprid 17.8SL @ 0.5ml/L. Act within 3 days.
• Sheath Blight — White/brown lesions at water line. Use: Hexaconazole 5EC @ 2ml/L. Act within 5 days.

COTTON:
• Bollworm — Holes in bolls. Use: Chlorpyrifos 20EC @ 2.5ml/L + Cypermethrin 10EC @ 1ml/L.
• Whitefly — Sticky leaves, sooty mould. Use: Thiamethoxam 25WG @ 0.3g/L. Act within 5 days.
• Root Rot — Wilting, black roots. Use: Copper oxychloride 50WP @ 3g/L soil drench.

CHILLI:
• Leaf Curl Virus — Curled, deformed leaves. No chemical cure. Remove infected plants. Use sticky yellow traps.
• Anthracnose — Dark, sunken spots on fruits. Use: Mancozeb 75WP @ 2.5g/L. Act within 5 days.

TOMATO:
• Early Blight — Brown spots with yellow rings. Use: Chlorothalonil 75WP @ 2g/L.
• Late Blight — Water-soaked dark lesions. Use: Metalaxyl 8% + Mancozeb 64% WP @ 2.5g/L.

⚠️ SAFETY: Always wear gloves and mask while spraying. Never spray in rain or strong wind.
📞 For precise advice: Call 1902 (free, 24/7, Telugu/Hindi)
`,
  schemes: `
📋 Government Farming Schemes — AP & Telangana

1. PM-KISAN (Central)
   • Amount: ₹6,000/year (3 installments of ₹2,000)
   • Who: All landowner farmers
   • Apply: pmkisan.gov.in or nearest RBK/Agriculture dept
   • Helpline: 011-24300606

2. YSR Rythu Bharosa (Andhra Pradesh)
   • Amount: ₹13,500/year (tenant + landowner farmers)
   • Includes: ₹7,500 from state + ₹6,000 PM-KISAN
   • Apply: Nearest RBK office (Rythu Bharosa Kendra)

3. Rythu Bandhu (Telangana)
   • Amount: ₹10,000/year per acre (₹5,000 per season)
   • Who: Landowner farmers
   • Apply: Nearest agriculture office

4. PMFBY Crop Insurance
   • Premium: 2% for Kharif, 1.5% for Rabi
   • Covers: drought, flood, pest, unseasonal rain
   • Apply: Through your bank or at insurance company

5. Kisan Credit Card (KCC)
   • Loan up to: ₹3 lakh at 4% interest (with subsidy)
   • Apply: At nearest bank branch

6. Drip/Sprinkler Irrigation Subsidy
   • Subsidy: Up to 90% for small/marginal farmers
   • Apply: Nearest horticulture department

📞 AP Agriculture Helpline: 1902 (24/7, free)
📞 Telangana Agriculture: 1800-425-1110 (free)
`,
  fertilizer: `
🌱 Fertilizer Schedule Quick Reference

PADDY (per acre):
• Basal (at transplanting): DAP 50 kg + MOP 25 kg
• 21 days after transplant: Urea 25 kg
• 45 days: Urea 25 kg
• Top dress if yellowing: Urea 12.5 kg
• Zinc deficiency (patches): Zinc Sulphate 10 kg/acre

COTTON (per acre):
• Basal: DAP 50 kg + MOP 50 kg + Urea 15 kg
• 30 days: Urea 50 kg + Potash 25 kg
• 60 days: Urea 25 kg + Sulfur 10 kg
• Micronutrient spray: 19:19:19 NPK @ 3g/L water

CHILLI (per acre):
• Land prep: FYM 5 tonnes + SSP 100 kg
• Basal: DAP 50 kg + MOP 30 kg
• 30 days: Urea 25 kg
• 60 days: Urea 25 kg + 13:00:45 NPK (fertigation) @ 3g/L

GROUNDNUT (per acre):
• Basal: SSP 100 kg + Gypsum 100 kg + Urea 10 kg
• 30 days: Calcium Ammonium Nitrate 25 kg
• Pod development: Gypsum top dress 50 kg

⚠️ Soil test first at your local agricultural lab (₹150–300) for precise recommendations.
📞 Soil testing centers: Contact RBK or District Agriculture Officer
`,
};

// ── Install event ─────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch(() => {
        // Non-fatal: PWA still works even if pre-cache fails
      });
    })
  );
  self.skipWaiting();
});

// ── Activate event ────────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch event: network-first with offline fallback ──────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET and API calls — always network for those
  if (event.request.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful responses for static assets
        if (response.ok && !url.pathname.startsWith('/api/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Return cached version if offline
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;

          // For navigation requests, return index.html
          if (event.request.mode === 'navigate') {
            return caches.match('/index.html');
          }

          return new Response('Offline', { status: 503 });
        });
      })
  );
});

// ── Message handler: offline knowledge base ───────────────────────────────────
self.addEventListener('message', (event) => {
  if (event.data?.type === 'GET_OFFLINE_RESPONSE') {
    const { category } = event.data;
    const content = OFFLINE_RESPONSES[category] || OFFLINE_RESPONSES.crop_disease;
    event.ports[0].postMessage({ content });
  }
});
