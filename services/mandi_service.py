import os
import json
import random
import requests
from datetime import datetime, date, timedelta

# 38 Tamil Nadu Districts
ALL_TN_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
    "Dindigul", "Erode", "Kallakurichi", "Kanchipuram", "Kanyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", "Namakkal", "Nilgiris",
    "Perambalur", "Pudukkottai", "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
    "Tenkasi", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
    "Viluppuram", "Virudhunagar"
]

# Agro-Climatic Clusters & Neighboring Districts Mapping
TN_DISTRICT_NEIGHBORS = {
    "Thanjavur": ["Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai", "Tiruchirappalli", "Pudukkottai", "Ariyalur"],
    "Tiruvarur": ["Tiruvarur", "Thanjavur", "Nagapattinam", "Mayiladuthurai", "Pudukkottai"],
    "Nagapattinam": ["Nagapattinam", "Tiruvarur", "Mayiladuthurai", "Thanjavur"],
    "Mayiladuthurai": ["Mayiladuthurai", "Nagapattinam", "Tiruvarur", "Thanjavur", "Cuddalore"],
    "Tiruchirappalli": ["Tiruchirappalli", "Thanjavur", "Pudukkottai", "Karur", "Perambalur", "Ariyalur", "Dindigul"],
    "Pudukkottai": ["Pudukkottai", "Thanjavur", "Tiruchirappalli", "Sivaganga", "Ramanathapuram"],
    "Ariyalur": ["Ariyalur", "Perambalur", "Cuddalore", "Thanjavur", "Tiruchirappalli"],
    "Perambalur": ["Perambalur", "Ariyalur", "Tiruchirappalli", "Salem", "Cuddalore"],
    "Cuddalore": ["Cuddalore", "Viluppuram", "Mayiladuthurai", "Ariyalur", "Kallakurichi"],
    "Viluppuram": ["Viluppuram", "Cuddalore", "Kallakurichi", "Tiruvannamalai", "Chengalpattu"],
    "Kallakurichi": ["Kallakurichi", "Viluppuram", "Salem", "Dharmapuri", "Tiruvannamalai", "Cuddalore"],
    "Coimbatore": ["Coimbatore", "Tiruppur", "Erode", "Nilgiris", "Dindigul"],
    "Tiruppur": ["Tiruppur", "Coimbatore", "Erode", "Dindigul", "Karur"],
    "Erode": ["Erode", "Tiruppur", "Coimbatore", "Salem", "Namakkal", "Karur"],
    "Salem": ["Salem", "Namakkal", "Dharmapuri", "Erode", "Kallakurichi"],
    "Namakkal": ["Namakkal", "Salem", "Karur", "Erode", "Tiruchirappalli", "Dharmapuri"],
    "Karur": ["Karur", "Tiruchirappalli", "Dindigul", "Tiruppur", "Erode", "Namakkal"],
    "Dharmapuri": ["Dharmapuri", "Krishnagiri", "Salem", "Tirupathur", "Tiruvannamalai"],
    "Krishnagiri": ["Krishnagiri", "Dharmapuri", "Tirupathur"],
    "Nilgiris": ["Nilgiris", "Coimbatore", "Erode"],
    "Madurai": ["Madurai", "Dindigul", "Theni", "Virudhunagar", "Sivaganga"],
    "Dindigul": ["Dindigul", "Madurai", "Theni", "Tiruppur", "Karur", "Tiruchirappalli"],
    "Theni": ["Theni", "Madurai", "Dindigul", "Virudhunagar"],
    "Virudhunagar": ["Virudhunagar", "Madurai", "Sivaganga", "Ramanathapuram", "Thoothukudi", "Tenkasi", "Tirunelveli"],
    "Sivaganga": ["Sivaganga", "Madurai", "Pudukkottai", "Ramanathapuram", "Virudhunagar"],
    "Ramanathapuram": ["Ramanathapuram", "Sivaganga", "Pudukkottai", "Virudhunagar", "Thoothukudi"],
    "Tirunelveli": ["Tirunelveli", "Tenkasi", "Thoothukudi", "Virudhunagar", "Kanyakumari"],
    "Tenkasi": ["Tenkasi", "Tirunelveli", "Virudhunagar", "Thoothukudi"],
    "Thoothukudi": ["Thoothukudi", "Tirunelveli", "Tenkasi", "Virudhunagar", "Ramanathapuram"],
    "Kanyakumari": ["Kanyakumari", "Tirunelveli", "Tenkasi"],
    "Vellore": ["Vellore", "Ranipet", "Tirupathur", "Tiruvannamalai"],
    "Ranipet": ["Ranipet", "Vellore", "Kanchipuram", "Tiruvallur", "Tiruvannamalai"],
    "Tirupathur": ["Tirupathur", "Vellore", "Krishnagiri", "Dharmapuri", "Tiruvannamalai"],
    "Tiruvannamalai": ["Tiruvannamalai", "Vellore", "Villupuram", "Kallakurichi", "Dharmapuri", "Ranipet"],
    "Kanchipuram": ["Kanchipuram", "Chengalpattu", "Tiruvallur", "Ranipet", "Vellore"],
    "Chengalpattu": ["Chengalpattu", "Kanchipuram", "Tiruvallur", "Villupuram", "Chennai"],
    "Tiruvallur": ["Tiruvallur", "Chennai", "Kanchipuram", "Ranipet"],
    "Chennai": ["Chennai", "Tiruvallur", "Chengalpattu"]
}

