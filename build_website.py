import os
import json
import random
import re

OUTPUT_DIR = "output_metadata"
CONFIG_FILE = "config.js"
journal_headers = {
    "2017-08-07": {
        "date_display": "DAY 1 OF 16 • 07 AUGUST, 2017 • YIN Renlong (2026)",
        "title": "The Weight of Beginnings: Atlases, Strangers, and the Road out of Rome",
        "subtitle": "Departure from Rome, Lazio to Nepi, Lazio"
    },
    "2017-08-08": {
        "date_display": "DAY 2 OF 16 • 08 AUGUST, 2017",
        "title": "Vulnerability and Providence: Forest Fires and the Land of Others",
        "subtitle": "Departure from Nepi, Lazio to Montefiascone, Lazio"
    },
    "2017-08-09": {
        "date_display": "DAY 3 OF 16 • 09 AUGUST, 2017",
        "title": "Bureaucracy and Grace: Rejection at the Summit, Feast in the Valley",
        "subtitle": "Departure from Montefiascone, Lazio to San Quirico d'Orcia, Tuscany"
    },
    "2017-08-10": {
        "date_display": "DAY 4 OF 16 • 10 AUGUST, 2017",
        "title": "Navigating the Unseen Boundaries: Highway Tensions and Siena's Rains",
        "subtitle": "Departure from San Quirico d'Orcia, Tuscany to Tavarnelle Val di Pesa, Tuscany"
    },
    "2017-08-11": {
        "date_display": "DAY 5 OF 16 • 11 AUGUST, 2017",
        "title": "Exhaustion and Isolation: The Bare Earth and the Chill of Florence",
        "subtitle": "Departure from Tavarnelle Val di Pesa, Tuscany to Firenze, Tuscany"
    },
    "2017-08-12": {
        "date_display": "DAY 6 OF 16 • 12 AUGUST, 2017",
        "title": "The Brink of Hypothermia: Art, Altitude, and the Lifesaving Blanket",
        "subtitle": "Departure from Firenze, Tuscany to Suviana, Emilia-Romagna"
    },
    "2017-08-13": {
        "date_display": "DAY 7 OF 16 • 13 AUGUST, 2017",
        "title": "Moorish Mirages and Bolognese Hospitality: The Architecture of Welcome",
        "subtitle": "Departure from Suviana, Emilia-Romagna to Bologna, Emilia-Romagna"
    },
    "2017-08-14": {
        "date_display": "DAY 8 OF 16 • 14 AUGUST, 2017",
        "title": "The Look of the Drifter: Misread Signals in the Empty City",
        "subtitle": "Departure from Bologna, Emilia-Romagna to Modena, Emilia-Romagna"
    },
    "2017-08-15": {
        "date_display": "DAY 9 OF 16 • 15 AUGUST, 2017",
        "title": "Ferragosto in the Void: Speed, Stasis, and a Solitary Meal",
        "subtitle": "Departure from Modena, Emilia-Romagna to Parma, Emilia-Romagna"
    },
    "2017-08-16": {
        "date_display": "DAY 10 OF 16 • 16 AUGUST, 2017",
        "title": "Betrayal and Sanctuary: A Ghosted Arrival and the Sisters of Reparation",
        "subtitle": "Departure from Parma, Emilia-Romagna to Varese, Lombardy"
    },
    "2017-08-17": {
        "date_display": "DAY 11 OF 16 • 17 AUGUST, 2017",
        "title": "The Invisible Wall: Borders, Belonging, and the Distribution of Grace",
        "subtitle": "Departure from Varese, Lombardy to Porto Ceresio, Lombardy (Swiss Border)"
    },
    "2017-08-18": {
        "date_display": "DAY 12 OF 16 • 18 AUGUST, 2017",
        "title": "Urban Drifting: Navigating the Metropolis and the Convent's Alarms",
        "subtitle": "Departure from Varese, Lombardy to Abbiategrasso, Lombardy"
    },
    "2017-08-19": {
        "date_display": "DAY 13 OF 16 • 19 AUGUST, 2017",
        "title": "The Leap of Faith: A Late-Night Bus and the Philosophy of Strangers",
        "subtitle": "Departure from Abbiategrasso, Lombardy to Capiago Intimiano, Lombardy"
    },
    "2017-08-20": {
        "date_display": "DAY 14 OF 16 • 20 AUGUST, 2017",
        "title": "Gravity and Grace: The Thrill of the Descent and the Warmth of the Hearth",
        "subtitle": "Departure from Capiago Intimiano, Lombardy to Cogliate, Lombardy"
    },
    "2017-08-21": {
        "date_display": "DAY 15 OF 16 • 21 AUGUST, 2017",
        "title": "The Epiphany of the Endpoint: Recognizing When to Stop",
        "subtitle": "Departure from Cogliate, Lombardy to Bergamo, Lombardy"
    },
    "2017-08-22": {
        "date_display": "DAY 16 OF 16 • 22 AUGUST, 2017",
        "title": "The Return: Steel Tracks and the Assimilation of the Road",
        "subtitle": "Departure from Bergamo, Lombardy to Rome, Lazio"
    }
}

