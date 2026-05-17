import os
import json
import re
import xml.etree.ElementTree as ET

KML_FILE = "kml_raw/Cyclemeter-Cycle-20170807-1024.kml"

def export_geojson():
    print("🌍 Extracting route from KML...")
    
    # 1. Extract the exact date from the KML filename
    match = re.search(r'(\d{4})(\d{2})(\d{2})', KML_FILE)
    if match:
        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    else:
        date_str = "unknown_date"

    # 2. Parse the KML telemetry
    tree = ET.parse(KML_FILE)
    root = tree.getroot()
    ns = {'abvio': 'http://www.abvio.com/xmlschemas/1'}
    telemetry = json.loads(root.find('.//abvio:jsonData', ns).text)
    
    coordinates = []
    for i in range(len(telemetry['latitude'])):
        coordinates.append([telemetry['longitude'][i], telemetry['latitude'][i]])
        
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            },
            "properties": {"name": f"Via Francigena {date_str}"}
        }]
    }
    
    # 3. Create the geojson folder if it doesn't exist
    os.makedirs("geojson", exist_ok=True)
    output_filename = f"geojson/route_{date_str}.geojson"
    
    with open(output_filename, "w") as f:
        json.dump(geojson, f)
        
    print(f"✅ Saved route to: {output_filename}")

if __name__ == "__main__":
    export_geojson()
