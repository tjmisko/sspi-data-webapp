class SSPIGlobeChart {
    constructor(parentElement) {
        this.parentElement = parentElement
        this.globeDataURL = "/api/v1/globe"
        this.tabBarState = "SSPI"; // load a globe for SSPI by default
        this.year = 2023;
        this.altitudeCoding = false;
        this.cloropleth = true;
        this.darkenBorders = false;
        this.pins = new Set() // pins contains a list of pinned countries
        this.pinnedOnly = window.observableStorage.getItem("pinnedOnly") || false
        this.computeGlobeDimensions() 
        this.getComputedStyles()
        this.buildGlobeContainer() 
        this.buildGlobe()
        this.hydrateGlobe().then(this.restyleGlobe())
        this.setTheme(window.observableStorage.getItem("theme"))
        this.rigPinChangeListener()
        this.rigUnloadListener()
    }

    computeGlobeDimensions() {
        if (window.screen.width < 800) {
            this.globeWidth = window.screen.width
            this.globeHeight = window.screen.height
        } else {
            this.globeWidth = 800;
            this.globeHeight = 800;
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
            });
        }
        this.globeAndTabContainer.appendChild(this.tabBar)
    }

    buildGlobe() {
        this.globeAndTabContainer = document.createElement("div");
        this.globeAndTabContainer.classList.add('globe-and-tab-container')
        this.buildTabBar() 
        this.globeSceneContainer = document.createElement("div");
        this.globeAndTabContainer.appendChild(this.globeSceneContainer)
        this.root.appendChild(this.globeAndTabContainer)
        this.globe = Globe()
            .width(this.globeWidth.toString())
            .height(this.globeHeight.toString())
            .showGraticules(false)
            .showAtmosphere(false)
            .lineHoverPrecision(0)
            .polygonAltitude(0.01)
            .polygonStrokeColor(() => 'rgba(0, 0, 0, 0.10)')
            .polygonsTransitionDuration(100)
            .pointOfView({lat: 25, lng: 60, altitude: 1.5}, 500)
            (this.globeSceneContainer)
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
            .onPolygonHover(hoverD => this.globe
                .polygonAltitude(d => d === hoverD ? 0.02 : 0.01)
                .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'cc' : "transparent")
            )
            .onPolygonClick((p, e) => {
                this.globe.controls().autoRotate = !this.globe.controls().autoRotate;
                const d = p.properties;
                this.countryInformatonBox.dataset.unpopulated = false;
                this.countryInformationBox.innerHTML = `
<div class="globegl-hover">
<h3>${d.CFlag}\u0020${d.CName}\u0020(${d.CCode})</h3>
<div class="globegl-hover-score-container">
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SSPI"}><span class="globe-hover-item-label">SSPI Score:\u0020</span><span class="globe-hover-item-score">\u0020${d?.SSPI?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SUS"}><span class="globe-hover-item-label">Sustainability\u0020(SUS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.SUS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "MS"}><span class="globe-hover-item-label">Market Structure\u0020(MS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.MS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "PG"}><span class="globe-hover-item-label">Public Goods\u0020(PG):\u0020</span><span class="globe-hover-item-score">\u0020${d?.PG?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
</div>
</div>`;
            })
            .polygonLabel(({ properties: d }) => `
<div class="globegl-hover">
<h3>${d.CFlag}\u0020${d.CName}\u0020(${d.CCode})</h3>
<div class="globegl-hover-score-container">
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SSPI"}><span class="globe-hover-item-label">SSPI Score:\u0020</span><span class="globe-hover-item-score">\u0020${d?.SSPI?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "SUS"}><span class="globe-hover-item-label">Sustainability\u0020(SUS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.SUS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "MS"}><span class="globe-hover-item-label">Market Structure\u0020(MS):\u0020</span><span class="globe-hover-item-score">\u0020${d?.MS?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
    <div class="globegl-hover-score-line" data-active-tab=${this.tabBarState === "PG"}><span class="globe-hover-item-label">Public Goods\u0020(PG):\u0020</span><span class="globe-hover-item-score">\u0020${d?.PG?.[this.year - 2000]?.toFixed(3) ?? "N/A"}</span></div>
</div>
</div>
`)
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
        this.globe.controls().autoRotate = true
        this.globe.controls().autoRotateSpeed = 0.3
        this.globe.controls().enableZoom = true;
    }

    setTheme(theme) {
        this.getComputedStyles()
        this.restyleGlobe()
    }

    updateDataset() {
        this.setColorScale();
        this.globe
            .polygonCapColor(feat => this.colorScale(this.getVal(feat)))
    }

    toggleDarkenBorders() {
        this.darkenBorders = !this.darkenBorders;
        if (this.darkenBorders) {
            this.globe.polygonStrokeColor(() => 'rgba(0, 0, 0, 1)')
        } else { 
            this.globe.polygonStrokeColor(() => 'rgba(0, 0, 0, 0.1)')
        }
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
                .onPolygonHover(hoverD => this.globe
                    .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                    .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'ef' : this.colorScale(this.getVal(d)) + 'ef')
                )
                .polygonAltitude(feat => {
                    const value = this.getVal(feat);
                    return value >= 0 ? value : 0.01;
                })
        } else {
            this.globe.pointOfView({ altitude: 1.5 }, 1500)
                .polygonsTransitionDuration(100)
                .polygonAltitude(feat => this.getVal(feat) / 2)
                .onPolygonHover(hoverD => this.globe
                    .polygonAltitude(d => d === hoverD ? 0.02 : 0.01)
                    .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
                    .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'cc' : "transparent")
                )
        }
    }

    setColorScale() {
        const maxVal = Math.max(...this.geojson.features.map(this.getVal));
        console.log(maxVal)
        if (maxVal && !maxVal.isNaN && this.cloropleth) {
            let colorGrad = SSPIColors.gradients[this.tabBarState]
            this.colorScale = function(value) { 
                if (value == -1) {
                    return "#cccccc";
                }
                let decile = Math.ceil(value / maxVal * 10);
                return colorGrad[decile]
            }
        } else {
            const newColor = SSPIColors[this.tabBarState]
            this.colorScale = function(value) { 
                if (value == -1) {
                    return "#cccccc";
                }
                return newColor
            }
        }
    };

    buildChartOptions() {
        this.chartOptions = document.createElement('div')
        this.chartOptions.classList.add('chart-options')
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
    </div>
</details>
<details class="select-countries-options chart-options-details">
    <summary class="select-countries-summary">Select Countries</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Pinned Countries</div>
        <div class="legend-title-bar-buttons">
            <div class="pin-actions-box">
                <button class="hideunpinned-button">Hide Unpinned</button>
                <button class="clearpins-button">Clear Pins</button>
            </div>
            <div class="pin-actions-box">
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
        this.showChartOptions = document.createElement('button')
        this.showChartOptions.classList.add("icon-button", "show-chart-options")
        this.showChartOptions.ariaLabel = "Show Chart Options"
        this.showChartOptions.title = "Show Chart Options"
        this.showChartOptions.innerHTML = `
<svg class="svg-button show-chart-options-svg" width="24" height="24">
    <use href="#icon-menu" />
</svg>
`;
        this.root.appendChild(this.showChartOptions)
        this.overlay = document.createElement('div')
        this.overlay.classList.add('chart-options-overlay')
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
        this.hideUnpinnedButton = this.chartOptions.querySelector('.hideunpinned-button')
        this.hideUnpinnedButton.addEventListener('click', () => {
            this.hideUnpinned()
        })
        this.clearPinsButton = this.chartOptions.querySelector('.clearpins-button')
        this.clearPinsButton.addEventListener('click', () => {
            this.clearPins()
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

    shouldIncludeDataset(dataset, scope) {
        let result
        switch(scope) {
            case 'pinned':
                result = !!dataset.pinned
                break
            case 'visible':
                result = !dataset.hidden
                break
            case 'group':
                const activeGroup = this.groupOptions[this.countryGroupSelector.selectedIndex]
                result = dataset.CGroup && dataset.CGroup.includes(activeGroup)
                break
            case 'all':
                result = true
                break
            default:
                result = !dataset.hidden
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
                    dataset.properties.hidden = false
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

    showAll() {
        this.pinnedOnly = false
        window.observableStorage.setItem("pinnedOnly", false)
        console.log('Showing all countries')
        this.geojson.features.forEach((dataset) => {
            dataset.properties.hidden = false
        })
        this.updateDataset()
    }
}

