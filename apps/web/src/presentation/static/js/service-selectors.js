'use strict';
for (const box of document.querySelectorAll('[data-service-selector]')) {
  const select = box.querySelector('select');
  const search = box.querySelector('[data-service-option-search]');
  const more = box.querySelector('[data-service-option-more]');
  const status = box.querySelector('[data-service-option-status]');
  let page = 1;
  let controller;
  let timer;
  async function load(reset) {
    if (controller) controller.abort();
    controller = new AbortController();
    const current = controller;
    const wanted = reset ? 1 : page + 1;
    const url = new URL(box.dataset.serviceSelector, location.origin);
    url.searchParams.set('q', search.value);
    url.searchParams.set('page', String(wanted));
    status.textContent = 'Consultando opciones…';
    more.disabled = true;
    try {
      const response = await fetch(url, {signal: current.signal, headers: {'Accept': 'application/json'}});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw new Error();
      const data = await response.json();
      if (current !== controller) return;
      if (reset) {
        for (const option of [...select.options]) if (option.value && !option.selected) option.remove();
      }
      const existing = new Set([...select.options].map(option => option.value));
      for (const item of data.items) {
        if (!existing.has(item.id)) select.add(new Option(item.label, item.id));
      }
      page = wanted;
      more.hidden = !data.has_more;
      status.textContent = `${data.total} opciones encontradas. La selección actual se conserva.`;
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = 'No se pudieron consultar las opciones. Intenta nuevamente.';
    } finally {
      if (current === controller) more.disabled = false;
    }
  }
  search.addEventListener('input', () => {clearTimeout(timer); timer = setTimeout(() => load(true), 300);});
  more.addEventListener('click', () => load(false));
}
