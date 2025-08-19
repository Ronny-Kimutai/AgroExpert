from agroexpert_main.crops.models import Crop
import time

# Keep global memory of fired rules to enforce refractoriness
fired_instances = set()

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


def forward_chaining_db(ph, rainfall, month, soil_type):
    recs = []
    now = time.time()  # timestamp for recency simulation

    for crop in Crop.objects.all():
        ph_min, ph_max = parse_range(crop.pH_range)
        r_min, r_max = parse_range(crop.rainfall_range)
        months = [m.strip() for m in crop.planting_months.split(',')]
        soils = [s.strip() for s in crop.soil_types.split(',')]

        reasons = []
        matched_facts = []

        # Rule: pH
        if not (ph_min <= ph <= ph_max):
            continue
        reasons.append(f"Soil pH is within {ph_min}-{ph_max}")
        matched_facts.append(("pH", ph, now))

        # Rule: rainfall
        if not (r_min <= rainfall <= r_max):
            continue
        reasons.append(f"Rainfall between {r_min}-{r_max} mm/year")
        matched_facts.append(("rainfall", rainfall, now))

        # Rule: month
        if months and "Year-round" not in " ".join(months):
            mnum = month_to_num(month)
            mnums = [month_to_num(m) for m in months if month_to_num(m)]
            if mnums and mnum not in mnums:
                continue
        reasons.append(f"{month} is in planting season for {crop.name}")
        matched_facts.append(("month", month, now))

        # Rule: soil
        if soils and not any(s.lower() in soil_type.lower() for s in soils):
            continue
        reasons.append(f"Soil type '{soil_type}' is suitable for {crop.name}")
        matched_facts.append(("soil", soil_type, now))

        recs.append({
            "crop": crop.name,
            "priority": crop.priority,
            "reason": "; ".join(reasons),
            "facts": matched_facts,
            "timestamp": now,
        })

    # === POLICY STACK ===
    def policy_sort_key(r):
        # 1. Refractoriness: skip if fired before
        instance_key = (r["crop"], tuple(f[1] for f in r["facts"]))
        if instance_key in fired_instances:
            return (9999,)  # push to bottom

        # 2. MEA + Recency: first matched fact's timestamp (most recent first)
        mea_recency = -r["facts"][0][2] if r["facts"] else 0

        # 3. Specificity: number of matched facts (more = higher specificity)
        specificity = -len(r["facts"])

        # 4. Recency of all facts (max timestamp)
        all_recency = -max(f[2] for f in r["facts"]) if r["facts"] else 0

        # 5. Lexical order (crop name)
        lexical = r["crop"]

        return 0, mea_recency, specificity, all_recency, lexical

    recs.sort(key=policy_sort_key)

    # Mark top recommendation as fired (for refractoriness)
    if recs:
        fired_instances.add((recs[0]["crop"], tuple(f[1] for f in recs[0]["facts"])))

    return recs

def can_plant_db(crop_name, ph, rainfall, month, soil_type):
    """
    Check if a specific crop can be planted given the conditions.
    Returns a dict with {canPlant: bool, explanation: str}
    """
    try:
        crop = Crop.objects.get(name__iexact=crop_name)
    except Crop.DoesNotExist:
        return {
            "canPlant": False,
            "explanation": f"Crop '{crop_name}' not found in database."
        }

    reasons = []

    # pH check
    ph_min, ph_max = parse_range(crop.pH_range)
    if not (ph_min <= ph <= ph_max):
        return {"canPlant": False, "explanation": f"Soil pH must be between {ph_min}-{ph_max}"}
    reasons.append(f"Soil pH is within {ph_min}-{ph_max}")

    # rainfall check
    r_min, r_max = parse_range(crop.rainfall_range)
    if not (r_min <= rainfall <= r_max):
        return {"canPlant": False, "explanation": f"Rainfall must be between {r_min}-{r_max} mm/year"}
    reasons.append(f"Rainfall between {r_min}-{r_max} mm/year")

    # month check
    months = [m.strip() for m in crop.planting_months.split(',')]
    if months and "Year-round" not in " ".join(months):
        m_num = month_to_num(month)
        m_nums = [month_to_num(m) for m in months if month_to_num(m)]
        if m_nums and m_num not in m_nums:
            return {"canPlant": False, "explanation": f"{month} is not in planting season for {crop.name}"}
    reasons.append(f"{month} is in planting season for {crop.name}")

    # soil check
    soils = [s.strip() for s in crop.soil_types.split(',')]
    if soils and not any(s.lower() in soil_type.lower() for s in soils):
        return {"canPlant": False, "explanation": f"Soil type '{soil_type}' is not suitable for {crop.name}"}
    reasons.append(f"Soil type '{soil_type}' is suitable for {crop.name}")

    return {"canPlant": True, "explanation": "; ".join(reasons)}
