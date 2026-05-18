import os
import json
import re
import xml.etree.ElementTree as ET

KML_FILE = "kml_raw/Cyclemeter-Cycle-20170807-1024.kml"

def export_geojson():
    print("🌍 Extracting High-Res Telemetry & Weather from KML...")
    
    match = re.search(r'(\d{4})(\d{2})(\d{2})', KML_FILE)
    date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else "unknown"

    tree = ET.parse(KML_FILE)
    root = tree.getroot()
    ns = {'abvio': 'http://www.abvio.com/xmlschemas/1', 'kml': 'http://www.opengis.net/kml/2.2'}
    
    json_meta_node = root.find('.//kml:ExtendedData/abvio:json', ns)
    if json_meta_node is None: json_meta_node = root.find('.//abvio:json', ns)
        
    json_data_node = root.find('.//kml:ExtendedData/abvio:jsonData', ns)
    if json_data_node is None: json_data_node = root.find('.//abvio:jsonData', ns)

    if json_meta_node is None or json_data_node is None:
        print("❌ Error: Could not find telemetry data.")
        return
        
    meta = json.loads(json_meta_node.text)
    telemetry = json.loads(json_data_node.text)
    
    run_data = meta.get("run", {})
    weather_data = run_data.get("weather", {})
    
    # Weather Mapping
    weather_code = weather_data.get("weatherCode", "Unknown")
    condition_str = "Clear / Sunny" if weather_code in ["FW", "Unknown", ""] else weather_code

    moving_time = run_data.get("runTime", 0)
    stopped_time = run_data.get("stoppedTime", 0)
    total_time = moving_time + stopped_time
    energy_kj = run_data.get("calories", 0) * 4.184

    # NEW: Expanded Telemetry
    avg_speed_kph = run_data.get("averageSpeed", 0) * 3.6
    max_speed_kph = run_data.get("fastestSpeed", 0) * 3.6
    app_info = f"{meta.get('appDisplayName', 'Cyclemeter')} v{meta.get('appVersion', '')} ({meta.get('systemName', '')} {meta.get('systemVersion', '')})"

    summary = {
        "start_iso": run_data.get("startTimeISO8601", ""),
        "moving_time": moving_time,
        "stopped_time": stopped_time,
        "total_time": total_time,
        "distance_km": run_data.get("distance", 0) / 1000.0,
        "ascent_m": run_data.get("ascent", 0),
        "descent_m": run_data.get("descent", 0),
        "energy_kj": energy_kj,
        "temp_min": run_data.get("minTemperature", 0),
        "temp_avg": run_data.get("avgTemperature", 0),
        "temp_max": run_data.get("maxTemperature", 0),
        "humidity": weather_data.get("humidity", 0),
        "wind_kph": weather_data.get("windSpeedKMH", 0),
        "wind_dir": weather_data.get("windDirectionCode", "--"),
        "condition": condition_str,
        # New Expanded Fields
        "avg_speed_kph": avg_speed_kph,
        "max_speed_kph": max_speed_kph,
        "bike_name": run_data.get("bikeName", "Unknown"),
        "sunrise": weather_data.get("sunriseTimeStr", "--:--"),
        "sunset": weather_data.get("sunsetTimeStr", "--:--"),
        "locality": weather_data.get("requestLocality", "Unknown"),
        "app_info": app_info
    }

    lats = telemetry.get('latitude', [])
    lons = telemetry.get('longitude', [])
    altitudes = telemetry.get('altitude', [])
    distances = telemetry.get('distance', [])
    speeds = telemetry.get('speed', [])
    
    if not distances: distances = [0] * len(lats)
    if not altitudes: altitudes = [0] * len(lats)
    if not speeds: speeds = [0] * len(lats)
    
    full_coordinates = []
    
    # Buckets for Map Coloring
    segments_slow = []    # < 12 km/h
    segments_medium = []  # 12 - 22 km/h
    segments_fast = []    # 22 - 32 km/h
    segments_sprint = []  # > 32 km/h

    for i in range(len(lats)):
        alt = altitudes[i] if i < len(altitudes) else 0.0
        full_coordinates.append([lons[i], lats[i], alt])
        
        # Build segments for coloring (needs pairs of points)
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
            {
                "type": "Feature",
                "properties": {
                    "type": "full_track",
                    "name": f"Via Francigena {date_str}",
                    "summary": summary, 
                    "distances": distances,
                    "altitudes": altitudes,
                    "speeds": speeds
                },
                "geometry": { "type": "LineString", "coordinates": full_coordinates }
            },
            { "type": "Feature", "properties": { "type": "speed_slow" }, "geometry": { "type": "MultiLineString", "coordinates": segments_slow } },
            { "type": "Feature", "properties": { "type": "speed_medium" }, "geometry": { "type": "MultiLineString", "coordinates": segments_medium } },
            { "type": "Feature", "properties": { "type": "speed_fast" }, "geometry": { "type": "MultiLineString", "coordinates": segments_fast } },
            { "type": "Feature", "properties": { "type": "speed_sprint" }, "geometry": { "type": "MultiLineString", "coordinates": segments_sprint } }
        ]
    }
    
    os.makedirs("geojson", exist_ok=True)
    output_filename = f"geojson/route_{date_str}.geojson"
    
    with open(output_filename, "w") as f:
        json.dump(geojson, f)
        
    print(f"✅ Saved telemetry, weather, and color-coded route to: {output_filename}")

if __name__ == "__main__":
    export_geojson()
