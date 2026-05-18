import os
import sys
import json
import base64
import asyncio
import httpx
import exifread
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
MODEL = os.getenv("DEPLOYMENT_NAME")

if len(sys.argv) < 2:
    print("❌ Error: Please provide a date. Example: python3 process_day.py 2017-08-07")
    sys.exit(1)

TARGET_DATE = sys.argv[1] # e.g., "2017-08-07"
IMAGE_DIR = f"images/{TARGET_DATE}"
JSON_DIR = f"output_metadata/{TARGET_DATE}"
MEMORY_FILE = f"{IMAGE_DIR}/memory.md"

os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs("geojson", exist_ok=True)

# 1. READ THE SECURE DIARY
if not os.path.exists(MEMORY_FILE):
    print(f"❌ Error: Could not find {MEMORY_FILE}")
    sys.exit(1)
with open(MEMORY_FILE, "r", encoding="utf-8") as f:
    DAY_DIARY = f.read()

# 2. AUTOMATICALLY FIND THE MATCHING KML FILE
kml_date_str = TARGET_DATE.replace("-", "") # Turns "2017-08-07" into "20170807"
matching_kmls = [f for f in os.listdir("kml_raw") if kml_date_str in f and f.endswith(".kml")]
if not matching_kmls:
    print(f"❌ Error: No KML file found in kml_raw/ containing {kml_date_str}")
    sys.exit(1)
KML_FILE = os.path.join("kml_raw", matching_kmls[0])
print(f"📁 Processing KML: {KML_FILE}")

# --- KML AND GEOJSON EXTRACTION ---
def extract_geojson_and_track():
    tree = ET.parse(KML_FILE)
    root = tree.getroot()
    ns = {'abvio': 'http://www.abvio.com/xmlschemas/1', 'kml': 'http://www.opengis.net/kml/2.2'}
    
    json_meta_node = root.find('.//kml:ExtendedData/abvio:json', ns)
    if json_meta_node is None: json_meta_node = root.find('.//abvio:json', ns)
        
    json_data_node = root.find('.//kml:ExtendedData/abvio:jsonData', ns)
    if json_data_node is None: json_data_node = root.find('.//abvio:jsonData', ns)

    meta = json.loads(json_meta_node.text)
    telemetry = json.loads(json_data_node.text)
    
    start_str = meta.get("startTimeISO8601") or meta.get("run", {}).get("startTimeISO8601")
    kml_clock_start = datetime.strptime(start_str[:19], "%Y-%m-%dT%H:%M:%S")
    
    run_data = meta.get("run", {})
    weather_data = run_data.get("weather", {})
    weather_code = weather_data.get("weatherCode", "Unknown")
    
    summary = {
        "start_iso": start_str,
        "moving_time": run_data.get("runTime", 0),
        "stopped_time": run_data.get("stoppedTime", 0),
        "total_time": run_data.get("runTime", 0) + run_data.get("stoppedTime", 0),
        "distance_km": run_data.get("distance", 0) / 1000.0,
        "ascent_m": run_data.get("ascent", 0) or run_data.get("climb", 0),
        "descent_m": run_data.get("descent", 0),
        "energy_kj": run_data.get("calories", 0) * 4.184,
        "temp_min": run_data.get("minTemperature", 0),
        "temp_avg": run_data.get("avgTemperature", 0),
        "temp_max": run_data.get("maxTemperature", 0),
        "humidity": weather_data.get("humidity", 0),
        "wind_kph": weather_data.get("windSpeedKMH", 0) or (weather_data.get("windSpeed", 0) * 3.6),
        "wind_dir": weather_data.get("windDirectionCode", "--"),
        "condition": "Clear / Sunny" if weather_code in ["FW", "Unknown", ""] else weather_code,
        "avg_speed_kph": run_data.get("averageSpeed", 0) * 3.6,
        "max_speed_kph": run_data.get("fastestSpeed", 0) * 3.6,
        "bike_name": run_data.get("bikeName", "Unknown"),
        "sunrise": weather_data.get("sunriseTimeStr", "--:--"),
        "sunset": weather_data.get("sunsetTimeStr", "--:--"),
        "locality": weather_data.get("requestLocality", "Unknown"),
        "app_info": f"{meta.get('appDisplayName', 'Cyclemeter')} ({meta.get('systemName', '')})"
    }

    lats, lons = telemetry.get('latitude', []), telemetry.get('longitude', [])
    altitudes, distances, speeds = telemetry.get('altitude', []), telemetry.get('distance', []), telemetry.get('speed', [])
    
    if not distances: distances = [0] * len(lats)
    if not altitudes: altitudes = [0] * len(lats)
    if not speeds: speeds = [0] * len(lats)
    
    full_coords, track_points, segments_slow, segments_medium, segments_fast, segments_sprint = [], [], [], [], [], []

    for i in range(len(lats)):
        alt = altitudes[i] if i < len(altitudes) else 0.0
        full_coords.append([lons[i], lats[i], alt])
        track_points.append({
            'time': kml_clock_start + timedelta(seconds=telemetry['timeOffset'][i]),
            'lat': lats[i], 'lon': lons[i]
        })
        
        if i < len(lats) - 1:
            spd_kph = speeds[i] * 3.6
            p1 = [lons[i], lats[i], alt]
            p2 = [lons[i+1], lats[i+1], altitudes[i+1] if i+1 < len(altitudes) else 0.0]
            segment = [p1, p2]
            if spd_kph < 12: segments_slow.append(segment)
            elif spd_kph < 22: segments_medium.append(segment)
            elif spd_kph < 32: segments_fast.append(segment)
            else: segments_sprint.append(segment)
        
    geojson = {
        "type": "FeatureCollection",
        "features": [
            { "type": "Feature", "properties": { "type": "full_track", "name": f"Via Francigena {TARGET_DATE}", "summary": summary, "distances": distances, "altitudes": altitudes, "speeds": speeds }, "geometry": { "type": "LineString", "coordinates": full_coords } },
            { "type": "Feature", "properties": { "type": "speed_slow" }, "geometry": { "type": "MultiLineString", "coordinates": segments_slow } },
            { "type": "Feature", "properties": { "type": "speed_medium" }, "geometry": { "type": "MultiLineString", "coordinates": segments_medium } },
            { "type": "Feature", "properties": { "type": "speed_fast" }, "geometry": { "type": "MultiLineString", "coordinates": segments_fast } },
            { "type": "Feature", "properties": { "type": "speed_sprint" }, "geometry": { "type": "MultiLineString", "coordinates": segments_sprint } }
        ]
    }
    
    geojson_path = f"geojson/route_{TARGET_DATE}.geojson"
    with open(geojson_path, "w") as f:
        json.dump(geojson, f)
    print(f"✅ Extracted GeoJSON to {geojson_path}")
    return track_points

