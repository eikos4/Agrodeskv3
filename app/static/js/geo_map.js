// static/js/geo_map.js
(function(){
  // Crea mapa
  const c = window.__MAP_CENTER__ || {lat:-36.82,lng:-73.05,zoom:8};
  const map = L.map('map').setView([c.lat, c.lng], c.zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  function styleByTipo(tipo){
    const s = (window.__ACTIVITY_STYLES__ && window.__ACTIVITY_STYLES__[tipo]) || window.__ACTIVITY_STYLES__?.otra || {color:'#6c757d',fill:'#6c757d33',icon:'bi-geo'};
    return { color: s.color, weight: 3, opacity: 0.9, fillColor: s.fill || s.color, fillOpacity: 0.2 };
  }

  const parcelasLayer = L.geoJSON(null, {
    style: { color:'#198754', weight:2, fillColor:'#19875433', fillOpacity:.2 }
  }).addTo(map);

  const actividadesLayer = L.geoJSON(null, {
    style: f => styleByTipo(f.properties?.tipo),
    pointToLayer: (f, latlng) => L.circleMarker(latlng, styleByTipo(f.properties?.tipo)),
    onEachFeature: (f, layer) => {
      const s = window.__ACTIVITY_STYLES__?.[f.properties?.tipo] || {};
      layer.bindPopup(`
        <div class="small">
          <div class="fw-semibold mb-1"><i class="bi ${s.icon||'bi-geo'}"></i> ${f.properties?.tipo||''}</div>
          <div><b>Fecha:</b> ${f.properties?.fecha||'-'}</div>
          ${f.properties?.parcela ? `<div><b>Parcela:</b> ${f.properties.parcela}</div>`:''}
          ${f.properties?.descripcion ? `<div class="mt-2">${f.properties.descripcion}</div>`:''}
        </div>
      `);
    }
  }).addTo(map);

  // Carga datos
  fetch('/geo/api/parcelas').then(r=>r.json()).then(fc=>{
    parcelasLayer.clearLayers(); parcelasLayer.addData(fc);
    try { map.fitBounds(parcelasLayer.getBounds(), {padding:[20,20]}); } catch(e){}
  });

  fetch('/geo/api/actividades').then(r=>r.json()).then(fc=>{
    actividadesLayer.clearLayers(); actividadesLayer.addData(fc);
  });

  // Leyenda
  if (window.__ACTIVITY_STYLES__){
    const legend = L.control({position:'bottomleft'});
    legend.onAdd = function(){
      const div = L.DomUtil.create('div','leaflet-control leaflet-bar p-2 bg-white shadow');
      div.innerHTML = '<div class="fw-semibold mb-1">Actividades</div>' +
        Object.entries(window.__ACTIVITY_STYLES__).map(([k,s])=>`
          <div class="d-flex align-items-center gap-2 mb-1">
            <span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:${s.color}66;border:2px solid ${s.color}"></span>
            <span class="small">${s.nombre||k}</span>
          </div>`).join('');
      return div;
    };
    legend.addTo(map);
  }
})();
