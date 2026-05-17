import os
import json
import base64
import asyncio
import httpx
import exifread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load Azure credentials
load_dotenv()
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
MODEL = os.getenv("DEPLOYMENT_NAME")

# EXACT FOLDERS
IMAGE_DIR = "images/2017-08-07"
JSON_DIR = "output_metadata/2017-08-07"
KML_FILE = "kml_raw/Cyclemeter-Cycle-20170807-1024.kml"

# Create the JSON folder if it doesn't exist
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
                try:
                    return datetime.strptime(str(tags[tag_name]), "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    continue
    return None

def get_kml_gps_track(kml_path):
    try:
        tree = ET.parse(kml_path)
        root = tree.getroot()
        ns = {'abvio': 'http://www.abvio.com/xmlschemas/1'}
        
        json_meta_elem = root.find('.//abvio:json', ns)
        json_data_elem = root.find('.//abvio:jsonData', ns)
        
        if json_meta_elem is None or json_data_elem is None:
            return []
            
        json_meta = json.loads(json_meta_elem.text)
        telemetry = json.loads(json_data_elem.text)
        
        start_str = json_meta.get("startTimeISO8601")
        if not start_str and "run" in json_meta:
            start_str = json_meta["run"].get("startTimeISO8601")
            
        if not start_str:
            return []
            
        kml_clock_start = datetime.strptime(start_str[:19], "%Y-%m-%dT%H:%M:%S")
        
        track_points = []
        for i in range(len(telemetry['timeOffset'])):
            current_clock_time = kml_clock_start + timedelta(seconds=telemetry['timeOffset'][i])
            track_points.append({
                'time': current_clock_time,
                'lat': telemetry['latitude'][i],
                'lon': telemetry['longitude'][i]
            })
        print(f"✅ KML Loaded: {len(track_points)} GPS points found.")
        return track_points
    except Exception as e:
        print(f"❌ KML Parsing Error: {e}")
        return []

def sync_photo_to_gps(photo_time, track_points, filename):
    if not photo_time or not track_points:
        return None
    closest_gps = min(track_points, key=lambda p: abs(p['time'] - photo_time))
    seconds_diff = abs(closest_gps['time'] - photo_time).total_seconds()
    if seconds_diff <= 2700:
        return f"[{closest_gps['lon']:.5f}, {closest_gps['lat']:.5f}]"
    return None

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def process_image(client, filename, kml_points):
    image_path = os.path.join(IMAGE_DIR, filename)
    json_path = os.path.join(JSON_DIR, f"{filename}.json")
    
    # --- 1. PROPER CACHE CHECK ---
    # Looks inside output_metadata/2017-08-07/
    if os.path.exists(json_path):
        print(f"⏭️  Skipped AI: {filename}.json already exists in metadata folder.")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 2. CRASH PROTECTION ---
    if not os.path.exists(image_path):
        print(f"⚠️ Warning: {filename} was moved. Skipping.")
        return None

    # --- 3. GEO-SYNC ---
    photo_time = get_photo_clock_time(image_path)
    gps_coords = sync_photo_to_gps(photo_time, kml_points, filename)
    
    if not gps_coords:
        if kml_points: gps_coords = f"[{kml_points[0]['lon']:.5f}, {kml_points[0]['lat']:.5f}]"
        else: gps_coords = "[12.4922, 41.8902]"

    print(f"📍 {filename} synced to {gps_coords}")

    # --- 4. AI ANALYSIS ---
    print(f"🧠 AI analyzing {filename}...")
    base64_image = encode_image(image_path)
    headers = { "api-key": API_KEY, "Content-Type": "application/json" }
    
    system_prompt = f"""You are an expert visual anthropologist.
Look at the attached photograph, and read the author's diary for this day:
DIARY: {DAY_1_DIARY}

Return a JSON object with EXACTLY these three keys:
{{
    "dc_description": "Strict, objective museum-grade description of the image content only.",
    "novel_visual_observations": "List 1-2 empirical details you noticed in the photo that add context to the diary.",
    "storytelling_narrative": "A beautifully written, 70-word first-person paragraph in English. Merge the visual reality of the photo with the psychological reality of the diary. Focus on themes of somatic friction, isolation, or sociology."
}}"""

    payload = {
        "model": MODEL,
        "response_format": { "type": "json_object" },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": f"Analyze this image: {filename}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    }

    try:
        response = await client.post(ENDPOINT, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        
        result_json = json.loads(response.json()["choices"][0]["message"]["content"])
        result_json["gps_coordinates"] = gps_coords
        result_json["filename"] = filename
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result_json, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Saved {json_path}\n")
        return result_json
        
    except Exception as e:
        print(f"❌ Error on {filename}: {e}\n")
        return None

async def main():
    print("🚀 Starting Kinesis & Praxis AI Co-Researcher...")
    kml_points = get_kml_gps_track(KML_FILE)
    
    # Only grab JPGs from the strict Day 1 folder
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    
    async with httpx.AsyncClient() as client:
        results = []
        for img in images:
            res = await process_image(client, img, kml_points)
            if res:
                results.append(res)
                
    print(f"\n📝 Generating config.js with {len(results)} chapters...")
    config_js = "var config = {\n    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',\n    chapters: [\n"
    
    for idx, r in enumerate(results):
        desc = r.get("storytelling_narrative", "").replace("`", "\\`")
        filename = r.get("filename", images[idx])
        gps = r.get("gps_coordinates", "[12.4922, 41.8902]")
        
        config_js += f"""        {{
            id: 'chapter-{idx}',
            title: '{filename}',
            image: '{IMAGE_DIR}/{filename}',
            description: `{desc}`,
            location: {{
                center: {gps},
                zoom: 15, pitch: 45, bearing: 0
            }}
        }},
"""
    config_js += "    ]\n};\n"
    
    with open("config.js", "w", encoding="utf-8") as f:
        f.write(config_js)
    
    print("🎉 Done! Website configuration updated.")

if __name__ == "__main__":
    asyncio.run(main())