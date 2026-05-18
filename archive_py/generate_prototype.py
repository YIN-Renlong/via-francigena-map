import os
import json
import base64
import asyncio
import httpx
import exifread
import xml.etree.ElementTree as ET
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
MODEL = os.getenv("DEPLOYMENT_NAME")

IMAGE_DIR = "images/2017-08-07"
JSON_DIR = "output_metadata/2017-08-07"
KML_FILE = "kml_raw/Cyclemeter-Cycle-20170807-1024.kml"

os.makedirs(JSON_DIR, exist_ok=True)

DAY_1_DIARY = """
2017-08-07 Rome to Nepi 
回忆：这是第一天出发，还算顺利，晚上在一个AirBNB睡觉，Adriana接待了我，这是我唯一一次去住BNB，因为我说我是Gregorian毕业的，而Adriana也是LUMSA毕业的，这样她似乎才选择接待了我。我感觉那时候，意大利的有一种对外国人不太照顾的气氛...
总体来说，那天还顺利，除了在中途我把我的自行车靠在了一辆汽车上（就是在_MG_0056-3.jpg那里），然后女主人凶了我，说我不应该把自行车靠在她的车上。我当时意大利语还不算熟练，具体不记得说什么了， 应该说的大意是“这里有这么多的位置，为什么你偏偏靠在我的车上”，那时候真窝火。我走的时候也对她做了一个意大利手🤌 的手势。
我还放了一本书在她家里，是意大利当年的地图集。很重，我说会罗马了再去拿。但这一晃就8年了，我还没有回去拿这本书。
"""

