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

// Evita un doble envío accidental. La integridad y concurrencia se validan en servidor.
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener("submit", () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.setAttribute("aria-busy", "true"); }
  });
});
