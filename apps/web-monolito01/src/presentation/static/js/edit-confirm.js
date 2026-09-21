/* Confirmación local: nunca guarda borradores ni datos clínicos fuera del formulario. */
(() => {
  'use strict';
  document.querySelectorAll('form[data-confirm-edit]').forEach((form, index) => {
    const original = JSON.parse(form.dataset.original || '{}');
    const controls = [...form.elements].filter(el => el.name && !el.disabled &&
      !['hidden', 'submit', 'button', 'search'].includes(el.type));
    const reason = controls.find(el => ['audit_reason', 'reason', 'observation', 'release_reference'].includes(el.name));
    const privateFields = new Set(['password', 'background', 'restrictions', 'requirement', 'studies',
      'consent_reference', 'display_name', 'party_name', 'contact_name', 'contact_email', 'contact_phone', 'login_email']);
    const raw = el => el.type === 'checkbox' ? el.checked : el.value;
    const initial = new Map(controls.map(el => {
      let value = Object.hasOwn(original, el.name) ? original[el.name] : raw(el);
      if (el.type === 'checkbox' && Array.isArray(value)) value = value.includes(el.value);
      return [el, value];
    }));
    const label = el => (el.labels?.[0]?.textContent || el.name).replace(/\s*\*\s*$/, '').trim();
    const readable = (el, value) => {
      if (el.type === 'checkbox') return value ? 'Sí' : 'No';
      if (el.tagName === 'SELECT') return [...el.options].find(o => o.value === String(value))?.textContent.trim() || 'Sin selección';
      return String(value ?? '').trim().slice(0, 100) || 'Sin registrar';
    };
    const dialog = document.createElement('dialog');
    dialog.className = 'record-dialog edit-confirm-dialog';
    dialog.setAttribute('aria-labelledby', `edit-confirm-title-${index}`);
    dialog.innerHTML = '<div class="record-dialog-header"><h2></h2><button type="button" class="icon-button" aria-label="Cerrar confirmación">×</button></div><div class="record-dialog-body"><p>Revisa la operación antes de confirmar.</p><ul class="change-summary"></ul><p class="notice confirmation-warning" hidden></p><div class="confirmation-fields"></div><div class="form-actions"><button type="button" class="button secondary" data-confirm-cancel>Volver a editar</button><button type="button" class="button" data-confirm-accept>Confirmar y guardar</button></div></div>';
    dialog.querySelector('h2').id = `edit-confirm-title-${index}`;
    dialog.querySelector('h2').textContent = form.dataset.confirmEdit;
    const summary = dialog.querySelector('.change-summary');
    const warning = dialog.querySelector('.confirmation-warning');
    const status = document.createElement('p');
    status.className = 'muted'; status.setAttribute('role', 'status');
    form.append(status, dialog);
    if (reason) {
      dialog.querySelector('.confirmation-fields').append(reason.closest('.field'));
      reason.disabled = true;
      reason.addEventListener('input', () => reason.setCustomValidity(''));
    }
    form.querySelectorAll('fieldset.form-group').forEach(group => {
      if (!group.querySelector('input, select, textarea')) group.hidden = true;
    });
    let submitter, confirmed = false;
    const close = () => dialog.close();
    dialog.querySelector('.icon-button').addEventListener('click', close);
    dialog.querySelector('[data-confirm-cancel]').addEventListener('click', close);
    dialog.addEventListener('click', event => { if (event.target === dialog) {
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
    }});
    dialog.addEventListener('close', () => {
      if (reason) reason.disabled = true;
      confirmed = false;
      document.body.classList.remove('detail-open');
      submitter?.focus();
    });
    form.addEventListener('submit', event => {
      if (confirmed && dialog.open) return;
      event.preventDefault(); event.stopImmediatePropagation();
      if (dialog.open) return;
      submitter = event.submitter;
      summary.replaceChildren(); status.textContent = '';
      const changes = controls.filter(el => el !== reason && el.name !== 'human_confirmation' &&
        (form.dataset.editMode !== 'edit' || String(raw(el)) !== String(initial.get(el))));
      if (!changes.length && form.dataset.editMode === 'edit') {
        status.textContent = 'No hay cambios para guardar.'; return;
      }
      changes.forEach(el => {
        const li = document.createElement('li');
        if (privateFields.has(el.name)) {
          li.textContent = `${label(el)}: ${el.type === 'password' ? 'se cambiará (valor oculto)' : 'se actualizará; contenido reservado'}.`;
        } else {
          li.textContent = `${label(el)}: ${form.dataset.editMode === 'edit' ? readable(el, initial.get(el)) + ' → ' : ''}${readable(el, raw(el))}`;
        }
        summary.append(li);
      });
      if (!summary.children.length) {
        const li = document.createElement('li'); li.textContent = form.dataset.confirmEdit; summary.append(li);
      }
      const deactivating = changes.some(el => ['INACTIVE','CANCELLED'].includes(el.value) || (el.name === 'is_active' && !el.checked));
      warning.textContent = [form.dataset.confirmWarning, deactivating ? 'Se inactivará o cancelará el registro. Su historial se conserva; revisa el efecto antes de continuar.' : ''].filter(Boolean).join(' ');
      warning.hidden = !warning.textContent;
      if (reason) { reason.disabled = false; reason.setCustomValidity(''); }
      dialog.showModal(); document.body.classList.add('detail-open');
      (reason || dialog.querySelector('[data-confirm-cancel]')).focus();
    }, true);
    dialog.querySelector('[data-confirm-accept]').addEventListener('click', () => {
      if (reason) reason.setCustomValidity(reason.value.trim() ? '' : 'Escribe el motivo o referencia requerida.');
      if (!form.reportValidity()) return;
      confirmed = true;
      form.requestSubmit(submitter);
      confirmed = false;
    });
  });
})();