# --- PHOTO & AI LOGIC ---
def get_photo_time(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
        for t in ['EXIF DateTimeOriginal', 'Image DateTime']:
            if t in tags:
                try: return datetime.strptime(str(tags[t]), "%Y:%m:%d %H:%M:%S")
                except: continue
    return None

async def get_location_data(client, lat, lon):
    try:
        resp = await client.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18", headers={"User-Agent": "Kinesis/1.0"})
        data = resp.json()
        await asyncio.sleep(1.1)
        short_title = "Via Francigena"
        if "address" in data:
            addr = data["address"]
            
            # Extract up to 3 levels of geographic data
            level_1 = addr.get("road") or addr.get("pedestrian") or addr.get("path")
            level_2 = addr.get("village") or addr.get("suburb") or addr.get("city_district") or addr.get("hamlet")
            level_3 = addr.get("city") or addr.get("town") or addr.get("county")
            
            # Combine them, ignoring any empty ones
            parts = [p for p in [level_1, level_2, level_3] if p]
            
            if parts: 
                # Join up to 3 parts (e.g., Road, Neighborhood, City)
                short_title = ", ".join(parts[:3])
                
        return short_title, data.get("display_name", "Unknown")
    except: 
        return "Via Francigena", "Unknown"

async def pass_1_visuals(client, filename, track_points):
    image_path = os.path.join(IMAGE_DIR, filename)
    json_path = os.path.join(JSON_DIR, f"{filename}.json")
    
    photo_time = get_photo_time(image_path)
    time_str = photo_time.strftime("%H:%M") if photo_time else "Unknown"
    
    gps_coords = "[12.4922, 41.8902]" # Default
    lat, lon = 41.8902, 12.4922
    if photo_time and track_points:
        closest = min(track_points, key=lambda p: abs(p['time'] - photo_time))
        if abs(closest['time'] - photo_time).total_seconds() <= 2700:
            gps_coords = f"[{closest['lon']:.5f}, {closest['lat']:.5f}]"
            lat, lon = closest['lat'], closest['lon']

    if os.path.exists(json_path):
        with open(json_path, "r") as f: return json.load(f)

    short_title, rich_context = await get_location_data(client, lat, lon)
    print(f"🌍 Pass 1: Scanning {filename} at {short_title}...")
    
    with open(image_path, "rb") as f: b64 = base64.b64encode(f.read()).decode("utf-8")
    
    payload = {
        "model": MODEL, "response_format": { "type": "json_object" },
        "messages": [
            {"role": "system", "content": "Return JSON: {'dc_description':'objective visual details', 'novel_visual_observations':'1-2 empirical facts'}"},
            {"role": "user", "content": [{"type": "text", "text": "Analyze image."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}
        ]
    }
    
    try:
        resp = await client.post(ENDPOINT, headers={"api-key": API_KEY, "Content-Type": "application/json"}, json=payload, timeout=60.0)
        res = json.loads(resp.json()["choices"][0]["message"]["content"])
        res.update({"filename": filename, "time": time_str, "gps_coordinates": gps_coords, "location_name": short_title, "rich_context": rich_context})
        with open(json_path, "w") as f: json.dump(res, f, indent=4)
        return res
    except Exception as e: print(f"❌ Error: {e}"); return None

async def pass_2_narrative(client, all_data):
    cache_path = os.path.join(JSON_DIR, "global_narratives.json")
    if os.path.exists(cache_path):
        print("⏭️  Pass 2 Skipped: Narrative already exists.")
        with open(cache_path, "r") as f: return json.load(f)

    print("\n🖋️ Pass 2: AI is writing the global narrative...")
    timeline = "\n".join([f"- {d['filename']} | {d['time']} | {d['location_name']}\n  Visuals: {d['novel_visual_observations']}" for d in all_data])

    # NEW: Shorter, punchier map captions since the main essay handles the deep philosophy
    prompt = f"""You are an expert auto-ethnographer writing an exhibition.
DIARY: {DAY_DIARY}
TIMELINE: {timeline}

Write a punchy, 70-word caption for EACH photo. DO NOT start with "On this day" or "In this photo". These will be used as interactive map slider captions. Keep them atmospheric and tied to the physical geography. FIRST-PERSON POV ONLY: You are the author reflecting on your own past journey. You must use "I", "me", and "my". NEVER refer to yourself in the third person (e.g., do not say "the rider", "the author", or "the cyclist").
Return JSON mapping filename to paragraph."""

    # We explicitly ask for a large token limit, just in case
    payload = {
        "model": MODEL, 
        "response_format": { "type": "json_object" }, 
        "messages": [{"role": "system", "content": prompt}],
        "max_completion_tokens": 15000
    }
    
    try:
        # NEW: Increased timeout to 240 seconds (4 minutes) to handle 30+ photos
        resp = await client.post(ENDPOINT, headers={"api-key": API_KEY, "Content-Type": "application/json"}, json=payload, timeout=240.0)
        resp.raise_for_status() # This will catch HTTP errors
        
        narratives = json.loads(resp.json()["choices"][0]["message"]["content"])
        with open(cache_path, "w") as f: json.dump(narratives, f, indent=4, ensure_ascii=False)
        return narratives
        
    except Exception as e: 
        # NEW: Prints the EXACT error (Timeout, JSON failure, etc)
        print(f"❌ Error in Pass 2: {repr(e)}")
        if 'resp' in locals():
            print("--- Raw AI Response ---")
            print(resp.text[:1000]) # Prints the first 1000 characters so we can see if it got cut off
        return {}

async def main():
    print(f"🚀 Processing Day: {TARGET_DATE}")
    track_points = extract_geojson_and_track()
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))])
    
    async with httpx.AsyncClient() as client:
        results = [await pass_1_visuals(client, img, track_points) for img in images]
        await pass_2_narrative(client, [r for r in results if r])
    print(f"🎉 Done processing {TARGET_DATE}. You can now run python3 process_daily_prose.py 2017-08-07 and python3 build_website.py")

if __name__ == "__main__":
    asyncio.run(main())