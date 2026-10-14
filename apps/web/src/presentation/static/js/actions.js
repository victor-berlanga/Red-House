'use strict';
// Los enlaces siguen funcionando sin JavaScript; cada operación se confirma por POST con CSRF.
(() => {
  const dialog = document.querySelector('#action-dialog');
  if (!dialog || !dialog.showModal || !window.fetch) return;
  const body = dialog.querySelector('[data-action-body]');
  let opener, controller;
  document.addEventListener('click', async event => {
    const link = event.target.closest('a[data-action-dialog]');
    if (!link || event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (new URL(link.href).origin !== location.origin) return;
    event.preventDefault();
    controller?.abort();
    const pending = new AbortController();
    controller = pending;
    opener = link;
    body.textContent = 'Cargando confirmación…';
    dialog.showModal();
    const timeout = setTimeout(() => pending.abort(), 15000);
    try {
      const response = await fetch(link.href, {credentials:'same-origin', cache:'no-store', signal:pending.signal, headers:{'X-Action-Modal':'1'}});
      if (response.redirected || !response.ok) throw Error('No disponible');
      const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
      const content = parsed.querySelector('[data-action-content]');
      if (!content || pending !== controller || !dialog.open) return;
      body.replaceChildren(content);
      content.querySelector('button[type="submit"]')?.focus();
    } catch (_) {
      if (pending !== controller || !dialog.open) return;
      body.textContent = 'No fue posible cargar la confirmación. ';
      const retry = document.createElement('a');
      retry.href = link.href; retry.className = 'text-link'; retry.textContent = 'Abrir operación';
      body.append(retry);
    } finally { clearTimeout(timeout); }
  });
  dialog.querySelector('[data-action-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    const cancel = event.target.closest('a');
    if (cancel?.hasAttribute('data-action-cancel')) { event.preventDefault(); dialog.close(); }
  });
  dialog.addEventListener('submit', event => {
    const button = event.submitter;
    if (button) { button.disabled = true; button.textContent = 'Procesando…'; }
  });
  dialog.addEventListener('close', () => { controller?.abort(); controller = null; body.replaceChildren(); if (opener?.isConnected) opener.focus(); });
})();
