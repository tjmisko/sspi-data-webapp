class SSPIGlobeChart {
    constructor(parentElement, globeDataURL) {
        this.parentElement = parentElement
        this.globeDataURL = globeDataURL
        this.colorScale = d3.scaleSequentialSqrt(d3.interpolateYlOrRd);
        // GDP per capita (avoiding countries with small pop)
        this.getVal = feat => feat.properties.GDP_MD_EST / Math.max(1e5, feat.properties.POP_EST);

        this.computeGlobeDimensions() 
        this.getComputedStyles()
        this.buildGlobe()
        this.setSceneLighting()
        this.hydrateGlobe().then(this.restyleGlobe())
    }

    computeGlobeDimensions() {
        if (window.screen.width < 600) {
            this.globeWidth = window.screen.width
            this.globeHeight = window.screen.height
        } else {
            this.globeWidth = 600;
            this.globeHeight = 600;
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


    buildGlobe() {
        this.globe = Globe()
            .width(this.globeWidth.toString())
            .height(this.globeHeight.toString())
            .showGraticules(false)
            .showAtmosphere(false)
            .lineHoverPrecision(0)
            .polygonAltitude(0.01)
            .polygonSideColor(() => 'rgba(0, 0, 0, 0.15)')
            .polygonStrokeColor(() => 'transparent')
            .polygonsTransitionDuration(200)
            .pointOfView({lat: 25, lng: 60, altitude: 1.5}, 500)
            (document.getElementById('globeViz'))
    } 

    setSceneLighting() {
      // this.globe.lights([]) 
    }

    async hydrateGlobe () {
        let countries = await fetch(this.globeDataURL).then(res => res.json())
        const maxVal = Math.max(...countries.features.map(this.getVal));
        this.colorScale.domain([0, maxVal]);
        this.globe
            .polygonsData(countries.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
            .polygonCapColor(feat => this.colorScale(this.getVal(feat)))
            .onPolygonHover(hoverD => this.globe
                .polygonAltitude(d => d === hoverD ? 0.05 : 0.01)
                .polygonCapColor(d => d === hoverD ? this.styles.greenAccent : this.colorScale(this.getVal(d)))
            )
            .onPolygonClick((p, e) => {
                console.log(p);
                console.log(e);
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
        this.globe.backgroundColor(this.styles.pageBackgroundColor)
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
}
