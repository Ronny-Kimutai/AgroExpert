from crops.models import Crop

def parse_range(range_str):
    try:
        low, high = map(float, range_str.split('-'))
        return low, high
    except:
        return None, None

def month_to_num(m):
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

def forward_chaining_db(pH, rainfall, month, soilType):
    recs = []
    for crop in Crop.objects.all():
        pHmin, pHmax = parse_range(crop.pH_range)
        rmin, rmax = parse_range(crop.rainfall_range)
        months = [m.strip() for m in crop.planting_months.split(',')]
        soils = [s.strip() for s in crop.soil_types.split(',')]

        reasons = []
        if not (pHmin <= pH <= pHmax):
            continue
        reasons.append(f"Soil pH is within {pHmin}-{pHmax}")

        if not (rmin <= rainfall <= rmax):
            continue
        reasons.append(f"Rainfall between {rmin}-{rmax} mm/year")

        if months and "Year-round" not in " ".join(months):
            mnum = month_to_num(month)
            mnums = [month_to_num(m) for m in months if month_to_num(m)]
            if mnums and mnum not in mnums:
                continue
        reasons.append(f"{month} is in planting season for {crop.name}")

        if soils and not any(s.lower() in soilType.lower() for s in soils):
            continue
        reasons.append(f"Soil type '{soilType}' is suitable for {crop.name}")

        recs.append({
            "crop": crop.name,
            "priority": crop.priority,
            "reason": "; ".join(reasons)
        })

    recs.sort(key=lambda x: -x["priority"])
    return recs

def can_plant_db(crop_name, pH, rainfall, month, soilType):
    crops = Crop.objects.filter(name__iexact=crop_name)
    if not crops.exists():
        return {"canPlant": False, "explanation": "Crop not found in database."}

    crop = crops.first()
    pHmin, pHmax = parse_range(crop.pH_range)
    rmin, rmax = parse_range(crop.rainfall_range)
    months = [m.strip() for m in crop.planting_months.split(',')]
    soils = [s.strip() for s in crop.soil_types.split(',')]

    reasons = []
    if not (pHmin <= pH <= pHmax):
        return {"canPlant": False, "explanation": f"Soil pH {pH} not in range {pHmin}-{pHmax}"}
    reasons.append(f"Soil pH is within {pHmin}-{pHmax}")

    if not (rmin <= rainfall <= rmax):
        return {"canPlant": False, "explanation": f"Rainfall {rainfall} mm/year not in range {rmin}-{rmax} mm/year"}
    reasons.append(f"Rainfall between {rmin}-{rmax} mm/year")

    if months and "Year-round" not in " ".join(months):
        mnum = month_to_num(month)
        mnums = [month_to_num(m) for m in months if month_to_num(m)]
        if mnums and mnum not in mnums:
            return {"canPlant": False, "explanation": f"Month {month} not in planting season {months}"}
    reasons.append(f"{month} is in planting season for {crop.name}")

    if soils and not any(s.lower() in soilType.lower() for s in soils):
        return {"canPlant": False, "explanation": f"Soil type '{soilType}' not suitable for {crop.name}"}
    reasons.append(f"Soil type '{soilType}' is suitable for {crop.name}")

    return {"canPlant": True, "explanation": "; ".join(reasons)}
