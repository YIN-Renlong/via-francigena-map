// ==========================================================================
// STORY LAYOUTS JS (ArcGIS-Style Component Generator)
// ==========================================================================

const Layouts = {
    
    // 1. Full Screen Cover Title
    renderCover: function(chapter) {
        // Only render the kicker if it exists in the data
        const kickerHtml = chapter.kicker ? `<div class="cover-kicker">${chapter.kicker}</div>` : '';
        return `
        <div class="step layout-cover" id="${chapter.id}" style="background-image: url('${chapter.image}');">
            ${kickerHtml}
            <h1>${chapter.title}</h1>
            ${chapter.description} 
        </div>
        `;
    },

    // 2. Solid Article Page (Reading Break)
    renderArticle: function(chapter) {
        return `
        <div class="step layout-article-solid" id="${chapter.id}">
            <div class="article-container">
                <h2>${chapter.title}</h2>
                <p>${chapter.description}</p>
            </div>
        </div>
        `;
    },

    // 3. Floating Map Card
    renderFloatingCard: function(chapter) {
        return `
        <div class="step layout-floating-card" id="${chapter.id}">
            <div class="floating-card">
                <h3>${chapter.title}</h3>
                ${chapter.description}
                <span class="gps-tag">Coordinate: ${chapter.location.center[1].toFixed(5)} N, ${chapter.location.center[0].toFixed(5)} E</span>
            </div>
        </div>
        `;
    },

    // 4. Media Map Card
    renderMediaCard: function(chapter) {
        const imgHtml = chapter.image ? `<img src="${chapter.image}" alt="${chapter.title}">` : '';
        return `
        <div class="step layout-media-card" id="${chapter.id}">
            <div class="media-card">
                ${imgHtml}
                <h3>${chapter.title}</h3>
                ${chapter.description}
                <span class="gps-tag">Coordinate: ${chapter.location.center[1].toFixed(5)} N, ${chapter.location.center[0].toFixed(5)} E</span>
            </div>
        </div>
        `;
    },

    // 5. Split Text & Photo
    renderSplit: function(chapter) {
        return `
        <div class="step layout-split" id="${chapter.id}">
            <div class="split-text">
                <h2>${chapter.title}</h2>
                <p>${chapter.description}</p>
                <span class="gps-tag" style="margin-top: 30px; display: inline-block;">Coordinate: ${chapter.location.center[1].toFixed(5)} N, ${chapter.location.center[0].toFixed(5)} E</span>
            </div>
            <div class="split-photo" style="background-image: url('${chapter.image}');"></div>
        </div>
        `;
    },

    // 6. PROSE LAYOUT (ArcGIS Full-Width Centered Article)
    renderProse: function(chapter) {
        return `
        <div class="step layout-prose" id="${chapter.id}">
            <div class="prose-container">
                <h2>${chapter.title}</h2>
                ${chapter.description} 
            </div>
        </div>
        `;
    }
};

// Main function to route the chapter to the correct layout
function renderChapter(chapter) {
    switch(chapter.layout) {
        case 'cover': return Layouts.renderCover(chapter);
        case 'article': return Layouts.renderArticle(chapter);
        case 'floating-card': return Layouts.renderFloatingCard(chapter);
        case 'media-card': return Layouts.renderMediaCard(chapter);
        case 'split': return Layouts.renderSplit(chapter);
        case 'prose': return Layouts.renderProse(chapter); // <-- This routes your AI essay correctly
        default: return Layouts.renderFloatingCard(chapter); 
    }
}