# MANUAL LAYOUT OVERRIDES (Grouped by Layout Type)
# This is ONLY for interactive map sliders. 
# (To put photos in the 'prose' section, use the tags inside generated_prose.md instead!)

manual_layouts = {
    "immersive-left": [
        "_MG_0082-3.jpg",   # National Geographic cinematic parallax
        "_MG_0119-2.jpg",   
        "_MG_0155-3.jpg",   
        "_MG_0240-2.jpg",   
        "_MG_0104-4.jpg",
        "_MG_0269.jpg"
    ],
    "split": [
        # Text on left, 50% Photo on right
    ],
    "floating-card": [
        # Pure white box, text on top, 1:1 Square photo on bottom
    ],
    "media-card": [
        # Off-white box, 16:10 Photo on top, text on bottom
    ]
}

def get_photo_caption(day_folder, filename):
    """Helper to extract Location and Time from the photo's JSON"""
    json_path = os.path.join(OUTPUT_DIR, day_folder, f"{filename}.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            loc = data.get("location_name", "Unknown Location")
            time = data.get("time", "")
            return f"{loc} • {time}"
    return filename

def parse_prose_md_into_chunks(filepath, day_folder, used_images_list):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read().strip()
    
    # Flawless regex split: Splits right BEFORE a '## ' without consuming or duplicating it
    raw_sections = re.split(r'\n(?=## )', raw_text)
    chunks = []
    
    for section in raw_sections:
        section = section.strip()
        if not section: continue
            
        html = ""
        paragraphs = section.split('\n\n')
        
        for p in paragraphs:
            p = p.strip()
            if not p: continue
            
            # --- THE WAVE BREAK ---
            if p == '---' or p == '***':
                html += '<hr class="wavy-divider">\n'
                continue
            
            # --- THE REGEX TYPESETTER ---
            img_match = re.match(r'^!\[(.*?)\]\((.*?)\)$', p)
            
            if img_match:
                layout_tag = img_match.group(1).strip()
                filenames_raw = img_match.group(2).strip()
                
                # Handle Diptychs (Inline or Outset)
                if " | " in filenames_raw:
                    file1, file2 = [f.strip() for f in filenames_raw.split('|')]
                    used_images_list.extend([file1, file2])
                    web_path1, web_path2 = f"images/{day_folder}/{file1}", f"images/{day_folder}/{file2}"
                    cap1, cap2 = get_photo_caption(day_folder, file1), get_photo_caption(day_folder, file2)
                    
                    wrapper_class = "prose-outset-diptych" if layout_tag == "OUTSET_DIPTYCH" else "prose-diptych"
                    
                    html += f'''<div class="{wrapper_class}">
                        <figure><img src="{web_path1}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {cap1}</figcaption></figure>
                        <figure><img src="{web_path2}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {cap2}</figcaption></figure>
                    </div>\n'''
                
                # Handle Single Images
                else:
                    filename = filenames_raw
                    used_images_list.append(filename)
                    web_path = f"images/{day_folder}/{filename}"
                    caption = get_photo_caption(day_folder, filename)
                    
                    if layout_tag == "FULL_BLEED":
                        html += f'<figure class="prose-full-bleed"><img src="{web_path}" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    elif layout_tag == "OUTSET":
                        html += f'<figure class="prose-outset"><img src="{web_path}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    elif layout_tag == "HANGING_LEFT":
                        html += f'<figure class="prose-hanging-left"><img src="{web_path}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    elif layout_tag == "HANGING_RIGHT":
                        html += f'<figure class="prose-hanging-right"><img src="{web_path}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    elif layout_tag == "HANGING_LEFT_PORTRAIT":
                        html += f'<figure class="prose-hanging-left portrait-crop"><img src="{web_path}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    elif layout_tag == "HANGING_RIGHT_PORTRAIT":
                        html += f'<figure class="prose-hanging-right portrait-crop"><img src="{web_path}" class="lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
                    else:
                        html += f'<figure class="prose-inline-container"><img src="{web_path}" class="prose-inline-img lightbox-trigger" loading="lazy"><figcaption class="prose-caption">📍 {caption}</figcaption></figure>\n'
            
            # Flawless Header parsing
            elif p.startswith('## '): 
                clean_header = p.replace('## ', '', 1).strip()
                html += f'<h2>{clean_header}</h2>\n'
            elif p.startswith('# '): 
                clean_header = p.replace('# ', '', 1).strip()
                html += f'<h2>{clean_header}</h2>\n'
            # Convert standard text (and parse italics/bold!)
            else: 
                # 1. Convert **bold** to <strong>bold</strong>
                p = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p)
                # 2. Convert *italics* to <em>italics</em>
                p = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p)
                
                html += f'<p>{p}</p>\n'
                
        chunks.append(html.replace("`", "\\`")) 
        
    return chunks

