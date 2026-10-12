'use strict';
// Una sola captura solicitada por el usuario; no hay seguimiento en segundo plano.
(() => {
  const button = document.querySelector('[data-capture-location]');
  if (!button) return;
  const feedback = document.querySelector('[data-location-feedback]');
  const latitude = document.querySelector('[name="latitude"]');
  const longitude = document.querySelector('[name="longitude"]');
  const captured = document.querySelector('[name="captured_at"]');
  button.addEventListener('click', () => {
    if (!navigator.geolocation || !window.isSecureContext) {
      feedback.textContent = 'Este navegador no permite consultar la ubicación. Puedes capturar las coordenadas autorizadas manualmente.';
      return;
    }
    const zoneControl = document.querySelector('[name="timezone"]');
    if (zoneControl.disabled) return;
    const controls = [button, zoneControl, ...button.form.querySelectorAll('button[type="submit"]')];
    const previous = controls.map(control => [control,control.disabled]);
    controls.forEach(control => { control.disabled = true; });
    const restore = () => previous.forEach(([control,disabled]) => { control.disabled = disabled; });
    feedback.textContent = 'Consultando ubicación…';
    navigator.geolocation.getCurrentPosition(position => {
      const zone = document.querySelector('[name="timezone"]').value;
      const time = new Date(position.timestamp);
      const parts = Object.fromEntries(new Intl.DateTimeFormat('sv-SE', {timeZone:zone, year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'}).formatToParts(time).map(p => [p.type,p.value]));
      latitude.value = position.coords.latitude.toFixed(6);
      longitude.value = position.coords.longitude.toFixed(6);
      captured.value = `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
      latitude.dispatchEvent(new Event('input', {bubbles:true}));
      feedback.textContent = `Ubicación capturada, precisión aproximada de ${Math.round(position.coords.accuracy)} m. Revisa y guarda para registrarla.`;
      restore();
    }, error => {
      feedback.textContent = error.code === 1 ? 'Permiso de ubicación denegado. Puedes capturar las coordenadas autorizadas manualmente.' : 'No se pudo obtener la ubicación. Reintenta o captura las coordenadas autorizadas manualmente.';
      restore();
    }, {enableHighAccuracy:true, timeout:12000, maximumAge:0});
  });
})();
