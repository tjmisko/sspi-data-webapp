class GlobeVisualization {
    constructor() {
        this.initalizeGlobe();
    }

    initalizeGlobe() {
      const colorScale = d3.scaleSequentialSqrt(d3.interpolateYlOrRd);

      // GDP per capita (avoiding countries with small pop)
      const getVal = feat => feat.properties.GDP_MD_EST / Math.max(1e5, feat.properties.POP_EST);

      fetch("{{ url_for('client_bp.static', filename = 'globe_data.geojson') }}").then(res => res.json()).then(countries =>
      {
        const maxVal = Math.max(...countries.features.map(getVal));
        colorScale.domain([0, maxVal]);
        console.log(countries.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
        const world = Globe()
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .backgroundColor("#1B2A3C")
          .width("500")
          .height("500")
          .showGraticules(true)
          .atmosphereColor("green")
          .lineHoverPrecision(0)
          .polygonsData(countries.features.filter(d => d.properties.ISO_A2 !== 'AQ'))
          .polygonAltitude(0.01)
          .polygonCapColor(feat => colorScale(getVal(feat)))
          .polygonSideColor(() => 'rgba(0, 100, 0, 0.15)')
          .polygonStrokeColor(() => '#111')
          .polygonLabel(({ properties: d }) => `
            <div class="globegl-hover"
              <b>${d.ADMIN} (${d.ISO_A2}):</b> <br />
              GDP: <i>${d.GDP_MD_EST}</i> M$<br/>
              Population: <i>${d.POP_EST}</i>
            </div>
          `)
          .onPolygonHover(hoverD => world
            .polygonAltitude(d => d === hoverD ? 0.10 : 0.01)
            .polygonCapColor(d => d === hoverD ? '#294b50' : colorScale(getVal(d)))
          )
          .polygonsTransitionDuration(200)
          .pointOfView({lat: 25, lng: 60, altitude: 2}, 500)
        (document.getElementById('globeViz'))
        world.controls().autoRotate = true
        world.controls().autoRotateSpeed = 0.3
        world.controls().enableZoom = false;
      });
    }
}