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

To prevent visual fatigue during the geographic scrolling segments, the engine dynamically alternates between distinct spatial layouts. This establishes a structural rhythm and shifts the visual hierarchy between the textual narrative and the photographic evidence:

*   **Layered Reading Layout:** To distinguish the text from the map background, the reading layout utilizes a CSS pseudo-element (`::before`) to create an asymmetric frame. The `#f9f6ed` reading layer sits within it, while keeping the 3D map visible and interactive in the screen margins.
*   **Dynamic Image Deduplication:** A Python Regex parser tracks every photograph selected for the main essay. It appends these to a `used_images` array and removes them from the Map Slider queue, preventing redundant images from appearing twice in the user interface.
*   **Context-Aware Telemetry Dashboard:** A bottom-anchored dashboard displays speed, elevation, and weather data. JavaScript event listeners automatically hide the dashboard during text-heavy prose sections to minimize reading distraction, and display it again when the user scrolls to the geographic map cards.
*   **Day Transitions:** Full-screen cover images with typography (Georgia and Open Sans) signal the transition between days, visually breaking up the content for better pacing.
*   **The Media Card (Image-Primary):** A classic editorial structure featuring an off-white background with a solid border. The photograph is placed at the top, preserving its original 16:10 aspect ratio, followed by the text and metadata.
*   **The Floating Vignette (Text-Primary):** A translucent, flush-left panel. To provide structural contrast, the textual narrative appears first. The accompanying photograph is repositioned to the bottom and forced into a 1:1 square crop via CSS `object-fit`, acting as a visual anchor.
*   **The Immersive Parallax (`immersive-left`):** Designed for high-impact visual breaks, this layout utilizes the photograph as a full-viewport `100vh` background with `background-attachment: fixed`. A dark-themed text panel scrolls vertically over the static image, creating a parallax effect before returning the user to the interactive map.
*   **The Split Layout:** A 35/65 vertical division of the viewport, dedicating distinct, equalized zones to the narrative text and the photographic background.
*   **Asymmetric Transitions:** Component widths are deliberately varied (e.g., setting floating cards to `42vw`) to create a cascading "staircase" overlap during scroll transitions. This prevents rigid vertical alignment and creates a more organic, dynamic visual flow as elements fade in and out of the viewport.
*   **Guided but Explorable Cartography:** The 3D MapLibre environment retains full native interaction (drag, pan, pitch, and rotate). To achieve this without breaking the scrolling narrative, the frontend utilizes a "Ghost Layer" architecture. By setting `pointer-events: none` on the primary Scrollama container (`#features`), the empty margins become permeable to mouse inputs, allowing the user to explore the topography underneath. However, the moment the user resumes scrolling the mouse wheel, the `IntersectionObserver` utilizes `map.flyTo()` to gracefully snap the camera back to the scripted focal point, perfectly balancing user agency with narrative control.

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

### Phase 2.5: Micro-Typography and "Breaking the Grid"
To prevent visual fatigue during long-form reading segments, the engine was upgraded to support advanced spatial manipulations within the text itself. By establishing a constrained 850px reading column, the AI Art Director can selectively "break the grid" to create a dynamic, organic visual rhythm:
*   `![OUTSET](img.jpg)` -> Expands the photograph 300px wider than the text margins, creating a commanding visual anchor without overwhelming the viewport.
*   `![HANGING_LEFT](img.jpg)` -> Pushes the image into the negative space of the left margin, allowing the text to wrap elegantly around it (a classic magazine layout).
*   `![HANGING_RIGHT_PORTRAIT](img.jpg)` -> Automatically crops a landscape photograph into a 4:5 vertical vignette and anchors it to the right margin.
*   `***` -> Translated by the Python Regex parser into a custom SVG "Fleuron" (a wavy thematic section break), signaling a psychological pause in the narrative without relying on external image files.
*   **Inline Regex Parsing:** The compiler natively interprets standard markdown emphasis (`*italics*`, `**bold**`) without relying on heavy external Python libraries, preserving the zero-dependency, archivable nature of the codebase.