def get_photo_clock_time(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        for tag_name in ['EXIF DateTimeOriginal', 'Image DateTime', 'EXIF DateTimeDigitized']:
            if tag_name in tags:
                try: return datetime.strptime(str(tags[tag_name]), "%Y:%m:%d %H:%M:%S")
                except ValueError: continue
    return None

def get_kml_gps_track(kml_path):
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        ns = {'abvio': 'http://www.abvio.com/xmlschemas/1'}
        json_meta = json.loads(root.find('.//abvio:json', ns).text)
        telemetry = json.loads(root.find('.//abvio:jsonData', ns).text)
        
        start_str = json_meta.get("startTimeISO8601") or json_meta.get("run", {}).get("startTimeISO8601")
        kml_clock_start = datetime.strptime(start_str[:19], "%Y-%m-%dT%H:%M:%S")
        
        track_points = []
        for i in range(len(telemetry['timeOffset'])):
            track_points.append({
                'time': kml_clock_start + timedelta(seconds=telemetry['timeOffset'][i]),
                'lat': telemetry['latitude'][i],
                'lon': telemetry['longitude'][i]
            })
        return track_points
    except Exception: return []

def sync_photo_to_gps(photo_time, track_points):
    if not photo_time or not track_points: return None
    closest_gps = min(track_points, key=lambda p: abs(p['time'] - photo_time))
    if abs(closest_gps['time'] - photo_time).total_seconds() <= 2700: return closest_gps
    return None

def encode_image(image_path):
    with open(image_path, "rb") as image_file: return base64.b64encode(image_file.read()).decode("utf-8")

async def get_location_data(client, lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18"
        headers = {"User-Agent": "KinesisPraxis/1.0"}
        resp = await client.get(url, headers=headers)
        data = resp.json()
        await asyncio.sleep(1.1) 
        
        short_title = "Via Francigena, Italy"
        if "address" in data:
            addr = data["address"]
            local = addr.get("road") or addr.get("pedestrian") or addr.get("square") or addr.get("amenity")
            district = addr.get("neighbourhood") or addr.get("suburb") or addr.get("village")
            city = addr.get("city") or addr.get("town")
            parts = [p for p in [local, district, city] if p]
            if parts: short_title = ", ".join(parts[:2])
            
        return short_title, data.get("display_name", "Unknown rural area")
    except: return "Via Francigena, Italy", "Unknown location"

# --- PASS 1: VISUAL EXTRACTION ONLY ---
async def process_image_visuals(client, filename, kml_points):
    image_path = os.path.join(IMAGE_DIR, filename)
    json_path = os.path.join(JSON_DIR, f"{filename}.json")
    
    photo_time = get_photo_clock_time(image_path)
    time_str = photo_time.strftime("%H:%M") if photo_time else "Unknown Time"
    
    gps_point = sync_photo_to_gps(photo_time, kml_points)
    if gps_point:
        gps_coords = f"[{gps_point['lon']:.5f}, {gps_point['lat']:.5f}]"
        lat, lon = gps_point['lat'], gps_point['lon']
    else:
        gps_coords, lat, lon = "[12.4922, 41.8902]", 41.8902, 12.4922

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    short_title, rich_context = await get_location_data(client, lat, lon)
    print(f"🌍 Pass 1: Scanning {filename} at {time_str}...")
    
    base64_image = encode_image(image_path)
    headers = { "api-key": API_KEY, "Content-Type": "application/json" }
    
    system_prompt = """You are a visual data extractor. Look at the photo.
Return a JSON object with EXACTLY these two keys:
{
    "dc_description": "Strict, objective description of objects, lighting, and composition.",
    "novel_visual_observations": "1-2 empirical details about the terrain, weather, or bicycle."
}"""

    payload = {
        "model": MODEL,
        "response_format": { "type": "json_object" },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract visual data."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    }

    try:
        response = await client.post(ENDPOINT, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        result_json = json.loads(response.json()["choices"][0]["message"]["content"])
        
        result_json.update({
            "filename": filename,
            "time": time_str,
            "gps_coordinates": gps_coords,
            "location_name": short_title,
            "rich_context": rich_context
        })
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_json, f, indent=4, ensure_ascii=False)
        return result_json
    except Exception as e:
        print(f"❌ Error on {filename}: {e}")
        return None

# --- PASS 2: THE GLOBAL STORYTELLER (NOW WITH CACHING!) ---
async def generate_global_narrative(client, all_photo_data):
    # Check if we already wrote the story!
    cache_path = os.path.join(JSON_DIR, "global_narratives.json")
    if os.path.exists(cache_path):
        print("⏭️  Skipped AI: Global story already written. Loading from cache...")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print("\n🖋️ Pass 2: AI is writing the cohesive global narrative...")
    
    # Compile the timeline for the AI
    timeline_str = ""
    for data in all_photo_data:
        timeline_str += f"- File: {data['filename']} | Time: {data['time']} | Location: {data['location_name']}\n  Visuals: {data['novel_visual_observations']}\n\n"

    system_prompt = f"""You are an expert academic auto-ethnographer. 
You are writing a continuous, beautifully flowing scrollytelling exhibition for Day 1 of a bicycle journey.

AUTHOR'S DIARY FOR THE DAY: 
{DAY_1_DIARY}

TIMELINE OF PHOTOS TAKEN:
{timeline_str}

YOUR TASK:
Write a perfectly cohesive narrative. You must provide exactly one 70-word paragraph for EACH photo file listed above.
- Make it flow like a novel. Do NOT repeat phrases like "At this time" or "In this photo".
- Let the story progress organically from morning to night.
- Merge the diary's psychological friction (the car argument, Adriana, isolation) with the visual timeline.

Return a JSON object where the keys are the filenames, and the values are the paragraphs:
{{
    "filename1.jpg": "Paragraph text...",
    "filename2.jpg": "Paragraph text..."
}}"""

    payload = {
        "model": MODEL,
        "response_format": { "type": "json_object" },
        "messages": [{"role": "system", "content": system_prompt}]
    }

    try:
        headers = { "api-key": API_KEY, "Content-Type": "application/json" }
        response = await client.post(ENDPOINT, headers=headers, json=payload, timeout=90.0)
        response.raise_for_status()
        
        narratives = json.loads(response.json()["choices"][0]["message"]["content"])
        
        # SAVE IT SO WE NEVER HAVE TO WRITE IT AGAIN!
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(narratives, f, indent=4, ensure_ascii=False)
            
        return narratives
    except Exception as e:
        print(f"❌ Storyteller Error: {e}")
        return {}


async def main():
    print("🚀 Starting Kinesis & Praxis AI Co-Researcher...")
    kml_points = get_kml_gps_track(KML_FILE)
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    
    async with httpx.AsyncClient() as client:
        results = []
        for img in images:
            res = await process_image_visuals(client, img, kml_points)
            if res: results.append(res)
            
        narratives = await generate_global_narrative(client, results)
                
    # --- THIS SECTION IS NOW CORRECTLY INDENTED ---
    print(f"\n📝 Compiling final config.js with ArcGIS sidecar layouts...")
    config_js = "var config = {\n    style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',\n    chapters: [\n"
    
    # We now only use two elegant layouts matching ArcGIS StoryMaps
    available_layouts = ["sidecar-map", "sidecar-photo"]
    prev_layout = ""
    
    for idx, r in enumerate(results):
        filename = r["filename"]
        desc = narratives.get(filename, "Narrative missing.").replace("`", "\\`")
        gps = r.get("gps_coordinates", "[12.4922, 41.8902]")
        title = r.get("location_name", filename)
        
        # --- ARCGIS PROCEDURAL PACING ---
        if idx == 0:
            layout_type = "sidecar-photo" # Open with a beautiful full-screen photo!
        else:
            # We want mostly Maps, with beautiful full-screen photos sprinkled in occasionally
            valid_choices = ["sidecar-map"] * 3 + ["sidecar-photo"] 
            
            # Never put two full-screen photos back-to-back
            if prev_layout == "sidecar-photo":
                valid_choices = ["sidecar-map"]
                
            layout_type = random.choice(valid_choices)
            
        prev_layout = layout_type 
        
        config_js += f"""        {{
            id: 'chapter-{idx}',
            title: '{title}',
            image: '{IMAGE_DIR}/{filename}',
            layout: '{layout_type}',
            description: `{desc}`,
            location: {{
                center: {gps},
                zoom: 14, pitch: 60, bearing: 0
            }}
        }},
"""
    config_js += "    ]\n};\n"
    with open("config.js", "w", encoding="utf-8") as f:
        f.write(config_js)
    print("🎉 Done! Open index.html to see the ArcGIS aesthetic.")

if __name__ == "__main__":
    asyncio.run(main())