def build():
    print("🏗️ Building ArcGIS-Style Mixed Media Website...")
    days = sorted([d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))])
    
    # Injecting the ArcGIS "Modern Antique" style with the secured API Key
    config_js = "var config = {\n    style: 'https://basemapstyles-api.arcgis.com/arcgis/rest/services/styles/v2/styles/arcgis/modern-antique?token=AAPTaa1kA0ARrHMCH2C6tcgEMRQ..IkmF6XP3uFeBYXC6loyslnoHUlE7TqPqnZ3qu_yIc37szmRzVjSwm1m6BJZ2H73ZMWY-QUKN2DKkj5scdyv7PT3qBbiJgYtyh0ugvE51XwGLWdi6bVIHUQzh3pYFkaFbklDnnX2eUn6vte0mPLBHJ6FGYH4hNpNeVCvS_PuJN8BrTrFmmTu3-BjlxItryiyzPv8ftQQF68Ebh0iznCdg4midvtYi_lWsItIF28xOuPi38Wl2ygduAT1_1mGBC5SI',\n    chapters: [\n"
    
    random.seed("kinesis-praxis-final")
    global_idx = 0
    prev_layout = ""

    # --- NEW: Translates your grouped lists into a fast lookup map ---
    override_map = {}
    for layout_name, photo_list in manual_layouts.items():
        for photo in photo_list:
            override_map[photo] = layout_name
    
    for day_index, day in enumerate(days):
        day_dir = os.path.join(OUTPUT_DIR, day)
        img_dir = f"images/{day}"
        
        narratives_path = os.path.join(day_dir, "global_narratives.json")
        if not os.path.exists(narratives_path): continue
            
        with open(narratives_path, "r", encoding="utf-8") as f:
            narratives = json.load(f)
            
        all_photo_jsons = sorted([f for f in os.listdir(day_dir) if f.endswith(".jpg.json")])
        
        # 1. Determine Initial GPS & First Photo for the Day Cover
        current_gps = "[12.4922, 41.8902]"
        cover_image = ""
        if len(all_photo_jsons) > 0:
            with open(os.path.join(day_dir, all_photo_jsons[0]), "r", encoding="utf-8") as f:
                first_photo_data = json.load(f)
                current_gps = first_photo_data.get("gps_coordinates", current_gps)
                cover_image = f"{img_dir}/{first_photo_data['filename']}"

        # MANUAL OVERRIDE: If 'cover.jpg' exists, use it instead!
        if os.path.exists(os.path.join(f"images/{day}", "cover.jpg")):
            cover_image = f"{img_dir}/cover.jpg"

        # Fetch the beautiful title, subtitle, and kicker from the dictionary
        day_headers = journal_headers.get(day, {
            "date_display": f"DAY {day_index + 1} • {day}",
            "title": f"Day {day_index + 1}", 
            "subtitle": "The Journey Continues"
        })
        
        # Extract and escape any potential backticks
        cover_kicker = day_headers["date_display"].replace("`", "\\`")
        cover_title = day_headers["title"].replace("`", "\\`")
        cover_subtitle = day_headers["subtitle"].replace("`", "\\`")

        # --- INJECT DAY COVER (Visual Transition) ---
        # Note: Using backticks (`) for kicker and title to safely handle apostrophes like "d'Orcia"
        config_js += f"""        {{
            id: 'chapter-{global_idx}',
            date: '{day}',
            title: `{cover_title}`,
            kicker: `{cover_kicker}`,
            image: '{cover_image}',
            layout: 'cover',
            description: `<p class="cover-subtitle">{cover_subtitle}</p>`,
            location: {{ center: {current_gps}, zoom: 11, pitch: 45, bearing: 0 }}
        }},
"""
        global_idx += 1
        prev_layout = "cover"

        # 2. THE DEDUPLICATION TRACKER
        used_prose_images = []

        # 3. GET PROSE CHUNKS
        prose_chunks = []
        prose_path = os.path.join(day_dir, "generated_prose.md")
        if os.path.exists(prose_path):
            prose_chunks = parse_prose_md_into_chunks(prose_path, day, used_prose_images)

        # 4. FILTER THE SLIDER QUEUE
        photo_jsons = []
        for p_json in all_photo_jsons:
            with open(os.path.join(day_dir, p_json), "r", encoding="utf-8") as f:
                filename = json.load(f)["filename"]
            if filename not in used_prose_images:
                photo_jsons.append(p_json)

        # 5. THE INTERLEAVING LOOP
        while prose_chunks or photo_jsons:
            
            if prose_chunks:
                chunk_html = prose_chunks.pop(0)
                config_js += f"""        {{
            id: 'chapter-{global_idx}',
            date: '{day}',
            title: '',
            image: '',
            layout: 'prose',
            description: `{chunk_html}`,
            location: {{ center: {current_gps}, zoom: 11, pitch: 20, bearing: 0 }}
        }},
"""
                global_idx += 1
                prev_layout = "prose"

