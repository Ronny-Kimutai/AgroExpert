import streamlit as st
from typing import Any

# ============================
# Utilities
# ============================

def month_to_num(m: Any) -> int:
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    if isinstance(m, int):
        return m
    if isinstance(m, str):
        m = m.strip()
        if m.isdigit():
            return int(m)
        for i, name in enumerate(months, 1):
            if name.lower().startswith(m.lower()):
                return i
    return None

# ============================
# Knowledge Base: Frames
# ============================

Frames = [
    {
        "Name": "Avocado",
        "pHRange": (5.5, 6.5),
        "RainfallRange": (1000, 1500),
        "PlantingMonths": ["March", "April", "September", "October"],
        "SoilTypes": ["Sandy", "Alluvial", "Loamy"],
        "Priority": 90
    },
    {
        "Name": "Tomato",
        "pHRange": (6.0, 6.8),
        "RainfallRange": (600, 1200),
        "PlantingMonths": ["March", "April", "October", "November"],
        "SoilTypes": ["Light loam", "Sandy loam", "Loam"],
        "Priority": 70
    },
    {
        "Name": "Capsicum",
        "pHRange": (6.0, 6.5),
        "RainfallRange": (600, 1200),
        "PlantingMonths": ["Year-round with irrigation", "March", "April", "September", "October"],
        "SoilTypes": ["Well-drained loam", "Loam"],
        "Priority": 60
    },
    {
        "Name": "Macadamia",
        "pHRange": (5.0, 6.5),
        "RainfallRange": (850, 1200),
        "PlantingMonths": ["March", "April", "October"],
        "SoilTypes": ["Loamy"],
        "Priority": 75
    },
    {
        "Name": "Passion Fruit",
        "pHRange": (5.5, 6.5),
        "RainfallRange": (900, 2000),
        "PlantingMonths": ["March", "April", "November"],
        "SoilTypes": ["Loamy"],
        "Priority": 65
    }
]

# ============================
# Production Rules
# ============================

Rules = []
for f in Frames:
    def make_condition(pHmin, pHmax, rmin, rmax, months, soils, crop_name):
        def cond(pH, rain, month, soilType):
            reasons = []
            if not (pHmin <= pH <= pHmax):
                return False, f"Soil pH {pH} not in range {pHmin}-{pHmax}"
            reasons.append(f"Soil pH is within {pHmin}-{pHmax}")

            if not (rmin <= rain <= rmax):
                return False, f"Rainfall {rain} mm/year not in range {rmin}-{rmax} mm/year"
            reasons.append(f"Rainfall between {rmin}-{rmax} mm/year")

            if months and "Year-round" not in " ".join(months):
                mnum = month_to_num(month)
                mnums = [month_to_num(m) for m in months if month_to_num(m)]
                if mnums and mnum not in mnums:
                    return False, f"Month {month} not in planting season {months}"
            reasons.append(f"{month} is in planting season for {crop_name}")

            if soils and not any(s.lower() in soilType.lower() for s in soils):
                return False, f"Soil type '{soilType}' not suitable for {crop_name}"
            reasons.append(f"Soil type '{soilType}' is suitable for {crop_name}")

            return True, "; ".join(reasons)
        return cond

    cond_fn = make_condition(
        f["pHRange"][0], f["pHRange"][1],
        f["RainfallRange"][0], f["RainfallRange"][1],
        f.get("PlantingMonths", []),
        f.get("SoilTypes", []),
        f["Name"]
    )
    Rules.append({
        "crop": f["Name"],
        "condition": cond_fn,
        "priority": f["Priority"]
    })

# ============================
# Forward Chaining
# ============================

def forward_chaining(facts: dict):
    recs = []
    for rule in Rules:
        matched, reason = rule["condition"](facts["pH"], facts["rainfall"], facts["month"], facts["soilType"])
        if matched:
            recs.append({
                "crop": rule["crop"],
                "priority": rule["priority"],
                "reason": reason
            })
    recs.sort(key=lambda x: -x["priority"])
    return recs

# ============================
# Backward Chaining
# ============================

def can_plant(crop_name: str, facts: dict) -> dict:
    for rule in Rules:
        if rule["crop"].lower() == crop_name.lower():
            matched, reason = rule["condition"](facts["pH"], facts["rainfall"], facts["month"], facts["soilType"])
            return {"canPlant": matched, "explanation": reason}
    return {"canPlant": False, "explanation": "Crop not found in database."}

# ============================
# Streamlit App
# ============================

st.title("🌱 AgroExpert - Crop Recommendation System")

# User inputs
pH = st.number_input("Enter soil pH", min_value=0.0, max_value=14.0, step=0.1, value=6.0)
rainfall = st.number_input("Enter annual rainfall (mm)", min_value=0.0, step=10.0, value=1000.0)
month = st.selectbox("Select current month", 
    ["January", "February", "March", "April", "May", "June", 
     "July", "August", "September", "October", "November", "December"])
soilType = st.text_input("Enter soil type", "Loamy")

facts = {
    "pH": pH,
    "rainfall": rainfall,
    "month": month,
    "soilType": soilType
}

# Forward chaining results
if st.button("Get Recommendations"):
    recommendations = forward_chaining(facts)
    if recommendations:
        st.subheader("Recommended Crops")
        for r in recommendations:
            st.markdown(f"**{r['crop']}** (priority={r['priority']})")
            st.caption(r['reason'])
    else:
        st.warning("No suitable crops found for the given conditions.")

# Backward chaining
st.subheader("Check a Specific Crop")
check_crop = st.text_input("Enter crop name to check")
if st.button("Check Crop"):
    if check_crop:
        res = can_plant(check_crop, facts)
        if res['canPlant']:
            st.success(f"Yes, you can plant {check_crop}.")
        else:
            st.error(f"No, you cannot plant {check_crop}.")
        st.caption(res["explanation"])
    else:
        st.info("Please enter a crop name.")
