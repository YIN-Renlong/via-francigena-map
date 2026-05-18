# Kinesis & Praxis: The Via Francigena Archive

**A 2026 AI-Augmented Retrospective & Spatial Auto-Ethnography Engine (Expedition Data: August 2017)**

**Live Demo:** [https://yin-renlong.github.io/via-francigena-map/](https://yin-renlong.github.io/via-francigena-map/)

### Author: YIN Renlong

* **Disciplines:** Digital Humanities, Theology & Missiology, Computer Science
* **Project Type:** Digital Cultural Archive & Spatial Auto-Ethnography
* **Academic Context:** Online Publishing (B-KUL-F0UO1A), KU Leuven
* **Professor:** Prof. Frederik Truyen

---

## 📜 Abstract & Philosophical Foundation

This project is a custom-built, open-source publishing engine designed to document a 1,000-kilometer bicycle expedition from Rome to Bergamo along the Via Francigena, undertaken in August 2017. The architecture of the website serves as a framework for **Spatial Auto-Ethnography**. 

Revisiting the expedition nearly a decade later, the raw data from 2017 (898 DSLR photographs, KML tracking files, and private diary entries) functions as a psychological and historical baseline. The project traces a period of personal and professional development, documenting the transition from a theology student navigating rural Italy into an experienced researcher and systems developer. 

To present this cultural evolution without relying on proprietary SaaS platforms (such as ArcGIS StoryMaps) or framework-heavy environments (such as React), this project prioritizes **Archival Stability**. By utilizing Vanilla HTML, CSS Grid, standard JavaScript, and MapLibre GL JS, the codebase is designed to ensure that this digital archive remains legible, functional, and accessible over the long term.

---

## ⚙️ Technical Architecture: A 3-Stage Pipeline

The website content is dynamically compiled by a custom Python pipeline that processes spatial data, synthesizes narrative text, and generates the web interface.

### 1. `process_day.py` (Data Extraction & Visual Analysis)
This script builds the foundational dataset. It parses raw `.kml` GPS files to extract environmental telemetry, including altitude gradients, moving time, ambient temperature, and energy expended. Concurrently, it uses Azure OpenAI Vision models to analyze original photographs, generating structured visual metadata and concise, 30-word geographic captions tailored for interactive map markers.

### 2. `process_daily_prose.py` (Narrative Synthesis)
This script processes the qualitative data. It reads the author's private `memory.md` diary entries. Acting as an analytical tool, the Azure OpenAI LLM synthesizes these private reflections with the generated visual metadata. It outputs a public-facing, structured ethnographic essay in Markdown format, facilitating an objective, external analysis of the author's field notes.

### 3. `build_website.py` (Site Compilation)
This is the core compiler. It parses the Markdown output and translates it into a dynamic web interface. It identifies custom "Layout Grammar" tags within the text and converts them into specific CSS/HTML components. It also executes a mathematical interleaving sequence, slicing the long-form essays and injecting interactive Map Cards between paragraphs to establish a balanced reading rhythm. Finally, it outputs the static `config.js` file required by the frontend.

---

## 🧭 UX & UI Design: Interface and Content Integration

The user interface is designed to clearly separate deep reading sections from interactive geographic exploration.

*   **Layered Reading Layout:** To distinguish the text from the map background, the reading layout utilizes a CSS pseudo-element (`::before`) to create an asymmetric frame. The `#f9f6ed` reading layer sits within it, while keeping the 3D map visible and interactive in the screen margins.
*   **Dynamic Image Deduplication:** A Python Regex parser tracks every photograph selected for the main essay. It appends these to a `used_images` array and removes them from the Map Slider queue, preventing redundant images from appearing twice in the user interface.
*   **Context-Aware Telemetry Dashboard:** A bottom-anchored dashboard displays speed, elevation, and weather data. JavaScript event listeners automatically hide the dashboard during text-heavy prose sections to minimize reading distraction, and display it again when the user scrolls to the geographic map cards.
*   **Day Transitions:** Full-screen cover images with typography (Georgia and Open Sans) signal the transition between days, visually breaking up the content for better pacing.

---

## 🛠️ Development History and Iterative Process

The final architecture is the result of an iterative development process aimed at balancing technical performance with editorial design.

### Phase 1: Open-Source Alternatives & Pacing
The initial goal was to build an alternative to Mapbox's default scrolling templates without relying on proprietary platforms. A custom component renderer (`story-layouts.js`) was developed to inject HTML directly into Scrollama.js. To prevent scrolling fatigue, the Python compiler was programmed to divide the essays using `##` headers, interleaving text blocks with 1-3 interactive map cards to balance text and visual media.

### Phase 2: Markdown "Layout Grammar"
To achieve professional editorial layouts using only Markdown, the Azure OpenAI model was prompted to output specific layout syntax alongside the text:
*   `![FULL_BLEED](img.jpg)` -> Translated into a `100vw` image spanning the full width of the screen.
*   `![DIPTYCH](img1.jpg | img2.jpg)` -> Translated into a `1fr 1fr` CSS Grid for side-by-side image comparison.
*   `![STICKY_RIGHT](img.jpg)` -> Translated into a floating portrait crop, allowing text to wrap around the image.

### Phase 3: API Limitations and Reasoning Models
During development, the pipeline encountered `JSONDecodeError` failures during narrative generation. Analysis revealed that newer Azure OpenAI reasoning models (`o1` series) had deprecated the `max_tokens` parameter in favor of `max_completion_tokens`. Furthermore, the model was exhausting token limits during its internal "thinking phase" when processing large batches of photo metadata. The payload requests were adjusted to support 15,000-token completion windows, resolving the bottleneck.

### Phase 4: UI Refinements
In the final iterations, several UI elements were refined:
1.  **Progress Bar:** Traditional text navigation links were replaced with a minimalist reading progress bar, calculated dynamically via `window.scrollY`.
2.  **Lightbox:** A native Vanilla JS dark-mode Lightbox overlay was built to allow high-resolution image viewing without opening new browser tabs.
3.  **Metadata Styling:** GPS coordinates and technical metadata were styled with minimalist CSS borders and typography to maintain a consistent documentary aesthetic.

---

## 🖥️ Operational Guide: Compiling a New Day

The pipeline is fully automated once the raw data is provided. To process and publish a new day of the expedition, follow this workflow:

### The Compilation Pipeline

**1. Prepare the Raw Data**
* Create a new folder for the day: `images/2017-08-09/`
* Place all high-resolution `.jpg` photographs into this folder.
* Create a `memory.md` file inside the folder containing the diary entry for that day.
* Ensure the corresponding GPS tracking file (e.g., `Cyclemeter-Cycle-20170809.kml`) is located in the `kml_raw/` folder.

**2. Extract Telemetry & Visual Metadata**
Run the processing script in your terminal:
```bash
python3 process_day.py 2017-08-09
```

*Function:* Parses the KML for GPS and elevation data, and uses Azure OpenAI Vision to scan photos, generating [filename].json metadata and short map captions.

**3. Synthesize the Narrative Essay**
Run the prose generator:

```bash
python3 process_daily_prose.py 2017-08-09
```

*Function:* Reads memory.md and the photo metadata to generate a public-facing essay (output_metadata/2017-08-09/generated_prose.md), embedding selected photos using the designated layout grammar.

**4. Compile the Web Output**
Run the build script:

```bash
python3 build_website.py
```

*Function:* Translates the Markdown layout tags into HTML/CSS, filters out duplicate photos from the map slider queue, and compiles the final config.js file.

**5. View the Output**
Open index.html in a web browser to view the updated interactive map.

------

### 🎨 Manual Overrides & Configuration

The system allows for manual adjustments when specific editorial control is required.

**The Cover Image Override (cover.jpg)**
By default, the compiler uses the chronologically first photograph of the day as the transition Cover Image. To manually select a different cover photograph:

1. Copy the preferred photo into the images/YYYY-MM-DD/ folder.
2. Rename it to cover.jpg.
3. Re-run python3 build_website.py. The compiler will automatically prioritize cover.jpg.

**Updating Timeline Titles**
To modify the cinematic titles displayed over the cover images, open build_website.py. Locate the journal_headers dictionary near the top of the script to add or edit specific date metadata.

**Adding Photos to an Already Processed Day**
If new .jpg files are added to a previously compiled day:

1. Place the new photos into the day's images/ folder.
2. Navigate to output_metadata/YYYY-MM-DD/ and delete global_narratives.json.
3. Re-run steps 2, 3, and 4. (Deleting the narrative file forces the system to acknowledge the new photos and regenerate the metadata).

**Manual Markdown Layout Tags**
If you wish to manually edit the generated essay (output_metadata/YYYY-MM-DD/generated_prose.md), you can apply advanced CSS layouts by utilizing the following tags:

- ![FULL_BLEED](_MG_1234.jpg) : Renders a full-width image spanning the viewport.
- ![DIPTYCH](_MG_1234.jpg | _MG_5678.jpg) : Places two photos side-by-side in a CSS Grid.
- ![STICKY_RIGHT](_MG_1234.jpg) : Crops the photo to a 4:5 vertical portrait and floats it to the right of the text block.

------



*Kinesis & Praxis, YIN Renlong. KU Leuven, 2026.*