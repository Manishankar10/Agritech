from datetime import datetime, timedelta, date

# Standard biological parameters for Indian Livestock
COW_GESTATION_DAYS = 283
BUFFALO_GESTATION_DAYS = 310
GOAT_GESTATION_DAYS = 150
COW_ESTRUS_CYCLE_DAYS = 21
GOAT_ESTRUS_CYCLE_DAYS = 20
COW_PD_CHECK_DAYS = 60
COW_DRY_PERIOD_DAYS_BEFORE_CALVING = 60
GOAT_WEANING_DAYS = 60

def parse_date(date_input):
    if not date_input:
        return None
    if isinstance(date_input, (datetime, date)):
        return date(date_input.year, date_input.month, date_input.day) if isinstance(date_input, datetime) else date_input
    try:
        return datetime.strptime(str(date_input).split("T")[0], "%Y-%m-%d").date()
    except Exception:
        return None

def calculate_cattle_reproduction(insemination_date, is_buffalo=False):
    """
    Computes key reproductive milestones for cattle given an insemination/breeding date.
    Returns:
      - next_heat_check: 21 days later (if not conceived)
      - pd_check_date: 60 days later (pregnancy diagnosis)
      - dry_off_date: 60 days before calving (stop milking)
      - expected_calving_date: 283 days (cow) or 310 days (buffalo)
      - days_pregnant: today - insemination_date
      - days_remaining: expected_calving - today
      - progress_percentage: 0 - 100%
    """
    dt = parse_date(insemination_date)
    if not dt:
        return {}
    
    today = date.today()
    gestation_days = BUFFALO_GESTATION_DAYS if is_buffalo else COW_GESTATION_DAYS
    
    calving_date = dt + timedelta(days=gestation_days)
    next_heat = dt + timedelta(days=COW_ESTRUS_CYCLE_DAYS)
    pd_date = dt + timedelta(days=COW_PD_CHECK_DAYS)
    dry_date = calving_date - timedelta(days=COW_DRY_PERIOD_DAYS_BEFORE_CALVING)
    
    days_pregnant = max(0, (today - dt).days)
    days_remaining = (calving_date - today).days
    progress = min(100.0, max(0.0, round((days_pregnant / gestation_days) * 100, 1)))

    # Determine current status stage
    if today < next_heat:
        stage = "Observation / Heat Watch"
        stage_ta = "முதல் சினை கண்காணிப்பு (21 நாள் வரை)"
    elif today < pd_date:
        stage = "Waiting for Pregnancy Diagnosis (PD)"
        stage_ta = "சினை பரிசோதனைக்கு காத்திருப்பு"
    elif today < dry_date:
        stage = "Confirmed Pregnant - Active Lactation"
        stage_ta = "உறுதிப்படுத்தப்பட்ட சினை - பால் கறவை காலம்"
    elif today < calving_date:
        stage = "Dry Period (Fetal Growth & Rest)"
        stage_ta = "கறவை நிறுத்தம் (வளர்ச்சி & ஓய்வு காலம்)"
    else:
        stage = "Calving Due / Imminent"
        stage_ta = "கன்று ஈனும் காலம்"

    return {
        "insemination_date": dt.isoformat(),
        "next_heat_check": next_heat.isoformat(),
        "pd_check_date": pd_date.isoformat(),
        "dry_off_date": dry_date.isoformat(),
        "expected_calving_date": calving_date.isoformat(),
        "gestation_days_total": gestation_days,
        "days_pregnant": days_pregnant,
        "days_remaining": days_remaining,
        "progress_percentage": progress,
        "stage": stage,
        "stage_ta": stage_ta
    }

