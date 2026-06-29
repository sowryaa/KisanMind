from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

SCHEMES = [
    {
        "id": "annadata_sukhibhava",
        "name": "Annadata Sukhibhava (అన్నదాత సుఖీభవ)",
        "description": "₹20,000/year per farmer family — ₹13,500 from AP govt + ₹6,000 from PM-KISAN. Renamed from YSR Rythu Bharosa by TDP government in 2024.",
        "eligibility": {
            "farmer_type": ["owner"],
            "caste": ["all"],
            "min_age": 18,
            "state": "Andhra Pradesh",
            "notes": "Must have valid pattadar passbook. Not eligible if income taxpayer or govt employee. eKYC required at nearest Raithu Seva Kendra."
        },
        "amount": "₹20,000/year (2 instalments — Kharif & Rabi)",
        "how_to_apply": "Visit annadathasukhibhava.ap.gov.in or nearest Raithu Seva Kendra with Aadhaar + land passbook",
        "helpline": "1902",
        "category": "income_support"
    },
    {
        "id": "pm_kisan",
        "name": "PM-KISAN (Central Govt)",
        "description": "₹6,000/year direct income support from Central Government in 3 instalments of ₹2,000 each. Already included in Annadata Sukhibhava for AP farmers.",
        "eligibility": {
            "farmer_type": ["owner"],
            "caste": ["all"],
            "min_age": 18,
            "notes": "Not eligible if income taxpayer, govt employee, or pension >₹10,000/month"
        },
        "amount": "₹6,000/year (3 instalments of ₹2,000)",
        "how_to_apply": "Visit pmkisan.gov.in or nearest CSC center with Aadhaar + land records",
        "helpline": "155261",
        "category": "income_support"
    },
    {
        "id": "pmfby",
        "name": "PMFBY — Pradhan Mantri Fasal Bima Yojana",
        "description": "Crop insurance at just 2% premium for Kharif crops and 1.5% for Rabi crops. Covers losses due to drought, flood, pest, disease.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
            "notes": "Must register before sowing season at bank or CSC"
        },
        "amount": "Compensation based on actual crop loss",
        "how_to_apply": "Register at nearest bank branch or CSC before crop sowing. Carry Aadhaar, land records, bank passbook.",
        "helpline": "1800-180-1551",
        "category": "insurance"
    },
    {
        "id": "kcc",
        "name": "Kisan Credit Card (KCC)",
        "description": "Short-term crop loan up to ₹3 lakh at only 4% interest rate per year. Covers crop production, post-harvest, and allied activities.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "Loan up to ₹3 lakh @ 4% interest/year",
        "how_to_apply": "Apply at any nationalized bank or cooperative bank with land records + Aadhaar + passport photo",
        "helpline": "1800-180-1551",
        "category": "credit"
    },
    {
        "id": "pm_kusum",
        "name": "PM-KUSUM Solar Pump Scheme",
        "description": "Up to 90% subsidy on solar pumps for irrigation. Helps reduce electricity bills and ensure reliable water supply.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "90% subsidy (60% govt + 30% bank loan), farmer pays only 10%",
        "how_to_apply": "Apply at AP state agriculture department or kusum.gov.in with land documents + Aadhaar",
        "helpline": "1800-180-3333",
        "category": "subsidy"
    },
    {
        "id": "ap_free_crop_insurance",
        "name": "AP Free Crop Insurance",
        "description": "AP government pays the full crop insurance premium on behalf of farmers. Farmers get coverage at zero cost.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "Full insurance premium paid by AP govt — free for farmers",
        "how_to_apply": "Auto-enrolled if registered in AP farmer database. Visit nearest Raithu Seva Kendra to confirm enrollment.",
        "helpline": "1902",
        "category": "insurance"
    },
    {
        "id": "ap_micro_irrigation",
        "name": "AP Micro Irrigation Scheme",
        "description": "100% subsidy on drip and sprinkler irrigation systems for small and marginal farmers (up to 5 acres).",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "max_land": 5,
            "min_age": 18,
        },
        "amount": "100% subsidy for small farmers (<5 acres), 90% for others",
        "how_to_apply": "Apply at nearest Raithu Seva Kendra or AP Micro Irrigation office with land documents",
        "helpline": "1902",
        "category": "subsidy"
    },
    {
        "id": "enam",
        "name": "eNAM — Online Mandi Platform",
        "description": "Sell your crops online to buyers across India and get better prices than local mandis. No middlemen.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "Better market prices — no fixed amount",
        "how_to_apply": "Register at enam.gov.in or nearest APMC mandi with Aadhaar + bank account details",
        "helpline": "1800-270-0224",
        "category": "marketing"
    },
    {
        "id": "rytanna_mee_kosam",
        "name": "Rytanna Mee Kosam (రైతన్న మీ కోసం)",
        "description": "New AP scheme launched 2026 to educate farmers on Panchasutras — 5 principles for profitable, safe, and modern farming.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "Training, awareness, and agricultural support",
        "how_to_apply": "Contact nearest Raithu Seva Kendra or village agriculture officer",
        "helpline": "1902",
        "category": "training"
    },
    {
        "id": "jagananna_chedodu",
        "name": "Jagananna Chedodu (BC Farmers)",
        "description": "₹10,000/year financial assistance for BC community farmers for agricultural needs.",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["bc"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "₹10,000/year",
        "how_to_apply": "Visit nearest Raithu Seva Kendra with caste certificate + Aadhaar + land documents",
        "helpline": "1902",
        "category": "income_support"
    },
]

@router.get("/check")
async def check_eligibility(
    farmer_type: str = Query("owner", description="owner or tenant"),
    land_acres: float = Query(2.0, description="Land in acres"),
    caste: str = Query("general", description="general, bc, sc, st"),
    age: int = Query(30, description="Age of farmer"),
    state: str = Query("Andhra Pradesh", description="State")
):
    eligible = []
    for scheme in SCHEMES:
        e = scheme["eligibility"]

        if farmer_type not in e.get("farmer_type", [farmer_type]):
            continue

        allowed_castes = e.get("caste", ["all"])
        if "all" not in allowed_castes and caste.lower() not in allowed_castes:
            continue

        if age < e.get("min_age", 0):
            continue

        if e.get("max_land") and land_acres > e["max_land"]:
            continue

        if e.get("state") and state not in e.get("state", state):
            continue

        eligible.append({
            "id": scheme["id"],
            "name": scheme["name"],
            "description": scheme["description"],
            "amount": scheme["amount"],
            "how_to_apply": scheme["how_to_apply"],
            "helpline": scheme["helpline"],
            "category": scheme["category"],
            "notes": scheme["eligibility"].get("notes", "")
        })

    return {
        "eligible_count": len(eligible),
        "schemes": eligible,
        "farmer_profile": {
            "type": farmer_type,
            "land_acres": land_acres,
            "caste": caste,
            "age": age,
            "state": state
        },
        "last_updated": "June 2026"
    }

@router.get("/all")
async def all_schemes():
    return {"schemes": SCHEMES, "last_updated": "June 2026"}
