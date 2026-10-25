import os
from datetime import date, timedelta
import db_store

def seed_sample_farm_data():
    """Initializes sample realistic farm data for first run if empty."""
    plots = db_store.get_all("plots")
    if plots:
        return # Already seeded or user has data

    today = date.today()

    # 1. Plots
    plot_a = {
        "id": "plot_cauvery_delta",
        "name": "Plot A - Vadakku Kadu (வடக்கு காடு)",
        "area_acres": 3.5,
        "soil_type": "Clay Loam (வண்டல் மண்)",
        "water_source": "Canal & Borewell (வாய்க்கால் & ஆழ்துளை)",
        "survey_no": "142/2B",
        "location": "Thiruvidaimarudur, Thanjavur"
    }
    plot_b = {
        "id": "plot_drip_thottam",
        "name": "Plot B - Thottam (மேற்கு தோட்டம்)",
        "area_acres": 2.0,
        "soil_type": "Red Loam (செம்மண்)",
        "water_source": "Drip Irrigation & Well (சொட்டு நீர் & கிணறு)",
        "survey_no": "88/1A",
        "location": "Thiruvidaimarudur, Thanjavur"
    }
    db_store.save_item("plots", plot_a)
    db_store.save_item("plots", plot_b)

    # 2. Crops
    sow_paddy = (today - timedelta(days=48)).isoformat()
    harvest_paddy = (today + timedelta(days=77)).isoformat()
    crop_paddy = {
        "id": "crop_cr1009_paddy",
        "plot_id": "plot_cauvery_delta",
        "plot_name": "Plot A - Vadakku Kadu",
        "crop_name": "Paddy (நெல்)",
        "variety": "CR-1009 Sub-1 (Ponmani)",
        "season": "Samba / Thaladi (சம்பா / தாளடி)",
        "sowing_date": sow_paddy,
        "stage": "Tillering & Vegetative (தூர்கட்டும் பருவம்)",
        "expected_harvest": harvest_paddy,
        "area_cultivated_acres": 3.5,
        "status": "active",
        "notes": "Good tillering observed, bio-fertilizer Azospirillum applied."
    }

    sow_banana = (today - timedelta(days=120)).isoformat()
    harvest_banana = (today + timedelta(days=210)).isoformat()
    crop_banana = {
        "id": "crop_poovan_banana",
        "plot_id": "plot_drip_thottam",
        "plot_name": "Plot B - Thottam",
        "crop_name": "Banana (வாழை)",
        "variety": "Poovan (பூவன்)",
        "season": "Annual (ஆண்டுப் பயிர்)",
        "sowing_date": sow_banana,
        "stage": "Vegetative Growth (இலை வளர்ச்சி பருவம்)",
        "expected_harvest": harvest_banana,
        "area_cultivated_acres": 2.0,
        "status": "active",
        "notes": "Drip fertigation applied weekly. Desuckering completed."
    }
    db_store.save_item("crops", crop_paddy)
    db_store.save_item("crops", crop_banana)

    # 3. Livestock
    cow_1 = {
        "id": "animal_tn01",
        "tag_id": "TN-01-LAKSHMI",
        "name": "Lakshmi (லட்சுமி)",
        "species": "cow",
        "breed": "Kangayam (காங்கேயம்)",
        "gender": "female",
        "age_years": 4.5,
        "lactation_number": 2,
        "daily_milk_avg": 9.5,
        "status": "pregnant",
        "notes": "Purebred Kangayam native cow. Calm temperament."
    }
    cow_2 = {
        "id": "animal_tn02",
        "tag_id": "TN-02-KAMALAM",
        "name": "Kamalam (கமலம்)",
        "species": "cow",
        "breed": "Jersey Cross (ஜெர்சி கலப்பினம்)",
        "gender": "female",
        "age_years": 3.5,
        "lactation_number": 1,
        "daily_milk_avg": 13.0,
        "status": "milking",
        "notes": "High yield milch cow. Yields 13-14 liters daily."
    }
    goat_1 = {
        "id": "animal_gt01",
        "tag_id": "GT-01-MEENA",
        "name": "Meena (மீனா)",
        "species": "goat",
        "breed": "Kanni Aadu (கன்னி ஆடு)",
        "gender": "female",
        "age_years": 2.0,
        "lactation_number": 1,
        "status": "pregnant",
        "notes": "Indigenous hardy goat from southern TN."
    }
    goat_2 = {
        "id": "animal_gt02",
        "tag_id": "GT-02-RAJA",
        "name": "Raja (ராஜா - கிடா)",
        "species": "goat",
        "breed": "Salem Black (சேலம் கருப்பு)",
        "gender": "male",
        "age_years": 2.5,
        "status": "healthy",
        "notes": "Breeding buck. Vigorous and healthy."
    }
    db_store.save_item("livestock", cow_1)
    db_store.save_item("livestock", cow_2)
    db_store.save_item("livestock", goat_1)
    db_store.save_item("livestock", goat_2)

    # 4. Breeding Records
    ai_date = (today - timedelta(days=125)).isoformat()
    breed_rec_1 = {
        "id": "breed_rec_lakshmi",
        "animal_id": "animal_tn01",
        "animal_tag": "TN-01-LAKSHMI",
        "event_type": "insemination",
        "date": ai_date,
        "semen_bull_info": "Kangayam Pedigree Bull #KG-402 (Erode Semen Station)",
        "technician": "Dr. Senthil, VAS Thiruvidaimarudur",
        "status": "active",
        "pd_confirmed": True,
        "notes": "PD confirmed positive at 65 days."
    }
    
    mating_date = (today - timedelta(days=88)).isoformat()
    breed_rec_2 = {
        "id": "breed_rec_meena",
        "animal_id": "animal_gt01",
        "animal_tag": "GT-01-MEENA",
        "event_type": "mating",
        "date": mating_date,
        "semen_bull_info": "Salem Black Buck (Raja)",
        "technician": "Natural service",
        "status": "active",
        "pd_confirmed": True,
        "notes": "Gestation progressing well. Due in approx 62 days."
    }
    db_store.save_item("breeding_records", breed_rec_1)
    db_store.save_item("breeding_records", breed_rec_2)

    # 5. Milk Records (Past 5 days for Kamalam)
    for d in range(5, -1, -1):
        log_date = (today - timedelta(days=d)).isoformat()
        db_store.save_item("milk_records", {
            "id": f"milk_log_tn02_{log_date}",
            "animal_id": "animal_tn02",
            "animal_tag": "TN-02-KAMALAM",
            "date": log_date,
            "morning_liters": 7.5,
            "evening_liters": 6.0,
            "total_liters": 13.5,
            "fat_pct": 4.3,
            "snf_pct": 8.6,
            "rate_per_liter": 38.5,
            "total_amount": round(13.5 * 38.5, 2),
            "buyer": "Aavin Milk Cooperative Society"
        })

    # 6. Financials
    fin_entries = [
        {"type": "expense", "category": "Seeds / நாற்று", "plot_id": "plot_cauvery_delta", "crop_id": "crop_cr1009_paddy", "amount": 3400, "date": (today - timedelta(days=48)).isoformat(), "desc": "CR-1009 Certified Paddy Seed bags"},
        {"type": "expense", "category": "Tractor & Machinery / உழவு கூலி", "plot_id": "plot_cauvery_delta", "crop_id": "crop_cr1009_paddy", "amount": 5200, "date": (today - timedelta(days=44)).isoformat(), "desc": "Cage wheel puddling & rotavator ploughing"},
        {"type": "expense", "category": "Labor / நடவுக் கூலி", "plot_id": "plot_cauvery_delta", "crop_id": "crop_cr1009_paddy", "amount": 7600, "date": (today - timedelta(days=40)).isoformat(), "desc": "Paddy transplanting labor (12 women laborers)"},
        {"type": "expense", "category": "Fertilizer / உரங்கள்", "plot_id": "plot_cauvery_delta", "crop_id": "crop_cr1009_paddy", "amount": 4500, "date": (today - timedelta(days=25)).isoformat(), "desc": "DAP 2 bags & Potash 1 bag basal dressing"},
        {"type": "expense", "category": "Cattle Feed / கால்நடை தீவனம்", "plot_id": "", "crop_id": "", "amount": 3800, "date": (today - timedelta(days=15)).isoformat(), "desc": "Cotton seed cake (பருத்திக் கொட்டை) & Wheat bran 2 bags"},
        {"type": "income", "category": "Crop Sale / பயிர் விற்பனை", "plot_id": "plot_cauvery_delta", "crop_id": "", "amount": 84000, "date": (today - timedelta(days=60)).isoformat(), "desc": "Previous Kuruvai Harvest 35 bags to Regulated Market"},
        {"type": "income", "category": "Milk Sale / பால் விற்பனை", "plot_id": "", "crop_id": "", "amount": 15600, "date": (today - timedelta(days=10)).isoformat(), "desc": "Aavin Milk Society Fortnightly payment"},
        {"type": "income", "category": "Livestock Sale / ஆடு விற்பனை", "plot_id": "", "crop_id": "", "amount": 17000, "date": (today - timedelta(days=20)).isoformat(), "desc": "Sale of 2 male goat kids (கிடா குட்டிகள்)"}
    ]
    for fin in fin_entries:
        db_store.save_item("financials", fin)

    print("[OK] Successfully seeded realistic Tamil Nadu agriculture & livestock data!")
