"use strict";
(() => {
  const dialog = document.getElementById('record-dialog');
  if (!dialog) return;
  const body = document.getElementById('record-dialog-body');
  let controller, opener;
  function message(text) {
    const p = document.createElement('p'); p.textContent = text;
    body.replaceChildren(p);
  }
  async function show(url, trigger) {
    const target = new URL(url, location.href);
    if (target.origin !== location.origin) return;
    controller?.abort();
    const pending = new AbortController(); controller = pending;
    if (!dialog.open) { opener = trigger; dialog.showModal(); document.body.classList.add('detail-open'); }
    message('Cargando detalle…'); body.setAttribute('aria-busy', 'true');
    document.getElementById('record-dialog-title').textContent='Detalle del registro';
    const timeout = setTimeout(() => pending.abort(), 15000);
    try {
      const response = await fetch(target, {headers: {'X-Detail-Modal':'1'}, signal:pending.signal, cache:'no-store'});
      if (pending !== controller || !dialog.open) return;
      if (response.redirected && new URL(response.url).pathname === '/login') {
        message('Tu sesión terminó. Inicia sesión nuevamente para consultar este registro.');
        const link = document.createElement('a'); link.href='/login'; link.className='button'; link.textContent='Iniciar sesión'; body.append(link); return;
      }
      const html = await response.text();
      if (pending !== controller || !dialog.open) return;
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const content = doc.querySelector('[data-detail-content]');
      if (!content) throw new Error('Respuesta no válida');
      // Solo se aceptan fragmentos de consulta del servidor, nunca formularios.
      if (content.querySelector('form,script,iframe')) throw new Error('Detalle no válido');
      body.replaceChildren(content);
      document.getElementById('record-dialog-title').textContent=content.querySelector('h1')?.textContent || 'Detalle del registro';
      body.scrollTop = 0;
    } catch (error) {
      if (pending !== controller || !dialog.open) return;
      message('No se pudo cargar el detalle. Comprueba tu conexión y vuelve a intentarlo.');
      const retry = document.createElement('button'); retry.type='button'; retry.className='button secondary'; retry.textContent='Reintentar';
      retry.addEventListener('click', () => show(url, trigger)); body.append(retry);
    } finally {
      clearTimeout(timeout);
      if (pending === controller) body.removeAttribute('aria-busy');
    }
  }
  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-record-view]');
    if (trigger) { event.preventDefault(); show(trigger.dataset.recordView, trigger); return; }
    const inline = event.target.closest('[data-row-preview]');
    if (inline) {
      controller?.abort(); controller=null;
      opener=inline; body.removeAttribute('aria-busy');
      document.getElementById('record-dialog-title').textContent=inline.closest('table').caption?.textContent || inline.closest('section')?.querySelector('h2')?.textContent || 'Detalle del registro';
      const template=inline.parentElement.querySelector('template');
      body.replaceChildren(template.content.cloneNode(true)); dialog.showModal(); document.body.classList.add('detail-open');
    }
  });
  // Tablas de resultados e historiales sin expediente: consulta de todos sus campos,
  // sin inventar una operación de edición sobre agregados o eventos inmutables.
  function enhanceTables() {
    document.querySelectorAll('main table').forEach(table => {
      if (table.dataset.previewReady || table.querySelector('[data-record-view]')) return;
      const headers=Array.from(table.querySelectorAll('thead th'));
      if (!headers.length || headers.some(h => h.textContent.trim()==='Acciones')) return;
      table.dataset.previewReady='true';
      const heading=document.createElement('th'); heading.scope='col'; heading.textContent='Acciones'; headers[0].parentElement.append(heading);
      table.querySelectorAll('tbody > tr').forEach(row => {
        const cells=Array.from(row.cells);
        if(cells.length===1 && cells[0].colSpan>1) {cells[0].colSpan++; return;}
        const td=document.createElement('td'), button=document.createElement('button'), template=document.createElement('template');
        button.type='button'; button.className='icon-button'; button.dataset.rowPreview='';
        button.setAttribute('aria-label','Ver '+(cells[0]?.textContent.trim() || 'registro')); button.title='Ver detalle';
        const icon=document.createElement('img'); icon.src='/static/img/icons/eye.svg'; icon.className='icon'; icon.alt=''; icon.width=20; icon.height=20; button.append(icon);
        const dl=document.createElement('dl'); dl.className='regional-facts';
        headers.forEach((header,i) => {const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd'); dt.textContent=header.textContent; dd.textContent=cells[i]?.textContent.trim() || '—'; div.append(dt,dd);dl.append(div);});
        template.content.append(dl); td.append(button,template);row.append(td);
      });
    });
  }
  enhanceTables();
  const main=document.querySelector('main');
  if(main) new MutationObserver(enhanceTables).observe(main,{childList:true,subtree:true});
  dialog.querySelector('[data-dialog-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r=dialog.getBoundingClientRect(); if(event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom) dialog.close(); } });
  dialog.addEventListener('close', () => { controller?.abort(); controller=null; body.replaceChildren(); document.body.classList.remove('detail-open'); if(opener?.isConnected) opener.focus(); });
})();
