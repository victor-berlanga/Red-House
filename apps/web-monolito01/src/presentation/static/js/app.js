"use strict";

const sidebar = document.getElementById("sidebar");
const menuButton = document.getElementById("menu-toggle");
const workspace = document.getElementById("workspace");
const narrowScreen = window.matchMedia("(max-width: 960px)");

function setMenu(open) {
  if (!sidebar) return;
  const expanded = open && narrowScreen.matches;
  document.body.classList.toggle("menu-open", expanded);
  menuButton.setAttribute("aria-expanded", String(expanded));
  sidebar.inert = narrowScreen.matches && !expanded;
  workspace.inert = expanded;
  if (expanded) document.getElementById("sidebar-close").focus();
}

if (sidebar) {
  setMenu(false);
  menuButton.addEventListener("click", () => setMenu(true));
  for (const id of ["sidebar-close", "menu-backdrop"]) {
    document.getElementById(id).addEventListener("click", () => { setMenu(false); menuButton.focus(); });
  }
  narrowScreen.addEventListener("change", () => setMenu(false));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.body.classList.contains("menu-open")) {
      setMenu(false); menuButton.focus();
    }
    if (event.key === "Tab" && document.body.classList.contains("menu-open")) {
      const focusable = sidebar.querySelectorAll("a, button");
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
}

const passwordToggle = document.getElementById("password-toggle");
if (passwordToggle) passwordToggle.addEventListener("click", () => {
  const input = document.getElementById("password");
  const showing = input.type === "password";
  input.type = showing ? "text" : "password";
  passwordToggle.setAttribute("aria-pressed", String(showing));
  passwordToggle.setAttribute("aria-label", showing ? "Ocultar contraseña" : "Mostrar contraseña");
});

// Confirma bajas y evita dobles envíos accidentales. La integridad y concurrencia se validan en servidor.
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener("submit", event => {
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }
    if (event.defaultPrevented) return;
    if (form.dataset.submitting) { event.preventDefault(); return; }
    form.dataset.submitting = "true";
    const button = event.submitter || form.querySelector('button:not([type="button"]), input[type="submit"]');
    if (button) {
      button.dataset.originalText = button.textContent;
      button.disabled = true; button.setAttribute("aria-busy", "true");
      if (button.classList.contains("button")) button.textContent = "Guardando…";
    }
  });
});

window.addEventListener("pageshow", () => {
  document.querySelectorAll('form[data-submitting]').forEach(form => {
    delete form.dataset.submitting;
    form.querySelectorAll('[aria-busy="true"]').forEach(button => {
      button.disabled = false; button.removeAttribute("aria-busy");
      if (button.dataset.originalText) button.textContent = button.dataset.originalText;
    });
  });
});
// Búsqueda local de opciones ya autorizadas; nunca consulta expedientes ajenos.
document.querySelectorAll('[data-option-search]').forEach(input => {
  const select = document.getElementById(input.dataset.optionSearch);
  const options = Array.from(select.options).map(option => option.cloneNode(true));
  input.addEventListener('input', () => {
    const chosen = select.value, query = input.value.toLocaleLowerCase('es').trim();
    select.replaceChildren(...options.filter(o => !o.value || o.value === chosen || o.textContent.toLocaleLowerCase('es').includes(query)).map(o => o.cloneNode(true)));
    select.value = chosen;
  });
});

document.querySelectorAll('form[method="post"]:not(.timezone-picker)').forEach(form => {
  form.addEventListener('input', () => {form.dataset.dirty='true';});
  form.addEventListener('change', () => {form.dataset.dirty='true';});
});
const timezoneForm=document.querySelector('.timezone-picker');
if (timezoneForm) timezoneForm.addEventListener('submit', event => {
  if (document.querySelector('form[data-dirty="true"]') && !window.confirm('Cambiar el horario recargará la página. Hay datos sin guardar. ¿Continuar?')) event.preventDefault();
},true);
const formError=document.getElementById('form-error');
if (formError) formError.focus();
