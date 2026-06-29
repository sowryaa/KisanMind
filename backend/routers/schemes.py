from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

SCHEMES = [
    {
        "id": "pm_kisan",
        "name": "PM-KISAN",
        "description": "₹6,000/year direct income support in 3 instalments",
        "eligibility": {
            "land_owner": True,
            "max_land": None,
            "farmer_type": ["owner"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "₹6,000/year",
        "how_to_apply": "Visit pmkisan.gov.in or nearest CSC center with Aadhaar + land records",
        "helpline": "155261",
        "category": "income_support"
    },
    {
        "id": "ysr_rythu_bharosa",
        "name": "YSR Rythu Bharosa",
        "description": "₹13,500/year for land owners, ₹7,500 for tenant farmers",
        "eligibility": {
            "land_owner": True,
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
            "state": "Andhra Pradesh"
        },
        "amount": "₹13,500 (owner) / ₹7,500 (tenant)",
        "how_to_apply": "Visit nearest RBK (Rythu Bharosa Kendra) with Aadhaar + land passbook",
        "helpline": "1902",
        "category": "income_support"
    },
    {
        "id": "pmfby",
        "name": "PMFBY (Crop Insurance)",
        "description": "Crop insurance at 2% premium for Kharif, 1.5% for Rabi",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "Depends on crop loss",
        "how_to_apply": "Register at nearest bank or CSC before sowing season",
        "helpline": "1800-180-1551",
        "category": "insurance"
    },
    {
        "id": "kcc",
        "name": "Kisan Credit Card (KCC)",
        "description": "Crop loan up to ₹3 lakh at 4% interest rate",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "Up to ₹3 lakh @ 4% interest",
        "how_to_apply": "Apply at any nationalized bank with land records + Aadhaar",
        "helpline": "1800-180-1551",
        "category": "credit"
    },
    {
        "id": "pm_kusum",
        "name": "PM Kusum (Solar Pump)",
        "description": "90% subsidy on solar pumps for irrigation",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "90% subsidy on solar pump cost",
        "how_to_apply": "Apply at state agriculture department or kusum.gov.in",
        "helpline": "1800-180-3333",
        "category": "subsidy"
    },
    {
        "id": "ysr_free_crop_insurance",
        "name": "YSR Free Crop Insurance",
        "description": "AP government pays full crop insurance premium for farmers",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "Full premium covered by AP govt",
        "how_to_apply": "Auto-enrolled if registered in AP farmer database. Visit RBK to confirm.",
        "helpline": "1902",
        "category": "insurance"
    },
    {
        "id": "ysr_sunna_vaddi",
        "name": "YSR Sunna Vaddi (Zero Interest Loan)",
        "description": "Zero interest loans for farmers through APSFC",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "Zero interest on existing loans",
        "how_to_apply": "Visit nearest APSFC office or RBK",
        "helpline": "1902",
        "category": "credit"
    },
    {
        "id": "ap_micro_irrigation",
        "name": "AP Micro Irrigation Scheme",
        "description": "100% subsidy on drip/sprinkler irrigation for small farmers",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "state": "Andhra Pradesh",
            "max_land": 5,
            "min_age": 18,
        },
        "amount": "100% subsidy (small farmers), 90% (others)",
        "how_to_apply": "Apply at nearest RBK or AP Micro Irrigation office",
        "helpline": "1902",
        "category": "subsidy"
    },
    {
        "id": "jagananna_chedodu",
        "name": "Jagananna Chedodu",
        "description": "₹10,000/year financial assistance for BC community farmers",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["bc"],
            "state": "Andhra Pradesh",
            "min_age": 18,
        },
        "amount": "₹10,000/year",
        "how_to_apply": "Visit nearest RBK with caste certificate + Aadhaar",
        "helpline": "1902",
        "category": "income_support"
    },
    {
        "id": "enam",
        "name": "eNAM (Online Mandi)",
        "description": "Sell crops online at better prices across India",
        "eligibility": {
            "farmer_type": ["owner", "tenant"],
            "caste": ["all"],
            "min_age": 18,
        },
        "amount": "Better market prices",
        "how_to_apply": "Register at enam.gov.in or nearest APMC mandi",
        "helpline": "1800-270-0224",
        "category": "marketing"
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
        
        # Check farmer type
        if farmer_type not in e.get("farmer_type", [farmer_type]):
            continue
        
        # Check caste
        allowed_castes = e.get("caste", ["all"])
        if "all" not in allowed_castes and caste.lower() not in allowed_castes:
            continue
        
        # Check age
        if age < e.get("min_age", 0):
            continue
        
        # Check max land
        if e.get("max_land") and land_acres > e["max_land"]:
            continue
        
        # Check state
        if e.get("state") and state not in e["state"]:
            continue

        eligible.append({
            "id": scheme["id"],
            "name": scheme["name"],
            "description": scheme["description"],
            "amount": scheme["amount"],
            "how_to_apply": scheme["how_to_apply"],
            "helpline": scheme["helpline"],
            "category": scheme["category"]
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
        }
    }

@router.get("/all")
async def all_schemes():
    return {"schemes": SCHEMES}