### Phase 3: API Limitations and Reasoning Models

During development, the pipeline encountered `JSONDecodeError` failures during narrative generation. Analysis revealed that newer Azure OpenAI reasoning models (`o1` series) had deprecated the `max_tokens` parameter in favor of `max_completion_tokens`. Furthermore, the model was exhausting token limits during its internal "thinking phase" when processing large batches of photo metadata. The payload requests were adjusted to support 15,000-token completion windows, resolving the bottleneck.

### Phase 4: UI Refinements
In the final iterations, several UI elements were refined:
1.  **Progress Bar:** Traditional text navigation links were replaced with a minimalist reading progress bar, calculated dynamically via `window.scrollY`.
2.  **Lightbox:** A native Vanilla JS dark-mode Lightbox overlay was built to allow high-resolution image viewing without opening new browser tabs.
3.  **Metadata Styling:** GPS coordinates and technical metadata were styled with minimalist CSS borders and typography to maintain a consistent documentary aesthetic.

### Phase 5: System Optimization and Edge-Case Resolution

As the dataset expanded, several structural and performance bottlenecks were identified and resolved to ensure cross-device stability:

1.  **Temporal Data Synchronization (GPS Snapping):** Discrepancies were identified where photograph EXIF timestamps occurred outside the active KML tracking window (e.g., morning preparations prior to GPS activation). A "snapping" algorithm was implemented in `process_day.py` to bind out-of-bounds media to the nearest valid chronological GPS coordinate (the daily start or end point). This ensures data integrity and prevents erratic camera movements during map rendering.
2.  **DOM Observer Refinement:** An opacity "ghosting" bug occurred where tall `.layout-prose` elements prematurely lost their `.active` visibility class during scrolling. The JavaScript `onStepEnter` logic was updated to selectively exclude full-page prose and cover blocks from class removal, preserving their solid state until the user fully scrolls past them.
3.  **Memory Management:** Initial testing utilized CSS hardware acceleration (`will-change`, `transform: translateZ(0)`) to optimize scrolling. However, rendering hundreds of accelerated DOM nodes caused VRAM memory exhaustion on mobile devices. These rules were reverted in favor of native HTML5 `loading="lazy"` attributes across all dynamically generated `<img>` tags, significantly reducing the initial payload and stabilizing mobile performance.
4.  **Data Structure Refactoring:** The manual layout assignment logic in `build_website.py` was refactored to utilize a grouped dictionary (`override_map`). This streamlines the batch-assignment of layout types to specific image filenames. Additionally, robust string sanitization was implemented to escape backticks, preventing JavaScript compilation failures caused by apostrophes in Italian geographic names (e.g., *Castiglione d'Orcia*).
5.  **Minimap Synchronization:** The secondary global minimap was updated with a `minimap.flyTo` function to synchronize its camera center with the primary map's coordinates, ensuring the location pin remains within the viewport during long-distance geographic shifts.

### Phase 6: Cross-Origin Integration and Security

To embed the application within a WordPress CMS environment (WPBakery) without suffering the performance penalties or UX friction typically associated with iframes, a seamless cross-origin handoff system was developed.

1.  **IntersectionObserver and Viewport Locking:** The WordPress parent page utilizes an `IntersectionObserver` to detect when the documentary iframe occupies 95% of the viewport. Upon detection, the parent document's overflow is locked, and the iframe snaps into a fixed full-screen position. 
2.  **The `postMessage` API Handoff:** To enable a seamless exit, the GitHub-hosted `index.html` file monitors scroll boundaries. When the user reaches the absolute top or bottom of the documentary, a `postMessage` signal (e.g., `scroll_down_out`) is broadcast to the parent WordPress window. The parent window receives the signal, unlocks the body scroll, and gently nudges the viewport, returning control to the standard CMS environment without requiring manual button clicks.
3.  **Iframe Throttling Mitigation:** To bypass browser iframe throttling and prevent premature scroll interception by the mouse, an invisible CSS shield restricts pointer events until the iframe is perfectly aligned in the viewport.
4.  **API Security and Vector Tiles:** The project utilizes Esri ArcGIS V2 vector basemaps ("Modern Antique"). To secure the requisite API keys within a public, client-side configuration file, strict HTTP Referrer URL restrictions were implemented (e.g., `https://*.yin.roma.it/*`). This restricts tile access exclusively to authorized development and production environments, neutralizing unauthorized usage.

### Phase 7: Telemetry & Data Visualization Polish (23 May, 2026)

To enhance the professional aesthetic of the data visualization and mimic high-end spatial tracking platforms (e.g., Strava, Garmin), several refinements were made to the dashboard interface:

1.  **Contextual Distance Tracking:** The static distance metric was refactored into a progressive `Current / Total` display (e.g., `45.2 / 80.5`). This is calculated dynamically during the `onStepEnter` scroll event. To maintain a clean UI, JavaScript `innerHTML` injection is used to apply a strict typographic hierarchy, keeping the current distance bold and prominent while fading the daily total into a smaller, secondary font weight.
2.  **In-Chart Legend Overlay:** The speed-zone color legend was transitioned from a standard DOM element into an absolute overlay within the Chart.js canvas container. Utilizing CSS `backdrop-filter: blur` (a frosted-glass effect), the legend remains perfectly legible even when the dynamic elevation line intersects behind it. This optimizes dashboard whitespace and adheres to modern data-visualization standards.
3.  **Dynamic Unit Injection:** To reduce label redundancy, unit markers were integrated directly into the numerical values. The Chart.js `callback` API was utilized to dynamically append "m" (meters) to the Y-axis tick generation. Similarly, the live altitude tracker utilizes inline CSS to append an elegantly scaled "m" to the live data stream, preventing the text UI from feeling overly bulky as values reach into the thousands.

### Phase 8: Mobile Gestures & Smart Branding

In the final polishing phase, critical adjustments were made to the mobile user experience and overall site branding to ensure cross-device stability:

1.  **Mobile Scroll Conflict Resolution:** A frustrating UX bug was identified on mobile devices where the "Ghost Layer" (`pointer-events: none` on the text container) allowed user touch swipes to fall through to the MapLibre canvas. The map intercepted these touches as drag events, completely blocking the browser's vertical scrolling. This was resolved via a dual-layered approach: enabling `cooperativeGestures` in MapLibre (requiring two fingers to pan, freeing one finger for scrolling) and forcing `pointer-events: auto` on mobile CSS breakpoints to safely shield the map from accidental thumb swipes.
2.  **Adaptive "Frosted Glass" Branding:** To solidify the documentary's visual identity, a custom brand logo was anchored to the viewport. Because the background shifts unpredictably between bright maps and dark, immersive parallax photographs, a dynamic contrast solution was required. Instead of complex JavaScript image-swapping, the logo was encased in a CSS "Frosted Glass" container (`backdrop-filter: blur` with an 85% opaque `#f9f6ed` background). This guarantees absolute text legibility while retaining an elegant, translucent editorial aesthetic.
3.  **Smart Auto-Hide Header:** To maximize reading space on restricted mobile viewports, the logo shifts to a top-center "pill" shape on screens under 800px. A custom JavaScript scroll-direction listener dynamically injects a `.logo-hidden` class. When the user scrolls down to read, the logo glides off-screen. The moment they swipe up, it reappears, providing seamless navigation without obstructing the spatial narrative.

### Phase 9: "Data Curation" and the Topographical Dashboard

To elevate the dashboard from a utilitarian "sports telemetry" readout to a museum-quality interactive exhibit, the design philosophy shifted from *data exhaustion* to *data curation*. Several advanced data visualization techniques were implemented in this polishing phase:

1. **Zero-Dependency Number Tweening (The Odometer Effect):** To prevent data readouts from jarringly snapping to new values during scroll events, a custom requestAnimationFrame engine was built. This creates a smooth, ease-out "odometer" effect for distance, speed, and gradient metrics. By avoiding heavy external animation libraries (like GSAP or CountUp.js), the project maintains its strict archival stability and lightweight footprint.
2. **Contextual Topography & The Floating Pill:** The static altitude metric was removed from the side panel to reduce visual clutter. Instead, utilizing the HTML5 Canvas API, a custom chart plugin was written to draw a dynamic "frosted glass" pill and locator ring on the fly. This tethers the exact altitude directly to the physical shape of the mountain, drastically reducing the reader's eye travel and merging the data with the visual terrain.
3. **Delicate Canvas Rendering (Mist & Shadows):** The default Chart.js aesthetic was stripped back to let the "mountain breathe." Harsh background grid lines and the solid black vertical scrubber were replaced with a delicate dashed guide-line. The solid gray fill beneath the route was replaced with an atmospheric, vertical gradient "mist."
4. **Dual-Layer Rendering Architecture:** A known rendering quirk in Chart.js causes ugly vertical striations ("hair") when applying gradient fills to highly segmented lines (such as our speed-colored route). To solve this, the chart data was elegantly split into two synchronized layers: a pure, un-segmented bottom layer handling the smooth mist gradient, and a top layer handling the colored route line. A custom plugin applies a drop-shadow *exclusively* to the top layer, giving the terrain crisp, 3D depth without muddying the gradient.
5. **Rolling-Window Gradient Math:** With altitude moved to the chart, the right-hand panel required a metric that better bridged the narrative gap between *Distance* and *Speed*. A dynamic slope calculation (Gradient %) was introduced. To prevent erratic jumping caused by raw GPS noise, the JavaScript calculates the slope using a +/- 5 point rolling window. The animateValue engine was upgraded to automatically inject a + sign and color-code the result (red for steep climbs, blue for descents), perfectly contextualizing the physical suffering or relief described in the prose.

### Phase 10: Performance Profiling and the "Main-Thread Traffic Jam" (23 May, 2026)

Following the implementation of the advanced topographical dashboard, testing revealed a perceptible micro-stutter (frame dropping) occurring exactly at the moment the user scrolled to a new geographic waypoint. Performance profiling isolated the issue to a classic JavaScript single-thread bottleneck: the browser was attempting to execute a WebGL 3D camera flight, redraw a heavily styled HTML5 Canvas chart (with drop-shadows and gradients), and calculate 180 frames of number tweening in the exact same millisecond.

To resolve this without sacrificing the rich visual feedback, a three-pronged optimization strategy was implemented:

1. **Staggered Rendering and Event Debouncing:** To prevent the MapLibre flyTo animation and the Chart.js update method from fighting for CPU/GPU resources, a "staggered rendering" architecture was introduced. The system now allows the heavy 3D map flight to initiate first. A setTimeout delays the chart redraw and telemetry calculations by 350 milliseconds, allowing the dashboard to smoothly "catch up" to the map. Furthermore, a clearTimeout debounce was added to the scroll observer; if a user rapidly scrolls past multiple photos, the system actively cancels the chart calculations for the skipped waypoints, preserving massive amounts of processing power.
2. **Eradicating DOM Thrashing:** The custom animateValue (odometer) engine initially utilized innerHTML to inject the dynamically formatted numbers (e.g., <span style="...">+12.4%</span>). Because this fired 60 times a second across three separate metrics, it forced the browser to destroy, re-parse, and rebuild HTML nodes 180 times per second, triggering heavy Layout Recalculation (Reflow). The engine was rewritten to cache the HTML structure once upon initialization and exclusively use textContent to swap the raw numerical strings, reducing CPU load by orders of magnitude.
3. **Asynchronous Media Unpacking:** Because the archive utilizes high-resolution DSLR photographs, the browser's default behavior was pausing the main thread to mathematically decode the heavy JPEGs as they entered the viewport, exacerbating scroll lag. The HTML5 decoding="async" attribute was injected into the procedural layout generator, instructing the browser to unpack the imagery on a background thread without interrupting the interactive scrolling timeline.

### Phase 11: Polish, Typography Unification, and Deployment Architecture (Post-Review Iteration)

Following a final review session with academic advisors, several critical UI/UX adjustments were implemented to elevate the project from a functional archive to a museum-quality digital exhibition. 

1. **Typography Unification:** To establish a seamless transition between the parent WordPress CMS and the interactive documentary iframe, the typography was unified. The legacy serif fonts (Georgia and Merriweather) were replaced with elegant, modern sans-serifs (**Karla** for body text and headers, matching the parent site). 
2. **Mobile Scaling & "Breathing Room":** Media queries were refined to dynamically scale down font sizes and line heights on mobile devices (<800px), preventing text from overwhelming small viewports. Additionally, the negative margins on the `HANGING_LEFT` and `HANGING_RIGHT` image layouts were slightly reduced. This preserves the editorial "breaking the grid" aesthetic while providing the text column with more spatial breathing room for enhanced readability.
3. **The 1-Click Deployment Pipeline (Cache-Busting):** To facilitate rapid iteration without relying on heavy CI/CD pipelines, a custom WordPress PHP plugin (`via-francigena-updater.php`) was developed. This plugin allows admins to pull the latest GitHub repository directly into the live server with one click. To defeat aggressive GitHub CDN and browser caching, query-string cache busters (`?nocache=time()` and `?v=2.0`) were engineered into both the PHP fetch logic and the HTML asset links, guaranteeing immediate live updates.
4. **Micro-Branding & SEO:** A custom favicon and `apple-touch-icon` were integrated, and the browser `<title>` was expanded, cementing the archive's identity as a standalone, professional web application.

5. **Parent CMS Mobile Optimization (Payload Reduction):** To ensure maximum performance and eliminate visual clutter on mobile devices, the heavy JavaScript-based hero element (Slider Revolution) was disabled entirely on viewports under 800px via aggressive CSS media queries. To compensate for the resulting structural shift, WPBakery's DOM rendering was intercepted using unique Extra Class Names (e.g., `.first-mobile-article`). This allowed for highly targeted CSS margin adjustments, preventing the narrative text from overlapping the fixed header and guaranteeing an immediate, elegant reading experience upon page load.

### Algorithmic Layout Distribution
To ensure the various spatial components are utilized dynamically without overwhelming the interface, the `build_website.py` compiler assigns layouts using a procedural generation algorithm based on two core principles:

*   **Weighted Probability Matrix:** Rather than a flat randomized selection, layouts are assigned mathematical weights. Standard, transparent map layouts (`floating-card`, `media-card`) are given a higher probability in the selection pool compared to visually dominant layouts (`split`, `immersive-left`). This ensures the 3D terrain remains the primary interface element, punctuated periodically by cinematic visual breaks.
*   **Sequential Constraints (Anti-Clumping Logic):** The compiler evaluates the previously assigned layout state during the generation loop. If a heavy structural layout (such as `cover`, `prose`, `immersive-left`, or `split`) was just rendered, the algorithm temporarily restricts the subsequent choice to standard, transparent map cards. This conditional logic guarantees a consistent editorial rhythm and prevents consecutive full-screen elements from entirely obscuring the geographic data.
*   **Deterministic Stability:** The randomized distribution is governed by a fixed seed (`random.seed`). This ensures that the procedural layout generation remains stable and reproducible across multiple compiler executions, preventing the interface from unpredictably shifting during textual revisions unless explicitly bypassed via the manual `override_map` dictionary.

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