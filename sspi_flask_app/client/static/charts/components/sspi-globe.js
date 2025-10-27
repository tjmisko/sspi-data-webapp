class SSPIGlobeChart {
    constructor(parentElement, globeDataURL) {
        this.parentElement = parentElement
        this.globeDataURL = globeDataURL
        this.tabBarState = "SSPI"; // load a globe for SSPI by default
        this.getVal = feat => feat.properties.GDP_MD_EST / Math.max(1e5, feat.properties.POP_EST);
        this.computeGlobeDimensions() 
        this.getComputedStyles()
        this.buildGlobeContainer() 
        this.buildTabBar() 
        this.buildGlobe()
        this.hydrateGlobe().then(this.restyleGlobe())
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
        this.globeContainer = document.createElement("div");
        this.globeContainer.classList.add("globe-visualization-container");
        this.parentElement.appendChild(this.globeContainer)
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
                this.tabBarUpdate()
                this.updateDataset()
            });
        }
        this.globeContainer.appendChild(this.tabBar)
    }


    tabBarUpdate() {
        // Update the visual state of the tabbar to show the currently selected dataset
    }


    buildGlobe() {
        this.globeSceneContainer = document.createElement("div");
        this.globeContainer.appendChild(this.globeSceneContainer)
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
        this.setColorScale(SSPIColors.SSPI);
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
                console.log(p.properties.ISO_A3);
            })
            .polygonLabel(({ properties: d }) => `
<div class="globegl-hover">
<h3>${d.ADMIN}\u0020(${d.ISO_A3}):</h3><br/>
GDP:\u0020<i>${d.GDP_MD_EST}</i> M$<br/>
Population:\u0020<i>${d.POP_EST}</i>
</div>
`)
    }

    restyleGlobe() {
        this.globe.backgroundColor(this.styles.boxBackgroundColor)
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
        const newColor = SSPIColors[this.tabBarState]
        this.getVal = feat => {feat.properties[this.tabBarState]};
        this.setColorScale(newColor);
        this.globe
            .polygonCapColor(feat => this.colorScale(this.getVal(feat)))
            .polygonSideColor(feat => "transparent")
            .onPolygonHover(hoverD => this.globe
                .polygonAltitude(d => d === hoverD ? 0.02 : 0.01)
                .polygonSideColor(d => d === hoverD ? this.styles.greenAccent + 'cc' : "transparent")
                .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
            )
            .onPolygonClick((p) => {
                console.log(p.target);
            })
    }

    toggleAltitudeCoding(){};

    setColorScale(newColor) {
        const maxVal = Math.max(...this.geojson.features.map(this.getVal));
        console.log(newColor);
        if (!maxVal) {
            this.colorScale = function(value) { return newColor }
        } else {
            this.colorScale = function(value) { return newColor }
        }
    };
}
