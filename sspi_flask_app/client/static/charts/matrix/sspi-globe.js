class SSPIGlobeChart {
    constructor(parentElement) {
        this.parentElement = parentElement
        this.globeDataURL = "/api/v1/globe"
        this.tabBarState = "SSPI"; // load a globe for SSPI by default
        this.year = window.observableStorage.getItem("globeYear") || 2023;
        this.altitudeCoding = false;
        this.cloropleth = true;
        this.darkenBorders = false;
        this.globeRotation = window.observableStorage.getItem("globeRotation") ?? true;
        this.rotationOnClick = window.observableStorage.getItem("rotationOnClick") ?? true;
        this.activeCountry = null; // currently selected country for info display
        this.hoveredCountry = null; // currently hovered country properties for tooltip
        this.hoveredFeature = null; // currently hovered feature object for color comparison
        this.pins = new Set() // pins contains a list of pinned countries
        this.playing = window.observableStorage.getItem("globePlaying") || false // timeline play state
        this.playInterval = null // interval reference for timeline playback
        this.computeGlobeDimensions() 
        this.getComputedStyles()
        this.buildGlobeContainer() 
        this.buildGlobe()
        this.hydrateGlobe().then(this.restyleGlobe())
        this.setTheme(window.observableStorage.getItem("theme"))
        this.rigResizeListener()
        this.rigPinChangeListener()
        this.rigUnloadListener()
    }

    computeGlobeDimensions() {
        // Use viewport/container width instead of screen width for better responsiveness
        const availableWidth = Math.min(window.innerWidth, this.parentElement.clientWidth || window.innerWidth);
        const availableHeight = window.innerHeight;

        if (availableWidth < 700) {
            // For narrow viewports, use available width with some padding
            this.globeWidth = Math.max(300, availableWidth - 40); // Min 300px, max viewport - 40px padding
            this.globeHeight = Math.min(this.globeWidth, availableHeight - 200); // Leave room for controls
        } else {
            // Responsive sizing: use 60% of available width, capped at 900px max, 700px min
            const maxGlobeSize = 900;
            const targetSize = Math.min(availableWidth * 0.60, maxGlobeSize);
            this.globeWidth = Math.max(700, targetSize);
            this.globeHeight = this.globeWidth;
        }
    }

    getComputedStyles() {
      this.styles = {}
      this.styles.greenAccent = window.getComputedStyle(document.documentElement).getPropertyValue("--green-accent")
      this.styles.pageBackgroundColor = window.getComputedStyle(document.documentElement).getPropertyValue("--page-background")
      this.styles.boxBackgroundColor = window.getComputedStyle(document.documentElement).getPropertyValue("--box-background-color")
      this.styles.oceanColor = window.getComputedStyle(document.documentElement).getPropertyValue("--ocean-color")
      console.log(this.styles)
    }

    handleResize() {
        // Clear existing timeout
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }

        // Debounce resize events (wait 300ms after last resize)
        this.resizeTimeout = setTimeout(() => {
            const oldWidth = this.globeWidth;
            const oldHeight = this.globeHeight;

            // Recompute dimensions
            this.computeGlobeDimensions();

            // Only update if dimensions changed significantly (threshold: 50px)
            const widthDiff = Math.abs(this.globeWidth - oldWidth);
            const heightDiff = Math.abs(this.globeHeight - oldHeight);

            if (widthDiff > 50 || heightDiff > 50) {
                // Update globe dimensions
                if (this.globe) {
                    this.globe
                        .width(this.globeWidth)
                        .height(this.globeHeight);
                }
            }
        }, 300);
    }

    rigResizeListener() {
        this.resizeTimeout = null;
        window.addEventListener('resize', () => this.handleResize());
    }

    buildGlobeContainer() {
        this.root = document.createElement("div");
        this.root.classList.add("globe-visualization-container");
        this.buildChartOptions()
        this.parentElement.appendChild(this.root)
    }

    buildTabBar() {
        this.tabBar = document.createElement("div");
        this.tabBar.classList.add("globe-tab-bar");
        this.tabBar.innerHTML = `
            <button data-item-code="SSPI" data-active-tab=true> SSPI </button>
            <button data-item-code="SUS" data-active-tab=false> Sustainability </button>
            <button data-item-code="MS" data-active-tab=false> Market Structure </button>
            <button data-item-code="PG" data-active-tab=false> Public Goods </button>
        `;
        for (var i = 0; i < this.tabBar.children.length; i++) {
            this.tabBar.children[i].addEventListener('click', (el) => {
                const oldTab = this.tabBar.querySelector('[data-item-code="' + this.tabBarState + '"]')
                oldTab.dataset.activeTab = false;
                this.tabBarState = el.target.dataset.itemCode
                const newTab =  this.tabBar.querySelector('[data-item-code="' + this.tabBarState + '"]')
                newTab.dataset.activeTab = true;
                this.updateDataset()
                this.updatePolygonLabel()
                this.updateCountryInformation()
            });
        }

        // Add hamburger menu button to tab bar
        this.showChartOptions = document.createElement('button')
        this.showChartOptions.classList.add("globe-hamburger-menu")
        this.showChartOptions.ariaLabel = "Show Chart Options"
        this.showChartOptions.title = "Show Chart Options"
        this.showChartOptions.innerHTML = `
<svg class="svg-button show-chart-options-svg" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <use href="#icon-menu" />
</svg>
`;
        this.showChartOptions.addEventListener('click', () => {
            this.openChartOptionsSidebar()
        })
        this.tabBar.appendChild(this.showChartOptions)
        this.globeTabSliderColumn.appendChild(this.tabBar)
    }

    buildGlobe() {
        this.globeTabSliderColumn = document.createElement("div");
        this.globeTabSliderColumn.classList.add('globe-and-tab-container')
        this.buildTabBar() 
        this.globeSceneContainer = document.createElement("div");
        this.globeTabSliderColumn.appendChild(this.globeSceneContainer)
        this.root.appendChild(this.globeTabSliderColumn)
        this.globe = Globe()
            .width(this.globeWidth.toString())
            .height(this.globeHeight.toString())
            .showGraticules(false)
            .showAtmosphere(false)
            .lineHoverPrecision(0)
            .polygonAltitude(0.01)
            .polygonStrokeColor(this.getStrokeColor())
            .polygonsTransitionDuration(100)
            .pointOfView({lat: 25, lng: 60, altitude: 1.5}, 500)
            (this.globeSceneContainer)
        this.buildYearSlider()
    } 

    buildYearSlider() {
        this.yearSliderContainer = document.createElement("div");
        this.yearSliderContainer.classList.add('globe-year-slider-container')
        this.yearSliderContainer.innerHTML = `
<div class="year-slider-controls">
    <label class="year-slider-label" for="globe-year-slider">
        <span class="year-value-display" contenteditable="true" spellcheck="false">${this.year}</span>
    </label>
    <div class="year-slider-wrapper">
        <div class="year-slider-track-container">
            <div class="year-slider-ticks"></div>
            <input
                type="range"
                class="year-slider-input"
                id="globe-year-slider"
                min="2000"
                max="2023"
                value="${this.year}"
                step="1"
            />
        </div>
        <div class="year-slider-bounds">
            <span class="year-slider-min">2000</span>
            <span class="year-slider-max">2023</span>
        </div>
    </div>
    <button class="year-play-pause-button" aria-label="Play timeline">
        <span class="play-icon">▶</span>
        <span class="pause-icon" style="display:none;">⏸</span>
    </button>
</div>
        `;
        this.globeTabSliderColumn.appendChild(this.yearSliderContainer)
        this.rigYearSlider()
    }

    rigYearSlider() {
        this.yearSliderInput = this.yearSliderContainer.querySelector('.year-slider-input')
        this.yearValueDisplay = this.yearSliderContainer.querySelector('.year-value-display')
        this.playPauseButton = this.yearSliderContainer.querySelector('.year-play-pause-button')
        this.playIcon = this.yearSliderContainer.querySelector('.play-icon')
        this.pauseIcon = this.yearSliderContainer.querySelector('.pause-icon')

        this.yearSliderInput.addEventListener('input', (e) => {
            if (this.playing) {
                this.stopPlay()
            }
            this.year = parseInt(e.target.value)
            this.yearValueDisplay.textContent = this.year
            window.observableStorage.setItem("globeYear", this.year)
            this.updateDataset()
            this.updatePolygonLabel()
            this.updateCountryInformation()
        })

        // Handle contenteditable year display
        this.yearValueDisplay.addEventListener('keydown', (e) => {
            // Only allow numbers, backspace, delete, arrow keys, enter
            if (e.key === 'Enter') {
                e.preventDefault()
                this.yearValueDisplay.blur()
            } else if (!/^\d$/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                e.preventDefault()
            }
        })

        this.yearValueDisplay.addEventListener('blur', () => {
            const inputYear = parseInt(this.yearValueDisplay.textContent.trim())

            if (isNaN(inputYear) || inputYear < 2000 || inputYear > 2023) {
                // Invalid year, revert to current year
                this.yearValueDisplay.textContent = this.year
                this.yearValueDisplay.classList.add('year-input-error')
                setTimeout(() => {
                    this.yearValueDisplay.classList.remove('year-input-error')
                }, 500)
            } else if (inputYear !== this.year) {
                // Valid year and different from current, update
                if (this.playing) {
                    this.stopPlay()
                }
                this.year = inputYear
                this.yearSliderInput.value = this.year
                this.yearValueDisplay.textContent = this.year
                window.observableStorage.setItem("globeYear", this.year)
                this.updateDataset()
                this.updatePolygonLabel()
                this.updateCountryInformation()
            } else {
                // Same year, just ensure formatting is correct
                this.yearValueDisplay.textContent = this.year
            }
        })

        this.playPauseButton.addEventListener('click', () => {
            this.togglePlay()
        })

        // Restore playing state if it was active
        if (this.playing) {
            this.startPlay()
        }
    }

    advanceYear() {
        if (this.year < 2023) {
            this.year++
        } else {
            // Loop back to beginning
            this.year = 2000
        }
        this.yearSliderInput.value = this.year
        this.yearValueDisplay.textContent = this.year
        window.observableStorage.setItem("globeYear", this.year)
        this.updateDataset()
        this.updatePolygonLabel()
        this.updateCountryInformation()
    }

    startPlay() {
        this.playing = true
        window.observableStorage.setItem("globePlaying", true)
        this.playIcon.style.display = 'none'
        this.pauseIcon.style.display = 'inline'
        // Use 1200ms (100ms transition + 1100ms viewing time)
        this.playInterval = setInterval(() => this.advanceYear(), 1200)
    }

    stopPlay() {
        this.playing = false
        window.observableStorage.setItem("globePlaying", false)
        this.playIcon.style.display = 'inline'
        this.pauseIcon.style.display = 'none'
        if (this.playInterval) {
            clearInterval(this.playInterval)
            this.playInterval = null
        }
    }

    togglePlay() {
        if (this.playing) {
            this.stopPlay()
        } else {
            this.startPlay()
        }
    }

    async hydrateGlobe () {
        this.geojson = await fetch(this.globeDataURL).then(res => res.json())
        this.getVal = (feat) => { 
            let series = feat.properties[this.tabBarState]
            if (!series) {
                return -1
            }
            let value = series[this.year - 2000] 
            if (!value) {
                return -1
            }
            return value
        }
        this.setColorScale();
        this.globe
            .polygonsData(this.geojson.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
            .polygonCapColor(feat => this.colorScale(this.getVal(feat)))
            .polygonSideColor(feat => "transparent")
            .onPolygonHover(hoverD => {
                this.hoveredCountry = hoverD ? hoverD.properties : null;
                this.hoveredFeature = hoverD;
                this.globe
                    .polygonAltitude(d => d === hoverD ? 0.02 : 0.01)
                    .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                    .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'cc' : "transparent")
            })
            .onPolygonClick((p, e) => {
                if (this.globeRotation && this.rotationOnClick) {
                    this.globe.controls().autoRotate = !this.globe.controls().autoRotate;
                }
                this.activeCountry = p.properties;
                this.countryInformationBox.dataset.unpopulated = false;
                this.updateCountryInformation();
            })
            .polygonLabel(({ properties: d }) => this.getPolygonLabel(d))
        this.getPins()
    }

    restyleGlobe() {
        this.globe.backgroundColor(this.styles.boxBackgroundColor)
        // this.globe.globeImageUrl('//cdn.jsdelivr.net/npm/three-globe/example/img/earth-dark.jpg')
        const mat = this.globe.globeMaterial();
        mat.map = null;
        mat.bumpMap = null;
        mat.specularMap = null;
        mat.shininess = 0;
        if (mat.specular && mat.specular.set) mat.specular.set(0x000000);
        mat.color.set(this.styles.oceanColor);       // ocean color
        mat.needsUpdate = true;
        this.globe.controls().autoRotate = this.globeRotation
        this.globe.controls().autoRotateSpeed = 0.3
        this.globe.controls().enableZoom = true;
    }

    setTheme(theme) {
        this.getComputedStyles()
        this.restyleGlobe()
    }

    getStrokeColor() {
        // Returns a function that determines stroke color based on pin state and darkenBorders setting
        return (feat) => {
            if (feat.properties.pinned) {
                return '#ff0000'; // Bright red for pinned countries
            }
            return this.darkenBorders ? 'rgba(0, 0, 0, 1)' : 'rgba(0, 0, 0, 0.1)';
        };
    }

    getPolygonLabel(d) {
        return `
<div class="globegl-hover">
<h3><span class="country-name">${d.CFlag}\u0020${d.CName}\u0020(${d.CCode})</span><span class="globegl-hover-year">${this.year}</span></h3>
<div class="globegl-hover-score-container">
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SSPI"}><span class="globe-hover-item-label">SSPI Score:\u0020</span><span class="globe-hover-item-score">\u0020${d?.SSPI?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SUS"}><span class="globe-hover-item-label">Sustainability\u0020(SUS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.SUS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "MS"}><span class="globe-hover-item-label">Market Structure\u0020(MS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.MS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "PG"}><span class="globe-hover-item-label">Public Goods\u0020(PG):\u0020</span><span class="globe-hover-item-score">\u0020${d?.PG?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
</div>
</div>
`;
    }

    updateCountryInformation() {
        if (!this.activeCountry) return;

        // Check if country is currently pinned
        const isPinned = this.activeCountry.pinned || false;
        const pinButtonText = isPinned ? "Unpin Country" : "Pin Country";
        const pinButtonClass = isPinned ? "unpin-country-button" : "pin-country-button";

        this.countryInformationBox.innerHTML = `
<div id="#active-country-information" class="country-details-info">
<h3 class="country-details-header"><span class="country-name">${this.activeCountry.CFlag}\u0020${this.activeCountry.CName}\u0020(${this.activeCountry.CCode})</span><span class="country-details-year">${this.year}</span></h3>
<div class="country-details-score-container">
    <div class="country-details-score-line" data-active-tab=${this.tabBarState === "SSPI"}><span class="country-details-label"><span class="label-full">SSPI Score:\u0020</span><span class="label-code">SSPI:\u0020</span></span><span class="country-details-score">\u0020${this.activeCountry?.SSPI?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="country-details-score-line" data-active-tab=${this.tabBarState === "SUS"}><span class="country-details-label"><span class="label-full">Sustainability\u0020(SUS):\u0020</span><span class="label-code">SUS:\u0020</span></span><span class="country-details-score">\u0020${this.activeCountry?.SUS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="country-details-score-line" data-active-tab=${this.tabBarState === "MS"}><span class="country-details-label"><span class="label-full">Market Structure\u0020(MS):\u0020</span><span class="label-code">MS:\u0020</span></span><span class="country-details-score">\u0020${this.activeCountry?.MS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="country-details-score-line" data-active-tab=${this.tabBarState === "PG"}><span class="country-details-label"><span class="label-full">Public Goods\u0020(PG):\u0020</span><span class="label-code">PG:\u0020</span></span><span class="country-details-score">\u0020${this.activeCountry?.PG?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
</div>
<div class="country-details-actions">
    <button class="${pinButtonClass}" data-country-code="${this.activeCountry.CCode}">${pinButtonText}</button>
    <button class="focus-country-button" data-country-code="${this.activeCountry.CCode}">Focus Country</button>
    <a class="view-all-data-link" href="/data/country/${this.activeCountry.CCode}">View All Data</a>
</div>
</div>`;

        // Add event listener for Pin/Unpin Country button
        const pinButton = this.countryInformationBox.querySelector('.pin-country-button, .unpin-country-button');
        if (pinButton) {
            pinButton.addEventListener('click', (e) => {
                const countryCode = e.target.dataset.countryCode;
                // Find the feature to toggle
                const feature = this.geojson.features.find(f => f.properties.CCode === countryCode);
                if (feature) {
                    this.togglePin(feature);
                    // Update the active country reference to reflect the new pin state
                    this.activeCountry = feature.properties;
                    // Refresh the country information to update button text
                    this.updateCountryInformation();
                }
            });
        }

        // Add event listener for Focus Country button
        const focusButton = this.countryInformationBox.querySelector('.focus-country-button');
        if (focusButton) {
            focusButton.addEventListener('click', (e) => {
                const countryCode = e.target.dataset.countryCode;
                this.zoomToCountry(countryCode);
            });
        }
    }

    updateDataset() {
        this.setColorScale();
        this.globe
            .polygonsData(this.geojson.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
            .polygonCapColor(feat => {
                // Preserve green color for currently hovered feature
                if (this.hoveredFeature && feat === this.hoveredFeature) {
                    return this.styles.greenAccent;
                }
                return this.colorScale(this.getVal(feat));
            })
            .polygonSideColor(feat => {
                // Preserve hover state for side color
                if (this.hoveredFeature && feat === this.hoveredFeature) {
                    return this.altitudeCoding ? this.styles.greenAccent + 'ef' : this.styles.greenAccent + 'cc';
                }
                return this.altitudeCoding ? this.colorScale(this.getVal(feat)) + 'ef' : "transparent";
            })
            .polygonAltitude(feat => {
                // Handle altitude based on mode and hover state
                if (this.altitudeCoding) {
                    const value = this.getVal(feat);
                    return value >= 0 ? value : 0.01;
                } else {
                    // Preserve elevated altitude for currently hovered feature
                    if (this.hoveredFeature && feat === this.hoveredFeature) {
                        return 0.02;
                    }
                    return 0.01;
                }
            })
            .polygonStrokeColor(this.getStrokeColor())
    }

    updatePolygonLabel() {
        this.globe.polygonLabel(({ properties: d }) => this.getPolygonLabel(d))

        // If currently hovering, manually update the tooltip DOM
        if (this.hoveredCountry) {
            // Find the Globe.gl tooltip element (not our sidebar)
            // Globe.gl creates tooltips as siblings of the scene container
            const tooltipElements = this.globeSceneContainer.parentElement.querySelectorAll('.globegl-hover');
            tooltipElements.forEach(tooltip => {
                // Skip if this is inside our chart options (the sidebar)
                if (!this.chartOptions.contains(tooltip)) {
                    tooltip.outerHTML = this.getPolygonLabel(this.hoveredCountry);
                }
            });
        }
    }

    toggleDarkenBorders() {
        this.darkenBorders = !this.darkenBorders;
        this.globe
            .polygonsData(this.geojson.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
            .polygonStrokeColor(this.getStrokeColor())
    }

    toggleCloropleth(){ 
        this.cloropleth = !this.cloropleth
        this.updateDataset()
    }

    toggleAltitudeCoding(){
        this.altitudeCoding = !this.altitudeCoding;
        if (this.altitudeCoding) {
            this.globe.pointOfView({ altitude: 3 }, 2000)
                .polygonsTransitionDuration(750)
                .polygonSideColor(feat => this.colorScale(this.getVal(feat)) + 'ef')
                .onPolygonHover(hoverD => {
                    this.hoveredCountry = hoverD ? hoverD.properties : null;
                    this.hoveredFeature = hoverD;
                    this.globe
                        .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                        .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'ef' : this.colorScale(this.getVal(d)) + 'ef')
                })
                .polygonAltitude(feat => {
                    const value = this.getVal(feat);
                    return value >= 0 ? value : 0.01;
                })
        } else {
            this.globe.pointOfView({ altitude: 1.5 }, 1500)
                .polygonsTransitionDuration(100)
                .polygonAltitude(feat => this.getVal(feat) / 2)
                .onPolygonHover(hoverD => {
                    this.hoveredCountry = hoverD ? hoverD.properties : null;
                    this.hoveredFeature = hoverD;
                    this.globe
                        .polygonAltitude(d => d === hoverD ? 0.02 : 0.01)
                        .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                        .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'cc' : "transparent")
                })
        }
    }

    toggleGlobeRotation() {
        this.globeRotation = !this.globeRotation;
        this.globe.controls().autoRotate = this.globeRotation;
        this.rotationOnClickToggleButton.disabled = !this.globeRotation;
    }

    toggleRotationOnClick() {
        this.rotationOnClick = !this.rotationOnClick;
    }

    setColorScale() {
        const validValues = this.geojson.features
            .map(this.getVal)
            .filter(v => v !== -1);

        const minVal = Math.min(...validValues);
        const maxVal = Math.max(...validValues);

        console.log(`Value range: [${minVal}, ${maxVal}]`);

        if (this.cloropleth) {
            const colorGrad = SSPIColors.gradients[this.tabBarState];
            this.colorScale = function(value) {
                if (value === -1) {
                    return "#cccccc";
                }
                let decile = Math.ceil((value - minVal) / (maxVal - minVal) * 10);
                return colorGrad[decile];
            }
        } else {
            const newColor = SSPIColors[this.tabBarState];
            this.colorScale = function(value) {
                if (value === -1) {
                    return "#cccccc";
                }
                return newColor;
            }
        }
    };

    buildChartOptions() {
        this.chartOptions = document.createElement('div')
        this.chartOptions.classList.add('chart-options', 'inactive')
        this.chartOptions.innerHTML = `
<div class="hide-chart-button-container">
    <button class="icon-button hide-chart-options" aria-label="Hide Chart Options" title="Hide Chart Options">
        <svg class="hide-chart-options-svg" width="24" height="24">
            <use href="#icon-close" />
        </svg>
    </button>
</div>
<details class="item-information chart-options-details">
    <summary class="item-information-summary">Country Information</summary>
    <div class="country-information-box" data-unpopulated=true>
        Click on a Country to Show Details and Links Here.
    </div>
</details>
<details class="chart-options-details chart-view-options">
    <summary class="chart-view-options-summary">View Options</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Dataset Options</div>
        <div class="chart-view-option">
            <input type="checkbox" class="altitude-toggle"/>
            <label class="title-bar-label">Exploded View</label>
        </div>
        <div class="chart-view-option">
            <input type="checkbox" checked=true class="cloropleth-toggle"/>
            <label class="title-bar-label">Cloropleth</label>
        </div>
        <div class="chart-view-option">
            <input type="checkbox" class="darken-borders-toggle"/>
            <label class="title-bar-label">Darken Borders</label>
        </div>
        <div class="chart-view-subheader">Rotation</div>
        <div class="chart-view-option">
            <input type="checkbox" checked="true" class="globe-rotation-toggle"/>
            <label class="title-bar-label">Globe Rotation</label>
        </div>
        <div class="chart-view-option">
            <input type="checkbox" checked="true" class="rotation-on-click-toggle"/>
            <label class="title-bar-label">Toggle Rotation on Click</label>
        </div>
    </div>
</details>
<details class="select-countries-options chart-options-details">
    <summary class="select-countries-summary">Select Countries</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Pinned Countries</div>
        <div class="legend-title-bar-buttons">
            <div class="pin-actions-box">
                <button class="clearpins-button">Clear Pins</button>
                <button class="add-country-button">Search Country</button>
            </div>
            <div class="country-search-results-window"></div>
        </div>
        <legend class="dynamic-line-legend">
            <div class="legend-items"></div>
        </legend>
    </div>
</details>
<details class="download-data-details chart-options-details">
    <summary>Download Chart Data</summary>
    <form class="panel-download-form">
        <fieldset class="download-scope-fieldset">
            <legend>Select data scope:</legend>
            <label class="download-scope-option"><input type="radio" name="scope" value="pinned" required>Pinned countries</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="visible">Visible countries</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="group">Countries in group</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="all">All available countries</label>
        </fieldset>
        <fieldset class="download-format-fieldset">
            <legend>Choose file format:</legend>
            <label class="download-format-option"><input type="radio" name="format" value="json" required>JSON</label>
            <label class="download-format-option"><input type="radio" name="format" value="csv">CSV</label>
        </fieldset>
        <button type="submit" class="download-submit-button">Download Data</button>
    </form>
</details>
`;
        this.overlay = document.createElement('div')
        this.overlay.classList.add('chart-options-overlay', 'inactive')
        this.overlay.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.root.appendChild(this.overlay)
        const wrapper = document.createElement('div')
        wrapper.classList.add('chart-options-wrapper')
        wrapper.appendChild(this.chartOptions)
        this.root.appendChild(wrapper)
        this.rigChartOptions()
    }

    rigChartOptions() {
        this.hideChartOptions = this.chartOptions.querySelector('.hide-chart-options')
        this.hideChartOptions.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.countryInformationBox = this.chartOptions.querySelector(".country-information-box");
        this.cloroplethToggleButton = this.chartOptions.querySelector(".cloropleth-toggle"); 
        this.cloroplethToggleButton.addEventListener('change', () => {
            this.toggleCloropleth();
        })
        this.altitudeToggleButton = this.chartOptions.querySelector(".altitude-toggle"); 
        this.altitudeToggleButton.addEventListener('change', () => {
            this.toggleAltitudeCoding();
        })
        this.darkenBordersToggleButton = this.chartOptions.querySelector(".darken-borders-toggle");
        this.darkenBordersToggleButton.addEventListener('change', () => {
            this.toggleDarkenBorders();
        })
        this.globeRotationToggleButton = this.chartOptions.querySelector(".globe-rotation-toggle");
        this.globeRotationToggleButton.addEventListener('change', () => {
            this.toggleGlobeRotation();
        })
        this.rotationOnClickToggleButton = this.chartOptions.querySelector(".rotation-on-click-toggle");
        this.rotationOnClickToggleButton.addEventListener('change', () => {
            this.toggleRotationOnClick();
        })
        // Initialize checkbox states from stored values
        this.globeRotationToggleButton.checked = this.globeRotation;
        this.rotationOnClickToggleButton.checked = this.rotationOnClick;
        this.rotationOnClickToggleButton.disabled = !this.globeRotation;
        this.clearPinsButton = this.chartOptions.querySelector('.clearpins-button')
        this.clearPinsButton.addEventListener('click', () => {
            this.clearPins()
        })
        this.countrySearchResultsWindow = this.chartOptions.querySelector('.country-search-results-window')
        this.addCountryButton = this.chartOptions.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            // Create adapter array for CountrySelector, filtering out features without CName/CCode
            const datasetsForSelector = this.geojson.features
                .filter(f => f.properties.CCode && f.properties.CName)
                .map(f => ({
                    CCode: f.properties.CCode,
                    CName: f.properties.CName,
                    borderColor: SSPIColors.get(f.properties.CCode)
                }))
            new CountrySelector(this.addCountryButton, this.countrySearchResultsWindow, datasetsForSelector, this)
        })
        this.legend = this.chartOptions.querySelector('.dynamic-line-legend')
        this.legendItems = this.legend.querySelector('.legend-items')
        const detailsElements = this.chartOptions.querySelectorAll('.chart-options-details')
        let openDetails = window.observableStorage.getItem("openPanelChartDetails")
        detailsElements.forEach((details) => {
            if (openDetails && openDetails.includes(details.classList[0])) {
                details.open = true
            } else {
                details.open = false
            }
        })
        const sidebarStatus = window.observableStorage.getItem("chartOptionsStatus")
        if (sidebarStatus === "active") {
            this.openChartOptionsSidebar()
        } else {
            this.closeChartOptionsSidebar()
        }
        
        this.rigDownloadForm()
    }

    rigDownloadForm() {
        this.downloadForm = this.chartOptions.querySelector('.panel-download-form')
        if (this.downloadForm) {
            this.downloadForm.addEventListener('submit', (e) => {
                e.preventDefault()
                e.stopPropagation()
                this.handleDownloadRequest()
                return false
            })
        }
    }

    handleDownloadRequest() {
        const formData = new FormData(this.downloadForm)
        const scope = formData.get('scope')
        const format = formData.get('format')
        if (!scope || !format) {
            console.error('Missing scope or format in form data')
            alert('Please select both scope and format options')
            return
        }
        
        if (format === 'json') {
            console.log('Calling dumpChartDataJSON with scope:', scope)
            this.dumpChartDataJSON(scope)
        } else if (format === 'csv') {
            console.log('Calling dumpChartDataCSV with scope:', scope)
            this.dumpChartDataCSV(scope)
        } else {
            console.error('Unknown format:', format)
            alert('Unknown format selected')
        }
    }

    shouldIncludeDataset(feature, scope) {
        // Note: This method expects a GeoJSON feature, accesses properties via feature.properties
        const props = feature.properties
        let result
        switch(scope) {
            case 'pinned':
                result = !!props.pinned
                break
            case 'visible':
                // Since we removed the hidden property, visible now means all countries
                result = true
                break
            case 'group':
                // Group functionality not yet implemented for globe
                // Would need this.groupOptions and this.countryGroupSelector
                result = true
                break
            case 'all':
                result = true
                break
            default:
                result = true
                break
        }
        return result
    }

    closeChartOptionsSidebar() {
        this.chartOptions.classList.remove('active')
        this.chartOptions.classList.add('inactive')
        this.overlay.classList.remove('active')
        this.overlay.classList.add('inactive')
    }

    openChartOptionsSidebar() {
        this.chartOptions.classList.add('active')
        this.chartOptions.classList.remove('inactive')
        this.overlay.classList.remove('inactive')
        this.overlay.classList.add('active')
    }

    rigUnloadListener() {
        window.addEventListener('beforeunload', () => {
            window.observableStorage.setItem("globeYear", this.year)
            window.observableStorage.setItem("globePlaying", this.playing)
            window.observableStorage.setItem("globeRotation", this.globeRotation)
            window.observableStorage.setItem("rotationOnClick", this.rotationOnClick)
            if (this.playing) {
                this.stopPlay()
            }
            window.observableStorage.setItem(
                "openPanelChartDetails",
                Array.from(this.chartOptions.querySelectorAll('.chart-options-details'))
                    .filter(details => details.open)
                    .map(details => details.classList[0])
            )
            window.observableStorage.setItem(
                "chartOptionsStatus",
                this.chartOptions.classList.contains('active') ? "active" : "inactive"
            )
        })
    }

    updateLegend() {
        this.legendItems.innerHTML = ''
        if (this.pins.size > 0) {
            this.pins.forEach((PinnedCountry) => {
                const pinSpan = document.createElement('span')
                pinSpan.innerText = PinnedCountry.CName + " (" + PinnedCountry.CCode + ")"
                const removeButton = document.createElement('button')
                removeButton.classList.add('icon-button', 'remove-button-legend-item')
                removeButton.id = `${PinnedCountry.CCode}-remove-button-legend`;
                removeButton.ariaLabel = `Remove ${PinnedCountry.CName} from pinned countries`;
                removeButton.title = `Unpin ${PinnedCountry.CName}`;
                removeButton.innerHTML = `
<svg class="remove-button-legend-item-svg" width="16" height="16">
    <use href="#icon-close" />
</svg>
`;
                const newPin = document.createElement('div')
                newPin.classList.add('legend-item')
                newPin.style.borderColor = PinnedCountry.borderColor
                newPin.style.backgroundColor = PinnedCountry.borderColor + "44"
                newPin.appendChild(pinSpan)
                newPin.appendChild(removeButton)
                this.legendItems.appendChild(newPin)
            })
        }
        let removeButtons = this.legendItems.querySelectorAll('.remove-button-legend-item')
        removeButtons.forEach((button) => {
            let CountryCode = button.id.split('-')[0]
            button.addEventListener('click', () => {
                this.unpinCountryByCode(CountryCode, true)
            })
        })
    }

    getPins() {
        const storedPins = window.observableStorage.getItem('pinnedCountries')
        if (storedPins) {
            this.pins = new Set(storedPins)
        }
        if (this.pins.size === 0) {
            return
        }
        this.geojson.features.forEach(dataset => {
            for (const element of this.pins) {
                if ( dataset.properties.CCode === element.CCode) {
                    dataset.properties.pinned = true
                }
            }
        })
        this.updateLegend()
        this.updateDataset()
    }

    rigPinChangeListener() {
        window.observableStorage.onChange("pinnedCountries", () => {
            this.getPins()
            console.log("Pin change detected!")
        })
    }

    pushPinUpdate() {
        window.observableStorage.setItem("pinnedCountries", Array.from(this.pins))
    }

    pinCountry(feature) {
        if (feature.properties.pinned) {
            return
        }
        feature.properties.pinned = true
        const borderColor = SSPIColors.get(feature.properties.CCode)
        this.pins.add({
            CName: feature.properties.CName,
            CCode: feature.properties.CCode,
            borderColor: borderColor
        })
        this.updateDataset()
        this.pushPinUpdate()
        this.updateLegend()
    }

    unpinCountry(feature) {
        feature.properties.pinned = false
        for (const element of this.pins) {
            if (element.CCode === feature.properties.CCode) {
                this.pins.delete(element)
            }
        }
        this.updateDataset()
        this.pushPinUpdate()
        this.updateLegend()
    }

    pinCountryByCode(countryCode) {
        this.geojson.features.forEach(feature => {
            if (feature.properties.CCode === countryCode) {
                if (!feature.properties.pinned) {
                    const borderColor = SSPIColors.get(feature.properties.CCode)
                    this.pins.add({
                        CName: feature.properties.CName,
                        CCode: feature.properties.CCode,
                        borderColor: borderColor
                    })
                }
                feature.properties.pinned = true
            }
        })
        this.updateDataset()
        this.pushPinUpdate()
        this.updateLegend()

        // Zoom to the pinned country
        this.zoomToCountry(countryCode)
    }

    unpinCountryByCode(countryCode) {
        this.geojson.features.forEach(feature => {
            if (feature.properties.CCode === countryCode) {
                this.unpinCountry(feature)
            }
        })
    }

    togglePin(feature) {
        if (feature.properties.pinned) {
            this.unpinCountry(feature)
        } else {
            this.pinCountry(feature)
        }
    }

    clearPins() {
        this.pins.forEach((PinnedCountry) => {
            this.unpinCountryByCode(PinnedCountry.CCode)
        })
        this.pins = new Set()
        this.updateLegend()
        this.pushPinUpdate()
    }

    /**
     * Zooms the globe to focus on a given bounding box
     * @param {Array} bbox - Bounding box in format [minLng, minLat, maxLng, maxLat]
     * @param {number} duration - Animation duration in milliseconds (default: 1000)
     * @param {number} paddingFactor - Additional zoom out factor for padding (default: 1.2)
     */
    zoomToBoundingBox(bbox, duration = 1000, paddingFactor = 1.2) {
        if (!bbox || bbox.length !== 4) {
            console.error('Invalid bounding box format. Expected [minLng, minLat, maxLng, maxLat]');
            return;
        }

        // Pause globe rotation when zooming
        if (this.globe.controls().autoRotate) {
            this.globe.controls().autoRotate = false;
            this.globeRotation = false;
            if (this.globeRotationToggleButton) {
                this.globeRotationToggleButton.checked = false;
            }
            window.observableStorage.setItem("globeRotation", false);
        }

        const [minLng, minLat, maxLng, maxLat] = bbox;

        // Calculate the center point of the bounding box
        let centerLng = (minLng + maxLng) / 2;
        let centerLat = (minLat + maxLat) / 2;

        // Handle bounding boxes that cross the International Date Line
        if (minLng > maxLng) {
            // Bbox crosses the antimeridian
            centerLng = ((minLng + maxLng + 360) / 2) % 360;
            if (centerLng > 180) centerLng -= 360;
        }

        // Calculate the span of the bounding box
        let lngSpan = maxLng - minLng;
        if (minLng > maxLng) {
            // Handle wraparound at International Date Line
            lngSpan = (360 - minLng) + maxLng;
        }
        const latSpan = maxLat - minLat;

        // Use the maximum span to determine altitude
        // Account for latitude distortion (longitude degrees are smaller near poles)
        const avgLat = Math.abs(centerLat);
        const lngSpanAdjusted = lngSpan * Math.cos(avgLat * Math.PI / 180);
        const maxSpan = Math.max(latSpan, lngSpanAdjusted);

        // Calculate altitude based on the span
        // The formula is calibrated so that:
        // - Small bbox (10°): altitude ≈ 0.875-1.0 (close view)
        // - Medium bbox (40°): altitude ≈ 1.25 (country view)
        // - Large bbox (80°): altitude ≈ 1.75 (continent view)
        // - Very large bbox (160°): altitude ≈ 2.75 (global view)
        const baseAltitude = (maxSpan / 40 + 1.5) / 2;
        const altitude = baseAltitude * paddingFactor;

        // Clamp altitude to reasonable bounds (lower than before for closer view)
        const finalAltitude = Math.max(0.8, Math.min(altitude, 4));

        // Animate to the new point of view
        this.globe.pointOfView({
            lat: centerLat,
            lng: centerLng,
            altitude: finalAltitude
        }, duration);

        console.log(`Zooming to bbox [${minLng}, ${minLat}, ${maxLng}, ${maxLat}]`);
        console.log(`Center: (${centerLat.toFixed(2)}°, ${centerLng.toFixed(2)}°), Altitude: ${finalAltitude.toFixed(2)}`);
    }

    /**
     * Zooms to a specific country by its country code
     * @param {string} countryCode - The country code (CCode) to zoom to
     * @param {number} duration - Animation duration in milliseconds (default: 1000)
     */
    zoomToCountry(countryCode, duration = 1000) {
        const feature = this.geojson.features.find(f => f.properties.CCode === countryCode);

        if (!feature) {
            console.error(`Country with code "${countryCode}" not found`);
            return;
        }

        if (!feature.bbox) {
            console.error(`Country "${countryCode}" does not have a bounding box`);
            return;
        }

        this.zoomToBoundingBox(feature.bbox, duration);
    }
}

