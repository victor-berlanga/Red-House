'use strict';
// Un único resumen accesible reemplaza los globos nativos. El servidor vuelve a validar.
(() => {
  function message(control) {
    const value = control.type === 'password' ? control.value : control.value.trim();
    const validity = control.validity;
    if (validity.badInput) return control.step === '1' ? 'Escribe un número entero.' : 'Escribe un número válido.';
    if (validity.valueMissing || (control.required && !value)) return control.type === 'checkbox' ? 'Confirma esta opción para continuar.' : 'Completa este campo.';
    if (!value) return '';
    const minimum = control.getAttribute('minlength'), maximum = control.getAttribute('maxlength');
    if (minimum && [...value].length < Number(minimum)) return `Escribe al menos ${minimum} caracteres${control.required ? '.' : ' o deja este campo vacío.'}`;
    if (maximum && [...value].length > Number(maximum)) return `Escribe como máximo ${maximum} caracteres.`;
    if (validity.rangeUnderflow) return `Escribe un valor mayor o igual a ${control.min}.`;
    if (validity.rangeOverflow) return `Escribe un valor menor o igual a ${control.max}.`;
    if (validity.stepMismatch) return control.step === '1' ? 'Escribe un número entero.' : 'Usa el incremento indicado junto al campo.';
    if (validity.patternMismatch) return control.name === 'folio' ? 'Usa letras ASCII, números, guion o guion bajo; sin espacios ni acentos.' : 'Usa el formato indicado junto al campo.';
    if (!validity.valid) return 'Revisa el formato indicado junto al campo.';
    return '';
  }
  // Captura también formularios que se incorporan después dentro de un diálogo.
  document.addEventListener('submit', event => {
    const form = event.target;
    if (!form.matches('[data-validated-form]')) return;
    const errors = [];
    for (const control of form.querySelectorAll('input[id]:not([type="hidden"]),textarea[id],select[id]')) {
      if (control.disabled || control.type === 'search') continue;
      const text = message(control);
      const old = form.querySelector(`#${CSS.escape(control.id)}-error`);
      old?.remove(); control.removeAttribute('aria-invalid');
      const descriptions = (control.getAttribute('aria-describedby') || '').split(' ').filter(id => id && id !== `${control.id}-error`);
      if (text) {
        control.setAttribute('aria-invalid', 'true');
        const error = document.createElement('p');
        error.id = `${control.id}-error`; error.className = 'field-error'; error.dataset.fieldError = ''; error.textContent = text;
        control.closest('.field').append(error); descriptions.push(error.id);
        errors.push({control, text});
      }
      control.setAttribute('aria-describedby', descriptions.join(' '));
    }
    const scope = form.closest('[data-action-content]') || form.parentElement;
    scope.querySelector('[data-error-summary]')?.remove();
    if (!errors.length) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const summary = document.createElement('div');
    summary.id = 'form-error'; summary.className = 'notice error'; summary.tabIndex = -1;
    summary.setAttribute('role', 'alert'); summary.dataset.errorSummary = '';
    const title = document.createElement('p');
    title.textContent = errors.length === 1 ? 'Revisa el campo señalado.' : `Revisa los ${errors.length} campos señalados.`;
    const list = document.createElement('ul');
    for (const {control, text} of errors) {
      const item = document.createElement('li'), link = document.createElement('a');
      link.href = `#${control.id}`; link.textContent = `${control.labels?.[0]?.textContent.replace('*', '').trim() || 'Campo'}: ${text}`;
      item.append(link); list.append(item);
    }
    summary.append(title, list); form.before(summary); summary.focus();
  }, true);
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-error-summary] a[href^="#"]');
    if (link) { event.preventDefault(); document.getElementById(link.hash.slice(1))?.focus(); }
  });
})();