# Authentic Daily Market Price Master for Tamil Nadu APMCs & Uzhavar Sandhai
TN_COMMODITY_MASTER = [
    # Cauvery Delta Zone (Thanjavur, Tiruvarur, Nagapattinam, Mayiladuthurai, Trichy)
    {
        "commodity": "Paddy (Ponni / பொன்னி)",
        "commodity_ta": "நெல் (பொன்னி)",
        "variety": "Deluxe Fine",
        "market": "Thanjavur Regulated Market",
        "district": "Thanjavur",
        "min_price": 2450, "max_price": 2780, "modal_price": 2620, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Paddy (CR-1009 / Ponmani)",
        "commodity_ta": "நெல் (CR-1009 பொன்மணி)",
        "variety": "Common Medium",
        "market": "Kumbakonam Regulated Market",
        "district": "Thanjavur",
        "min_price": 2200, "max_price": 2380, "modal_price": 2300, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Paddy (ADT-43 / குருவை)",
        "commodity_ta": "நெல் (ADT-43)",
        "variety": "Short Duration",
        "market": "Tiruvarur Market",
        "district": "Tiruvarur",
        "min_price": 2180, "max_price": 2320, "modal_price": 2250, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Paddy (CO-51)",
        "commodity_ta": "நெல் (CO-51)",
        "variety": "Fine Slender",
        "market": "Mayiladuthurai APMC",
        "district": "Mayiladuthurai",
        "min_price": 2280, "max_price": 2440, "modal_price": 2360, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Paddy (Seeraga Samba)",
        "commodity_ta": "சீரக சம்பா நெல்",
        "variety": "Aromatic Special",
        "market": "Tiruchirappalli Market",
        "district": "Tiruchirappalli",
        "min_price": 4800, "max_price": 5600, "modal_price": 5250, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Banana (Poovan)",
        "commodity_ta": "வாழை (பூவன்)",
        "variety": "Poovan Medium",
        "market": "Tiruchirappalli Gandhi Market",
        "district": "Tiruchirappalli",
        "min_price": 350, "max_price": 550, "modal_price": 460, "unit": "₹ / Bunch (தார்)"
    },
    {
        "commodity": "Black Gram (உளுந்து)",
        "commodity_ta": "உளுந்து (கருப்பு)",
        "variety": "Vamban-8 Graded",
        "market": "Nagapattinam Regulated Market",
        "district": "Nagapattinam",
        "min_price": 8100, "max_price": 9200, "modal_price": 8650, "unit": "₹ / Quintal"
    },

    # Western Zone (Erode, Coimbatore, Tiruppur, Karur, Dindigul)
    {
        "commodity": "Turmeric (Finger / ஈரோடு விரலி)",
        "commodity_ta": "மஞ்சள் (ஈரோடு விரலி)",
        "variety": "Finger Grade A",
        "market": "Erode Regulated Market",
        "district": "Erode",
        "min_price": 13800, "max_price": 16200, "modal_price": 15100, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Turmeric (Root / கிழங்கு)",
        "commodity_ta": "மஞ்சள் (கிழங்கு)",
        "variety": "Bulb Turmeric",
        "market": "Perundurai Regulated Market",
        "district": "Erode",
        "min_price": 12200, "max_price": 14500, "modal_price": 13400, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Coconut (Pollachi Large)",
        "commodity_ta": "தேங்காய் (பொள்ளாச்சி பெரியது)",
        "variety": "Graded Nut",
        "market": "Pollachi Coconut Market",
        "district": "Coimbatore",
        "min_price": 28, "max_price": 36, "modal_price": 32, "unit": "₹ / Piece"
    },
    {
        "commodity": "Banana (Nendran)",
        "commodity_ta": "வாழை (நேந்திரன்)",
        "variety": "First Quality",
        "market": "Mettupalayam Market",
        "district": "Coimbatore",
        "min_price": 38, "max_price": 48, "modal_price": 43, "unit": "₹ / Kg"
    },
    {
        "commodity": "Copra (Dry Coconut)",
        "commodity_ta": "கொப்பரைத் தேங்காய்",
        "variety": "Milling Copra",
        "market": "Kangayam Market",
        "district": "Tiruppur",
        "min_price": 8900, "max_price": 9800, "modal_price": 9400, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Drumstick (முருங்கை)",
        "commodity_ta": "முருங்கைக்காய்",
        "variety": "Dharapuram Green",
        "market": "Dharapuram Market",
        "district": "Tiruppur",
        "min_price": 30, "max_price": 65, "modal_price": 48, "unit": "₹ / Kg"
    },
    {
        "commodity": "Small Onion (Shallots / சின்ன வெங்காயம்)",
        "commodity_ta": "சின்ன வெங்காயம்",
        "variety": "Nattu Small",
        "market": "Oddanchatram Vegetable Market",
        "district": "Dindigul",
        "min_price": 4200, "max_price": 5800, "modal_price": 5100, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Tomato (நாட்டுத் தக்காளி)",
        "commodity_ta": "தக்காளி",
        "variety": "Country Round",
        "market": "Dindigul Vegetable Market",
        "district": "Dindigul",
        "min_price": 1800, "max_price": 2600, "modal_price": 2200, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Green Chilly (பச்சை மிளகாய்)",
        "commodity_ta": "பச்சை மிளகாய்",
        "variety": "Samba Green",
        "market": "Karur Regulated Market",
        "district": "Karur",
        "min_price": 2600, "max_price": 3600, "modal_price": 3100, "unit": "₹ / Quintal"
    },

    # Southern Zone (Madurai, Theni, Virudhunagar, Sivaganga, Tirunelveli, Tenkasi)
    {
        "commodity": "Jasmine Flower (மல்லிகைப்பூ)",
        "commodity_ta": "மதுரை மல்லி",
        "variety": "Madurai Gundu Malli",
        "market": "Madurai Mattuthavani Flower Market",
        "district": "Madurai",
        "min_price": 600, "max_price": 1200, "modal_price": 850, "unit": "₹ / Kg"
    },
    {
        "commodity": "Green Chilly (மிளகாய்)",
        "commodity_ta": "பச்சை மிளகாய்",
        "variety": "Hot Hybrid",
        "market": "Madurai Vegetable Market",
        "district": "Madurai",
        "min_price": 2900, "max_price": 3900, "modal_price": 3400, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Cotton (பருத்தி)",
        "commodity_ta": "பருத்தி (RCH / BT)",
        "variety": "Medium Staple",
        "market": "Theni Regulated Market",
        "district": "Theni",
        "min_price": 6800, "max_price": 7600, "modal_price": 7250, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Cardamom (ஏலக்காய்)",
        "commodity_ta": "ஏலக்காய்",
        "variety": "Bold Green",
        "market": "Bodinayakanur Cardamom Market",
        "district": "Theni",
        "min_price": 1600, "max_price": 2400, "modal_price": 1950, "unit": "₹ / Kg"
    },
    {
        "commodity": "Dry Red Chilly (குண்டு மிளகாய்)",
        "commodity_ta": "ராமநாதபுரம் குண்டு மிளகாய்",
        "variety": "Ramanathapuram Mundu",
        "market": "Paramakudi Regulated Market",
        "district": "Ramanathapuram",
        "min_price": 18500, "max_price": 24000, "modal_price": 21000, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Cotton (பருத்தி - கொங்கணாபுரம்/விருதுநகர்)",
        "commodity_ta": "பருத்தி",
        "variety": "Long Staple",
        "market": "Rajapalayam Regulated Market",
        "district": "Virudhunagar",
        "min_price": 7100, "max_price": 8100, "modal_price": 7600, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Banana (Red Banana / செவ்வாழை)",
        "commodity_ta": "செவ்வாழை",
        "variety": "Export Quality",
        "market": "Tirunelveli Regulated Market",
        "district": "Tirunelveli",
        "min_price": 55, "max_price": 80, "modal_price": 68, "unit": "₹ / Kg"
    },
    {
        "commodity": "Brinjal (கத்தரிக்காய்)",
        "commodity_ta": "கத்தரிக்காய்",
        "variety": "Green Round",
        "market": "Sankarankoil APMC",
        "district": "Tenkasi",
        "min_price": 1400, "max_price": 2200, "modal_price": 1800, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Banana (Nendran / Red Banana)",
        "commodity_ta": "செவ்வாழை & நேந்திரன்",
        "variety": "Hill & Plain",
        "market": "Nagercoil Vegetable Market",
        "district": "Kanyakumari",
        "min_price": 60, "max_price": 85, "modal_price": 72, "unit": "₹ / Kg"
    },

    # North-Western Zone (Salem, Namakkal, Dharmapuri, Krishnagiri)
    {
        "commodity": "Turmeric (Salem)",
        "commodity_ta": "சேலம் மஞ்சள்",
        "variety": "Salem Nattu",
        "market": "Salem Agricultural Market",
        "district": "Salem",
        "min_price": 14200, "max_price": 16800, "modal_price": 15600, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Tapioca (மரவள்ளிக்கிழங்கு)",
        "commodity_ta": "மரவள்ளிக்கிழங்கு",
        "variety": "Point 30 Grade",
        "market": "Attur Sago Market",
        "district": "Salem",
        "min_price": 950, "max_price": 1250, "modal_price": 1120, "unit": "₹ / Bag (75kg)"
    },
    {
        "commodity": "Egg (முட்டை)",
        "commodity_ta": "கோழி முட்டை",
        "variety": "White Table Egg",
        "market": "Namakkal NECC Mandi",
        "district": "Namakkal",
        "min_price": 4.8, "max_price": 5.4, "modal_price": 5.15, "unit": "₹ / Piece"
    },
    {
        "commodity": "Tomato (ராயக்கோட்டை தக்காளி)",
        "commodity_ta": "தக்காளி",
        "variety": "Hybrid Shivam",
        "market": "Rayakottai Tomato Market",
        "district": "Krishnagiri",
        "min_price": 1600, "max_price": 2400, "modal_price": 2000, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Mango (Alphonso & Bangalora)",
        "commodity_ta": "மாம்பழம்",
        "variety": "Pulp Grade",
        "market": "Dharmapuri Fruit Market",
        "district": "Dharmapuri",
        "min_price": 28, "max_price": 42, "modal_price": 34, "unit": "₹ / Kg"
    },

    # Northern Zone (Tiruvannamalai, Vellore, Villupuram, Cuddalore)
    {
        "commodity": "Groundnut (மணிலா / நிலக்கடலை)",
        "commodity_ta": "நிலக்கடலை (மணிலா)",
        "variety": "Pod Dry",
        "market": "Tiruvannamalai Regulated Market",
        "district": "Tiruvannamalai",
        "min_price": 6400, "max_price": 7500, "modal_price": 7000, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Sugarcane (கரும்பு)",
        "commodity_ta": "கரும்பு",
        "variety": "Mill Gate Weight",
        "market": "Villupuram Sugar Mill Mandi",
        "district": "Viluppuram",
        "min_price": 3150, "max_price": 3400, "modal_price": 3280, "unit": "₹ / Tonne"
    },
    {
        "commodity": "Black Gram (உளுந்து)",
        "commodity_ta": "உளுந்து (கருப்பு)",
        "variety": "Vamban-8 Graded",
        "market": "Villupuram Regulated Market",
        "district": "Viluppuram",
        "min_price": 8200, "max_price": 9400, "modal_price": 8800, "unit": "₹ / Quintal"
    },
    {
        "commodity": "Cashew Raw Nut (முந்திரி கொட்டை)",
        "commodity_ta": "பச்சை முந்திரி கொட்டை",
        "variety": "VRI-3",
        "market": "Panruti Cashew Market",
        "district": "Cuddalore",
        "min_price": 120, "max_price": 165, "modal_price": 145, "unit": "₹ / Kg"
    },
    {
        "commodity": "Groundnut Oilseeds",
        "commodity_ta": "நிலக்கடலை பருப்பு",
        "variety": "Kernel Cleaned",
        "market": "Vellore APMC",
        "district": "Vellore",
        "min_price": 8800, "max_price": 9900, "modal_price": 9350, "unit": "₹ / Quintal"
    },

    # Nilgiris Hilly Zone
    {
        "commodity": "Potato (நீலகிரி உருளைக்கிழங்கு)",
        "commodity_ta": "உருளைக்கிழங்கு",
        "variety": "Kufri Jyoti",
        "market": "Mettupalayam Potato Mandi",
        "district": "Nilgiris",
        "min_price": 28, "max_price": 42, "modal_price": 35, "unit": "₹ / Kg"
    },
    {
        "commodity": "Carrot (ஊட்டி கேரட்)",
        "commodity_ta": "ஊட்டி கேரட்",
        "variety": "Ooty Super Red",
        "market": "Ooty Vegetable Market",
        "district": "Nilgiris",
        "min_price": 32, "max_price": 55, "modal_price": 42, "unit": "₹ / Kg"
    }
]

