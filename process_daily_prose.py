import os
import sys
import json
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("AZURE_API_KEY")
ENDPOINT = os.getenv("AZURE_ENDPOINT")
MODEL = os.getenv("DEPLOYMENT_NAME")

if len(sys.argv) < 2:
    print("❌ Error: Please provide a date. Example: python3 process_daily_prose.py 2017-08-07")
    sys.exit(1)

TARGET_DATE = sys.argv[1]
IMAGE_DIR = f"images/{TARGET_DATE}"
JSON_DIR = f"output_metadata/{TARGET_DATE}"
MEMORY_FILE = f"{IMAGE_DIR}/memory.md"
OUTPUT_PROSE_FILE = f"{JSON_DIR}/generated_prose.md"

async def generate_prose():
    print(f"🚀 Generating public prose for {TARGET_DATE}...")

    # 1. Read the private diary
    if not os.path.exists(MEMORY_FILE):
        print(f"❌ Error: Could not find private memory file at {MEMORY_FILE}")
        sys.exit(1)
        
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        private_memory = f.read()

    # 2. Gather all the photo descriptions for context
    photo_context = ""
    photo_files = sorted([f for f in os.listdir(JSON_DIR) if f.endswith(".jpg.json")])
    
    if not photo_files:
        print(f"⚠️ Warning: No processed photo JSONs found in {JSON_DIR}.")
    
    for filename in photo_files:
        with open(os.path.join(JSON_DIR, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            img_name = data.get("filename", "")
            desc = data.get("dc_description", "")
            novel = data.get("novel_visual_observations", "")
            photo_context += f"- Image: {img_name}\n  Visual Details: {desc}\n  Novel Obs: {novel}\n\n"

# 3. Construct the AI Prompts
    system_prompt = """
You are an expert Digital Humanities scholar, sociologist, and ethnographic writer.
Your task is to write a cohesive, deeply reflective, public-facing essay for a specific day of a 1,000km bicycle expedition.

You will be provided with:
1. PRIVATE CONTEXT: The author's raw, unedited diary (memory.md). This contains psychological, logistical, and structural reflections.
2. VISUAL DATA: A list of photographs taken that day and their descriptions.

CRITICAL INSTRUCTIONS FOR PACING:
- You MUST divide your essay into 3 to 5 distinct thematic sections using Markdown H2 subheadings (e.g., `## The Topography of Exhaustion`). 

LAYOUT GRAMMAR (ART DIRECTION):
You act as the Art Director. You must embed photos from the VISUAL DATA into the text using specific Markdown syntax to trigger advanced CSS layouts:
1. Standard Image (Fits inside text margins): `![](_MG_1234.jpg)`
2. Full Bleed (100vw edge-to-edge break): `![FULL_BLEED](_MG_1234.jpg)`
3. Outset (Wider than text margins): `![OUTSET](_MG_1234.jpg)`
4. Hanging Left/Right (Pushed into margins, text wraps around): `![HANGING_LEFT](_MG_1234.jpg)` or `![HANGING_RIGHT](_MG_1234.jpg)`
5. Hanging Portrait (Same as above, but automatically crops a landscape photo to a vertical 4:5 ratio): `![HANGING_LEFT_PORTRAIT](_MG_1234.jpg)` or `![HANGING_RIGHT_PORTRAIT](_MG_1234.jpg)`
6. Diptych (Side-by-side): `![DIPTYCH](_MG_1234.jpg | _MG_5678.jpg)` or `![OUTSET_DIPTYCH](_MG_1234.jpg | _MG_5678.jpg)`

THEMATIC BREAKS:
When transitioning between major themes without an image, use `***` on a new line to insert a minimalist wavy section divider.

GENERAL INSTRUCTIONS:
- Synthesize the physical journey with the psychological reality.
- DO NOT reveal overly sensitive private information.
- Only use exact filenames provided in the VISUAL DATA.
- Output ONLY the Markdown text. Do not wrap it in JSON.
"""

    user_prompt = f"""
PRIVATE CONTEXT (DO NOT PUBLISH DIRECTLY):
{private_memory}

VISUAL DATA (AVAILABLE IMAGES):
{photo_context}

Please write the public essay in Markdown format.
"""

    # 4. Call Azure OpenAI
    payload = {
        "model": MODEL, 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    print("⏳ Waiting for Azure OpenAI to write the essay...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                ENDPOINT, 
                headers={"api-key": API_KEY, "Content-Type": "application/json"}, 
                json=payload, 
                timeout=120.0
            )
            resp.raise_for_status()
            
            # Extract the raw markdown text
            generated_markdown = resp.json()["choices"][0]["message"]["content"]
            
            # 5. Save the AI's essay to the output folder
            with open(OUTPUT_PROSE_FILE, "w", encoding="utf-8") as f:
                f.write(generated_markdown)
                
            print(f"✅ Success! Saved public prose to {OUTPUT_PROSE_FILE}")
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            if 'resp' in locals():
                print(resp.text)

if __name__ == "__main__":
    asyncio.run(generate_prose())