# --- B. INJECT 1 TO 3 MAP/PHOTO CARDS ---
            if photo_jsons:
                num_photos_to_show = random.randint(1, 3) 
                if not prose_chunks:
                    num_photos_to_show = len(photo_jsons)
                    
                for _ in range(num_photos_to_show):
                    if not photo_jsons: break
                    
                    p_json = photo_jsons.pop(0)
                    with open(os.path.join(day_dir, p_json), "r", encoding="utf-8") as f:
                        r = json.load(f)
                        
                    filename = r["filename"]
                    desc = narratives.get(filename, "Narrative missing.").replace("`", "\\`")
                    current_gps = r.get("gps_coordinates", current_gps)
                    
                    # THE FIX 1: Sanitize the title
                    title = r.get("location_name", filename).replace("`", "\\`")
                    
                    # --- NEW: MANUAL OVERRIDE CHECK ---
                    # We check the new override_map we built at the top!
                    if filename in override_map:
                        layout_type = override_map[filename]
                        prev_layout = layout_type
                    else:
                        # If not overridden, let the frozen random seed decide
                        valid_choices = ["floating-card"] * 4 + ["media-card"] * 4 + ["split"] * 2 + ["immersive-left"] * 2
                        if prev_layout in ["split", "prose", "cover", "immersive-left"]:
                            valid_choices = ["floating-card", "media-card"]
                            
                        layout_type = random.choice(valid_choices)
                        prev_layout = layout_type
                        
            # THE FIX 2: Use backticks (`) around {title} instead of single quotes (')
                    config_js += f"""        {{
            id: 'chapter-{global_idx}',
            date: '{day}',
            title: `{title}`,
            image: '{img_dir}/{filename}',
            layout: '{layout_type}',
            description: `<p>{desc}</p>`,
            location: {{ center: {current_gps}, zoom: 14, pitch: 60, bearing: 0 }}
        }},
"""
                    global_idx += 1

    config_js += "    ]\n};\n"
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_js)

    print(f"🎉 Successfully stitched {len(days)} days into {CONFIG_FILE}!")

if __name__ == "__main__":
    build()