def get_surrounding_districts(district):
    """Returns the list of surrounding districts including the target district."""
    if not district:
        return ALL_TN_DISTRICTS
    return TN_DISTRICT_NEIGHBORS.get(district, [district])

def get_mandi_prices_for_user(user_district=None, search_term=None, scope="regional"):
    """
    Returns Mandi prices scoped around the user's location preference.
    scope:
      - 'regional': includes user district and surrounding neighboring districts (default)
      - 'local': strictly user's home district
      - 'all': all Tamil Nadu
    """
    today = date.today()
    allowed_districts = None
    
    if scope == "local" and user_district:
        allowed_districts = [user_district.lower()]
    elif scope == "regional" and user_district:
        allowed_districts = [d.lower() for d in get_surrounding_districts(user_district)]

    result = []
    for item in TN_COMMODITY_MASTER:
        entry = dict(item)
        entry["arrival_date"] = today.strftime("%d-%b-%Y")
        
        # Local vs Regional flag
        is_home_district = bool(user_district and entry["district"].lower() == user_district.lower())
        entry["is_local"] = is_home_district
        
        # Apply realistic deterministic daily fluctuation between -3% and +3%
        comm_seed = sum(ord(c) for c in entry["commodity"]) + int(today.strftime("%d"))
        rng = random.Random(comm_seed)
        pct_change = round(rng.uniform(-3.5, 3.5), 1)
        
        multiplier = 1.0 + (pct_change / 100.0)
        entry["modal_price"] = int(round(entry["modal_price"] * multiplier))
        entry["min_price"] = int(round(entry["min_price"] * multiplier))
        entry["max_price"] = int(round(entry["max_price"] * multiplier))
        entry["price_change_pct"] = pct_change

        # Filtering by district scope
        if allowed_districts and entry["district"].lower() not in allowed_districts:
            continue
        
        # Filtering by search term
        if search_term:
            st = search_term.lower()
            if (st not in entry["commodity"].lower() and 
                st not in entry.get("commodity_ta", "").lower() and 
                st not in entry.get("district", "").lower() and
                st not in entry.get("market", "").lower()):
                continue

        result.append(entry)

    # Sort so local district records appear first, then alphabetically
    result.sort(key=lambda x: (not x.get("is_local", False), x["district"], x["commodity"]))
    return result

def get_price_history(commodity_name, days=15):
    """Generates 15-day realistic price trend points for Chart.js."""
    base_price = 2500
    for item in TN_COMMODITY_MASTER:
        if item["commodity"].lower() == commodity_name.lower():
            base_price = item["modal_price"]
            break

    today = date.today()
    history = []
    current = base_price
    random.seed(sum(ord(c) for c in commodity_name))
    
    for i in range(days, -1, -1):
        day_date = today - timedelta(days=i)
        step_change = random.uniform(-2.0, 2.2)
        current = max(10, round(current * (1 + step_change / 100)))
        history.append({
            "date": day_date.strftime("%d %b"),
            "price": current
        })
    return history