def calculate_goat_reproduction(mating_date):
    """
    Computes key reproductive milestones for Goats / Sheep given mating date.
    Returns:
      - next_heat_check: 20 days
      - expected_kidding_date: 150 days (~5 months)
      - expected_weaning_date: kidding + 60 days
      - days_pregnant: today - mating_date
      - days_remaining: expected_kidding - today
    """
    dt = parse_date(mating_date)
    if not dt:
        return {}
    
    today = date.today()
    gestation_days = GOAT_GESTATION_DAYS
    kidding_date = dt + timedelta(days=gestation_days)
    next_heat = dt + timedelta(days=GOAT_ESTRUS_CYCLE_DAYS)
    weaning_date = kidding_date + timedelta(days=GOAT_WEANING_DAYS)
    
    days_pregnant = max(0, (today - dt).days)
    days_remaining = (kidding_date - today).days
    progress = min(100.0, max(0.0, round((days_pregnant / gestation_days) * 100, 1)))

    if today < next_heat:
        stage = "Mated - Heat Monitoring"
        stage_ta = "இணை சேர்க்கை - வெப்ப கண்காணிப்பு"
    elif today < kidding_date - timedelta(days=30):
        stage = "Early to Mid Gestation"
        stage_ta = "வளரும் சினை காலம்"
    elif today < kidding_date:
        stage = "Advanced Pregnancy (Extra feed & Care)"
        stage_ta = "முதிர்ந்த சினை காலம் (கூடுதல் தீவனம்)"
    else:
        stage = "Kidding Due"
        stage_ta = "குட்டி ஈனும் காலம்"

    return {
        "mating_date": dt.isoformat(),
        "next_heat_check": next_heat.isoformat(),
        "expected_kidding_date": kidding_date.isoformat(),
        "weaning_date": weaning_date.isoformat(),
        "gestation_days_total": gestation_days,
        "days_pregnant": days_pregnant,
        "days_remaining": days_remaining,
        "progress_percentage": progress,
        "stage": stage,
        "stage_ta": stage_ta
    }

def get_vaccination_calendar():
    """Returns official veterinary vaccination schedule for Tamil Nadu livestock."""
    return [
        {
            "disease": "Foot and Mouth Disease (FMD / கோமாரி நோய்)",
            "species": ["cow", "buffalo", "goat", "sheep"],
            "schedule": "Twice a year (March and September)",
            "schedule_ta": "ஆண்டுக்கு இருமுறை (மார்ச் & செப்டம்பர்)",
            "importance": "High",
            "notes": "Statewide free vaccination camps by TN Animal Husbandry Dept."
        },
        {
            "disease": "Deworming (குடற்புழு நீக்கம்)",
            "species": ["cow", "buffalo", "goat", "sheep", "poultry"],
            "schedule": "Every 3-4 months (Quarterly)",
            "schedule_ta": "3-4 மாதங்களுக்கு ஒருமுறை",
            "importance": "High",
            "notes": "Administer Albendazole or Fenbendazole pre-monsoon."
        },
        {
            "disease": "Anthrax (அடைப்பான் நோய்)",
            "species": ["cow", "buffalo", "sheep"],
            "schedule": "Once a year (August / Pre-monsoon)",
            "schedule_ta": "ஆண்டுக்கு ஒருமுறை (ஆகஸ்ட் / பருவமழைக்கு முன்)",
            "importance": "High",
            "notes": "Crucial for endemic areas in Tamil Nadu."
        },
        {
            "disease": "Black Quarter (BQ / கருங்காலி நோய்)",
            "species": ["cow", "buffalo"],
            "schedule": "Once a year (May-June)",
            "schedule_ta": "ஆண்டுக்கு ஒருமுறை (மே - ஜூன்)",
            "importance": "Medium",
            "notes": "For cattle above 6 months of age."
        },
        {
            "disease": "Enterotoxemia (ET / துள்ளு மாரி)",
            "species": ["goat", "sheep"],
            "schedule": "Annually before lush monsoon flush",
            "schedule_ta": "பருவமழை பசுந்தீவன காலத்திற்கு முன் ஆண்டுதோறும்",
            "importance": "High",
            "notes": "Protects goats from sudden death due to clostridial toxins."
        },
        {
            "disease": "Ranikhet Disease (வெள்ளைக் கழிச்சல்)",
            "species": ["poultry"],
            "schedule": "RDV F1 at 7th day, Lasota at 4th week, RDVK at 8th week",
            "schedule_ta": "7-வது நாள், 4-வது வாரம் மற்றும் 8-வது வாரம்",
            "importance": "Critical",
            "notes": "Essential for country chicken / Aseel / Kadaknath."
        }
    ]

