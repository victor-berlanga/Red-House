"use strict";
(() => {
  const form=document.getElementById('inventory-update');
  if(!form) return;
  const dialog=document.getElementById('inventory-confirm-dialog');
  const reason=document.getElementById('inventory-reason');
  const state=form.elements.current_status, location=form.elements.location_id;
  const message=document.getElementById('inventory-change-message');
  let opener;
  const label=(select,value)=>Array.from(select.options).find(option=>option.value===value)?.textContent.trim() || value;
  document.querySelectorAll('[data-inventory-confirm]').forEach(button=>button.addEventListener('click',()=>{
    const withdraw=button.dataset.inventoryConfirm==='withdraw';
    const changes=[];
    for(const [select,original,title] of [[state,form.dataset.originalStatus,'Estado'],[location,form.dataset.originalLocation,'Ubicación']]) {
      if(select.value!==original) changes.push(`${title}: ${label(select,original)} → ${label(select,select.value)}`);
    }
    message.textContent='';
    if(!withdraw && !changes.length) {message.textContent='No hay cambios de estado o ubicación para guardar.';return;}
    if(!withdraw && (!state.reportValidity() || !location.reportValidity())) return;
    form.action=withdraw ? form.dataset.withdrawUrl : form.dataset.saveUrl;
    document.getElementById('inventory-confirm-title').textContent=withdraw ? 'Confirmar baja' : 'Confirmar cambios';
    document.getElementById('inventory-confirm-submit').textContent=withdraw ? 'Confirmar baja' : 'Confirmar cambios';
    document.getElementById('inventory-confirm-summary').textContent=withdraw
      ? `Se retirará ${form.dataset.unitCode} del inventario operativo. Se conservarán su folio, historial y auditoría. Esta acción no se revierte desde esta vista. Los cambios de los desplegables no se guardarán.`
      : `Se actualizará ${form.dataset.unitCode} con estos cambios:`;
    const list=document.getElementById('inventory-change-summary');list.replaceChildren();
    if(!withdraw) for(const change of changes){const li=document.createElement('li');li.textContent=change;list.append(li);}
    opener=button;reason.setCustomValidity('');dialog.showModal();document.body.classList.add('detail-open');reason.focus();
  }));
  reason.addEventListener('input',()=>reason.setCustomValidity(reason.value.trim() ? '' : 'Escribe un motivo; no puede contener solo espacios.'));
  form.addEventListener('submit',event=>{
    if(!dialog.open || !reason.value.trim()) {event.preventDefault();event.stopImmediatePropagation();reason.setCustomValidity('Escribe el motivo de la operación.');if(dialog.open)reason.reportValidity();}
  },true);
  dialog.querySelectorAll('[data-inventory-cancel]').forEach(button=>button.addEventListener('click',()=>dialog.close()));
  dialog.addEventListener('close',()=>{document.body.classList.remove('detail-open');opener?.focus();});
  dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left || event.clientX>r.right || event.clientY<r.top || event.clientY>r.bottom)dialog.close();}});
})();
