/* Comparte actividad y avisos entre pestañas; nunca credenciales ni capturas. */
(() => {
  'use strict';
  const dialog = document.getElementById('session-dialog');
  if (!dialog) return;
  const text = dialog.querySelector('[data-session-message]');
  const renew = dialog.querySelector('[data-session-renew]');
  const channel = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('red-house-session') : null;
  const warningWindow = 300000, activityWindow = 300000;
  let deadline = 0, busy = false, syncing = false, expired = false, focused, epoch = 0;
  let lastActivity = document.hidden ? 0 : Date.now(), lastBroadcast = 0, retryAt = 0;

  async function request(url, options = {}) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 10000);
    try { return await fetch(url, {...options, signal:controller.signal}); }
    finally { clearTimeout(timer); }
  }
  function show(message) {
    if (text.textContent !== message) text.textContent = message;
    if (!dialog.open) { focused = document.activeElement; dialog.showModal(); }
  }
  function close() {
    if (dialog.open) { dialog.close(); focused?.focus({preventScroll:true}); }
  }
  function end() {
    if (expired) return;
    expired = true; epoch++;
    window.dispatchEvent(new Event('session-ended'));
    window.location.replace('/login');
  }
  function apply(state) {
    deadline = Date.now() + (state.expires_at - state.server_time) * 1000;
    if (state.csrf_token) document.querySelectorAll('[name=csrf_token]').forEach(e => { e.value = state.csrf_token; });
    if (deadline - Date.now() > warningWindow) close();
  }
  async function sync() {
    if (busy || syncing || expired) return;
    syncing = true;
    const seen = epoch;
    try {
      const res = await request('/sesion/estado', {cache:'no-store'});
      if (seen !== epoch) return;
      if (res.status === 401) { end(); return; }
      if (!res.ok) throw Error();
      const state = await res.json();
      if (seen !== epoch) return;
      apply(state);
      if (deadline <= Date.now()) end();
      else tick();
    } catch {
      if (seen !== epoch || expired) return;
      if (deadline && deadline <= Date.now()) end();
      else if (dialog.open) text.textContent = 'No se pudo comprobar la conexión. Reintenta continuar antes de que termine la sesión.';
    } finally { syncing = false; }
  }
  async function continueSession() {
    if (busy || expired) return;
    busy = true; epoch++; renew.disabled = true;
    const seen = epoch;
    let conflict = false;
    try {
      const res = await request('/sesion/continuar', {
        method:'POST', headers:{'X-CSRFToken':dialog.querySelector('[name=csrf_token]').value}
      });
      if (seen !== epoch || expired) return;
      if (res.status === 401) { end(); return; }
      if (res.status === 409) {
        // Otra pestaña está rotando el mismo token. Consultar antes de reintentar.
        retryAt = Date.now() + 5000; conflict = true; return;
      }
      if (!res.ok) throw Error();
      const state = await res.json();
      if (seen !== epoch || expired) return;
      apply(state); retryAt = 0;
      channel?.postMessage('renewed'); close();
    } catch {
      if (!expired && seen === epoch) {
        retryAt = Date.now() + 30000;
        show('No se pudo renovar la sesión automáticamente. Comprueba la conexión y pulsa Continuar sesión para reintentar.');
      }
    } finally {
      busy = false; renew.disabled = false;
      if (conflict) setTimeout(sync, 1000);
    }
  }
  function tick() {
    if (!deadline || expired || busy) return;
    const remaining = deadline - Date.now();
    // Tras suspender una pestaña, otra pudo haber renovado su vencimiento.
    if (remaining <= 0) { void sync(); return; }
    if (remaining > warningWindow || Date.now() < retryAt) return;
    if (Date.now() - lastActivity < activityWindow) {
      void continueSession();
    } else {
      show('No hemos detectado actividad reciente y tu sesión está por finalizar. ¿Quieres continuar? Conservarás los datos que estás capturando.');
    }
  }
  function activity(event) {
    // Los refrescos del listado, eventos programáticos y pestañas ocultas no prolongan la sesión.
    if (!event.isTrusted || document.hidden || expired) return;
    lastActivity = Date.now();
    if (lastActivity - lastBroadcast >= 5000) {
      lastBroadcast = lastActivity;
      channel?.postMessage({type:'activity', at:lastActivity});
    }
    if (!event.target.closest?.('[data-session-renew]')) tick();
  }
  ['pointerdown', 'pointermove', 'keydown', 'input', 'wheel', 'touchstart'].forEach(name => {
    document.addEventListener(name, activity, {capture:true, passive:true});
  });
  renew.addEventListener('click', continueSession);
  dialog.addEventListener('cancel', event => event.preventDefault());
  document.querySelectorAll('form[action="/logout"]').forEach(form => form.addEventListener('submit', () => {
    expired = true; epoch++; channel?.postMessage('logout');
  }));
  if (channel) channel.onmessage = event => {
    if (event.data === 'logout') end();
    else if (event.data === 'renewed') { if (!busy) { epoch++; void sync(); } }
    else if (event.data?.type === 'activity') {
      const at = event.data.at;
      if (Number.isFinite(at) && at <= Date.now() && Date.now() - at < activityWindow) {
        lastActivity = Math.max(lastActivity, at); tick();
      }
    }
  };
  document.addEventListener('visibilitychange', () => { if (!document.hidden) void sync(); });
  window.addEventListener('pageshow', sync);
  setInterval(tick, 1000); setInterval(sync, 60000); void sync();
})();
