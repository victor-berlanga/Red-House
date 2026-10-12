'use strict';
// Cambia la presentación de instantes, sin reconstruir páginas ni perder borradores.
(() => {
  const form = document.querySelector('.timezone-picker');
  if (!form || !window.fetch || !window.Intl) return;
  const select = form.querySelector('select');
  const feedback = document.querySelector('[data-timezone-feedback]');
  let zone = select.value, busy = false;
  form.dataset.liveTimezone = '';
  function formatter() {
    return new Intl.DateTimeFormat('es-MX', {timeZone:zone, day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit', hourCycle:'h23'});
  }
  function render() {
    const format = formatter();
    document.querySelectorAll('time[data-local-time]').forEach(element => {
      const date = new Date(element.dateTime);
      if (!Number.isFinite(date.getTime())) return;
      const parts = Object.fromEntries(format.formatToParts(date).map(part => [part.type,part.value]));
      const label = `${parts.day}/${parts.month}/${parts.year} · ${parts.hour}:${parts.minute}`;
      if (element.textContent !== label) element.textContent = label;
    });
  }
  async function update() {
    if (busy || select.value === zone) return;
    const desired = select.value;
    const dates = Array.from(document.querySelectorAll('input[type="datetime-local"]:not(:disabled)'));
    const payload = new FormData(form);
    payload.set('_timezone', zone);
    dates.forEach(input => payload.append('date_values', input.value));
    const controls = new Set([select,...dates]);
    dates.forEach(input => input.form?.querySelectorAll('button[type="submit"],input[type="submit"]').forEach(button => controls.add(button)));
    const previous = Array.from(controls, control => [control,control.disabled]);
    const restoreFocus = document.activeElement === select;
    previous.forEach(([control]) => { control.disabled = true; });
    busy = true;
    feedback.textContent = 'Actualizando horario…';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(form.action, {method:'POST', body:payload, credentials:'same-origin', cache:'no-store', signal:controller.signal, headers:{'X-Timezone-Update':'1','Accept':'application/json'}});
      if (!response.ok || response.redirected) throw Error('No se pudo guardar');
      const data = await response.json();
      if (data.timezone !== desired || !Array.isArray(data.date_values) || data.date_values.length !== dates.length) throw Error('Respuesta inválida');
      zone = data.timezone;
      dates.forEach((input,index) => { input.value = data.date_values[index]; });
      document.querySelectorAll('input[name="_timezone"]').forEach(input => { input.value = zone; });
      document.querySelectorAll('[data-timezone-label]').forEach(label => { label.textContent = data.label; });
      render();
      feedback.textContent = `Fechas actualizadas a ${data.label}.`;
    } catch (_) {
      select.value = zone;
      feedback.textContent = 'No se pudo cambiar el horario. Se conservaron las fechas; vuelve a seleccionar la zona para reintentar.';
    } finally {
      clearTimeout(timeout);
      previous.forEach(([control,disabled]) => { control.disabled = disabled; });
      busy = false;
      if (restoreFocus && document.activeElement === document.body) select.focus({preventScroll:true});
    }
  }
  select.addEventListener('change', update);
  form.addEventListener('submit', event => { event.preventDefault(); update(); });
  document.addEventListener('submit', event => {
    if (busy && event.target.querySelector('input[type="datetime-local"]')) event.preventDefault();
  },true);
  // También normaliza fragmentos y modales que terminaron de cargar tras el cambio.
  new MutationObserver(render).observe(document.body,{childList:true,subtree:true});
  render();
})();