def generate_livestock_alerts(livestock_list, breeding_records):
    """
    Scans all animals and active breeding records to generate actionable farmer alerts.
    """
    today = date.today()
    alerts = []
    
    animal_map = {str(a.get("id")): a for a in livestock_list}

    for record in breeding_records:
        animal_id = str(record.get("animal_id"))
        animal = animal_map.get(animal_id)
        if not animal or record.get("status") == "completed":
            continue

        species = (animal.get("species") or "cow").lower()
        tag = animal.get("tag_id") or animal.get("name") or f"Animal #{animal_id[:4]}"
        breed = animal.get("breed", "")

        event_type = record.get("event_type", "insemination")
        event_date = parse_date(record.get("date"))
        if not event_date:
            continue

        if species in ["cow", "buffalo", "cattle"]:
            timeline = calculate_cattle_reproduction(event_date, is_buffalo=(species == "buffalo"))
            
            # Check Calving
            calving_dt = parse_date(timeline.get("expected_calving_date"))
            if calving_dt:
                days_to_calve = (calving_dt - today).days
                if -5 <= days_to_calve <= 15:
                    urgency = "danger" if days_to_calve <= 5 else "warning"
                    alerts.append({
                        "type": "calving",
                        "urgency": urgency,
                        "animal_id": animal_id,
                        "tag": tag,
                        "title": f"Calving Due Soon: {tag} ({breed})",
                        "title_ta": f"ஈற்று நாள் நெருங்குகிறது: {tag} ({breed})",
                        "message": f"Expected calving in {days_to_calve} days on {calving_dt}. Prepare clean bedding and colostrum kit.",
                        "message_ta": f"இன்னும் {days_to_calve} நாட்களில் ({calving_dt}) கன்று ஈனும். தூய கொட்டகை மற்றும் கன்றுக்கான வசதிகளை தயார் செய்யவும்.",
                        "date": calving_dt.isoformat(),
                        "days_left": days_to_calve
                    })

            # Check Dry Off
            dry_dt = parse_date(timeline.get("dry_off_date"))
            if dry_dt:
                days_to_dry = (dry_dt - today).days
                if -3 <= days_to_dry <= 10:
                    alerts.append({
                        "type": "dry_off",
                        "urgency": "warning",
                        "animal_id": animal_id,
                        "tag": tag,
                        "title": f"Dry Period Alert: {tag}",
                        "title_ta": f"பால் கறவை நிறுத்தும் காலம்: {tag}",
                        "message": f"Due to dry off on {dry_dt} (60 days before calving). Stop milking to allow udder rest.",
                        "message_ta": f"{dry_dt} அன்று பால் கறவையை நிறுத்தவும் (ஈற்று நாளுக்கு 60 நாள் முன்). இது கருவின் முழு வளர்ச்சிக்கு அவசியமானது.",
                        "date": dry_dt.isoformat(),
                        "days_left": days_to_dry
                    })

            # Check PD Check
            pd_dt = parse_date(timeline.get("pd_check_date"))
            if pd_dt:
                days_to_pd = (pd_dt - today).days
                if -5 <= days_to_pd <= 10:
                    alerts.append({
                        "type": "pd_check",
                        "urgency": "info",
                        "animal_id": animal_id,
                        "tag": tag,
                        "title": f"Pregnancy Check (PD) Due: {tag}",
                        "title_ta": f"சினை பரிசோதனை செய்ய வேண்டிய நாள்: {tag}",
                        "message": f"60-90 days elapsed since AI. Contact veterinary doctor for PD check on {pd_dt}.",
                        "message_ta": f"சினை ஊசி போட்டு 60 நாட்கள் முடிந்தது. கால்நடை மருத்துவரை அணுகி சினை பரிசோதனை ({pd_dt}) செய்யவும்.",
                        "date": pd_dt.isoformat(),
                        "days_left": days_to_pd
                    })

        elif species in ["goat", "sheep"]:
            timeline = calculate_goat_reproduction(event_date)
            kidding_dt = parse_date(timeline.get("expected_kidding_date"))
            if kidding_dt:
                days_to_kid = (kidding_dt - today).days
                if -3 <= days_to_kid <= 15:
                    urgency = "danger" if days_to_kid <= 5 else "warning"
                    alerts.append({
                        "type": "kidding",
                        "urgency": urgency,
                        "animal_id": animal_id,
                        "tag": tag,
                        "title": f"Goat Kidding Due: {tag} ({breed})",
                        "title_ta": f"ஆடு குட்டி ஈனும் காலம்: {tag} ({breed})",
                        "message": f"Expected kidding in {days_to_kid} days on {kidding_dt}. Provide isolated quiet pen.",
                        "message_ta": f"இன்னும் {days_to_kid} நாட்களில் ({kidding_dt}) குட்டி ஈனும். அமைதியான தனி கொட்டகை ஒதுக்கவும்.",
                        "date": kidding_dt.isoformat(),
                        "days_left": days_to_kid
                    })

    # Sort alerts by urgency and days left
    alerts.sort(key=lambda x: x.get("days_left", 999))
    return alerts
