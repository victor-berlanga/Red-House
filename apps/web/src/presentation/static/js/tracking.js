'use strict';
(() => {
  const root = document.getElementById('tracking');
  if (!root) return;
  const text = (id, value) => { document.getElementById('tracking-' + id).textContent = value; };
  const isSimulated = position => position?.source === 'SIMULATOR' || position?.simulated === true;
  const sourceLabel = position => ({SIMULATOR:'Simulador', GPS_BRIDGE:'Puente GPS', ANDROID:'Teléfono Android', IOS:'Teléfono iPhone'}[position.source] || 'Desconocida') + (isSimulated(position) ? ' · SIMULADO' : '');
  const initial = JSON.parse(root.dataset.snapshot);
  const policy = JSON.parse(root.dataset.policy), provider = JSON.parse(root.dataset.provider);
  root.dataset.snapshot = '';
  let cursor = initial.cursor, latest = null, marker, socket, timer, heartbeat, stopped = false, connected = false, attempt = 0;
  let terminal = initial.state === 'FINALIZED', serverState = initial.state;
  const points = new Map(), bounds = [[23.1, -101.3], [27.85, -98.35]];
  const map = L.map('tracking-map', {scrollWheelZoom: false}).fitBounds(bounds);
  const credit = document.createElement('a'); credit.href = provider.attribution_url; credit.textContent = provider.attribution;
  const tiles = L.tileLayer(provider.url, {
    maxZoom: 19, attribution: credit.outerHTML,
  }).addTo(map);
  tiles.on('tileload', () => { root.dataset.tilesLoaded = String(Number(root.dataset.tilesLoaded || 0) + 1); });
  tiles.on('tileerror', () => text('tiles', 'Cartografía no disponible. Puedes continuar usando el portal.'));
  for (const anchor of JSON.parse(root.dataset.anchors)) {
    if (anchor.latitude == null || anchor.longitude == null) continue;
    const label = document.createElement('span'); label.textContent = anchor.label + ': ' + anchor.name + (anchor.synthetic ? ' · SINTÉTICO' : '');
    L.circleMarker([anchor.latitude,anchor.longitude], {radius:7,color:anchor.label === 'Origen' ? '#176338' : '#224c91'}).addTo(map).bindTooltip(label, {permanent:true});
  }
  const line = L.polyline([], {color: '#a51c30', weight: 3}).addTo(map);
  function status() {
    const age = latest ? Math.max(0, Math.floor((Date.now() - Date.parse(latest.captured_at)) / 1000)) : null;
    text('age', age === null ? 'Sin datos' : age + ' s');
    const state = terminal ? 'Finalizado o sin permiso de rastreo' : !connected ? 'Desconectado · último dato conservado' : !latest ? 'Sin señal · sin datos' : !latest.fix_valid ? 'Sin señal GPS' : age > policy.tracking_stale_seconds ? 'Retrasado · última observación' : 'En vivo';
    text('status', state + (isSimulated(latest) ? ' · SIMULADO' : ''));
  }
  function receive(position) {
    if (!position) return;
    {
      const existed = points.has(position.event_id);
      points.set(position.event_id, position);
      if (points.size > 1000) points.delete(points.keys().next().value);
      const ordered = [...points.values()].sort((a,b) => Date.parse(a.captured_at)-Date.parse(b.captured_at) || a.cursor-b.cursor);
      line.setLatLngs(ordered.filter(p=>p.fix_valid).map(p => [p.latitude,p.longitude]));
      if (!existed) {
        const tr = document.createElement('tr'); tr.dataset.eventId = position.event_id;
        for (const value of [new Date(position.captured_at).toLocaleString('es-MX',{timeZone:root.dataset.timezone}), sourceLabel(position), position.fix_valid ? 'Válida' : 'Sin señal', position.latitude ?? 'No informada', position.longitude ?? 'No informada', position.accuracy_m == null ? 'No informada' : position.accuracy_m + ' m']) {
          const td=document.createElement('td'); td.textContent=String(value); tr.append(td);
        }
        const history=document.getElementById('tracking-history'); history.append(tr); if (history.rows.length>1000) history.firstElementChild.remove();
      }
      root.dataset.lastEventId = position.event_id;
      requestAnimationFrame(()=>root.dispatchEvent(new CustomEvent('redhouse:position-rendered', {detail:{event_id:position.event_id, shipment_id:position.shipment_id, cursor:position.cursor, received_at:position.received_at, rendered_at:new Date().toISOString(), receive_to_map_ms:Date.now()-Date.parse(position.received_at)}})));
    }
    // Late replay never moves the current marker backwards in capture time.
    if (latest && Date.parse(position.captured_at) < Date.parse(latest.captured_at)) return;
    latest = position;
    text('source', sourceLabel(position));
    text('time', new Date(position.captured_at).toLocaleString('es-MX', {timeZone:root.dataset.timezone}));
    text('accuracy', position.accuracy_m == null ? 'No informada' : position.accuracy_m + ' m');
    if (position.fix_valid) {
      const coords = [position.latitude, position.longitude];
      if (marker) marker.setLatLng(coords); else marker = L.circleMarker(coords, {radius: 9, color: '#a51c30'}).addTo(map);
      text('coordinate', coords.join(', '));
      text('coordinate-time', new Date(position.captured_at).toLocaleString('es-MX',{timeZone:root.dataset.timezone}));
      text('outside', position.latitude<bounds[0][0] || position.latitude>bounds[1][0] || position.longitude<bounds[0][1] || position.longitude>bounds[1][1] ? 'Posición fuera del encuadre inicial de Nuevo León. Usa «Ver última posición»; la observación se conserva sin corregirla.' : '');
    }
    status();
  }
  for (const position of initial.events || []) receive(position);
  receive(initial.position); status();
  function endAccess() {
    terminal=true; points.clear(); line.setLatLngs([]); marker?.remove(); marker=null; latest=null;
    document.getElementById('tracking-history').replaceChildren();
    for (const field of ['source','time','accuracy','coordinate','coordinate-time']) text(field,'Acceso terminado');
    root.dataset.lastEventId=''; status();
  }
  const send = message => socket?.readyState === WebSocket.OPEN && socket.send(JSON.stringify(message));
  function retry() {
    connected = false; clearInterval(heartbeat); status();
    if (!stopped && !terminal) timer = setTimeout(connect, Math.min(30000, 1000 * 2 ** Math.min(attempt++,5)) + Math.random()*500);
  }
  async function connect() {
    clearTimeout(timer);
    if (stopped || terminal) return;
    if (location.protocol !== 'https:') { text('status', 'El seguimiento en vivo requiere HTTPS/WSS. Última observación conservada.'); return; }
    try {
      const response = await fetch(root.dataset.access, {method:'POST', headers:{'X-CSRFToken':root.dataset.csrf}, redirect:'manual', signal:AbortSignal.timeout(10000)});
      if (response.type === 'opaqueredirect' || [401,403,404].includes(response.status)) { endAccess(); return; }
      if (!response.ok) throw new Error('access');
      const ticket = await response.json();
      if (stopped) return;
      socket = new WebSocket('wss://' + location.host + '/services/transporte/ws/v1/tracking/json', 'redhouse.tracking.v1.json');
      socket.onopen = () => { send({type:'authenticate',credential_kind:'browser',credential:ticket.credential}); ticket.credential = ''; };
      socket.onmessage = event => {
        const message = JSON.parse(event.data);
        if (message.type === 'authenticated') {
          send({type:'subscribe',shipment_id:root.dataset.shipment,cursor});
          heartbeat = setInterval(() => send({type:'heartbeat'}),20000);
        } else if (message.type === 'subscribed') {
          connected = true; attempt = 0; serverState = message.state; receive(message.position); status();
          // Cursor belongs to replay delivery, not the latest observed position.
        } else if (message.type === 'position.updated') {
          receive(message.position); cursor = message.cursor;
        } else if (message.type === 'tracking.status') {
          serverState = message.state; status();
        } else if (message.type === 'resync.required') {
          points.clear(); line.setLatLngs([]); cursor = null;
          document.getElementById('tracking-history').replaceChildren();
          text('recovery','El cursor salió de la ventana de recuperación. Se obtiene una instantánea nueva; no se inventan los puntos ausentes.');
          send({type:'subscribe',shipment_id:root.dataset.shipment});
        } else if (message.type === 'error') {
          if (['forbidden','tracking_closed'].includes(message.code)) endAccess();
          socket.close();
        }
        if (message.type === 'subscribed' && cursor == null) cursor = message.cursor;
      };
      socket.onerror = () => socket.close();
      socket.onclose = retry;
    } catch { retry(); }
  }
  document.getElementById('tracking-state').onclick = () => { map.invalidateSize({pan:false}); map.fitBounds(bounds,{animate:false}); };
  document.getElementById('tracking-focus').onclick = () => { if (marker) { map.invalidateSize({pan:false}); map.setView(marker.getLatLng(),14,{animate:false}); } };
  document.getElementById('tracking-retry').onclick = () => { if (socket && socket.readyState < 2) socket.close(); else { terminal = false; connect(); } };
  const ageTimer = setInterval(status,1000);
  addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); clearInterval(heartbeat); clearInterval(ageTimer); socket?.close(); });
  connect();
})();
