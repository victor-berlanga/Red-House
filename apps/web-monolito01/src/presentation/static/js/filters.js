"use strict";

// Mejora progresiva de los GET existentes: autorización y consultas siguen en Flask.
(() => {
  const form = document.querySelector("form[data-live-filter]");
  const results = document.querySelector("[data-filter-results]");
  if (!form || !results || !window.fetch || !window.AbortController) return;

  const summary = document.querySelector("[data-filter-summary]");
  const feedback = document.createElement("div");
  feedback.className = "filter-feedback";
  const message = document.createElement("span");
  message.setAttribute("role", "status");
  message.setAttribute("aria-live", "polite");
  message.setAttribute("aria-atomic", "true");
  const retry = document.createElement("button");
  retry.type = "button";
  retry.className = "button secondary small";
  retry.textContent = "Reintentar";
  retry.hidden = true;
  feedback.append(message, retry);
  form.after(feedback);
  form.classList.add("live-filters-enabled");

  let controller, delay, sequence = 0, composing = false;
  let desired = new URL(location.href);

  function busy(value) {
    results.setAttribute("aria-busy", String(value));
    results.inert = value;
  }

  function invalidate() {
    clearTimeout(delay);
    controller?.abort();
    sequence += 1;
    retry.hidden = true;
    feedback.classList.remove("filter-error");
    return sequence;
  }

  function inputURL() {
    const url = new URL(location.href);
    url.searchParams.delete("page");
    for (const [key, value] of new FormData(form)) {
      if (value) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    }
    return url;
  }

  function restoreFilters(url) {
    for (const control of form.elements) {
      if (control.name) control.value = url.searchParams.get(control.name) || "";
    }
  }

  async function load(url, ticket, {history = true, focus = false} = {}) {
    const pending = new AbortController();
    controller = pending;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; pending.abort(); }, 15000);
    busy(true);
    message.textContent = "Actualizando resultados…";
    try {
      const response = await fetch(url, {
        credentials: "same-origin", cache: "no-store", signal: pending.signal,
        headers: {Accept: "text/html"},
      });
      if (ticket !== sequence) return;
      const destination = new URL(response.url);
      if (response.redirected && destination.origin === location.origin && destination.pathname === "/login") {
        results.replaceChildren();
        summary?.replaceChildren();
        location.assign(destination.href);
        return;
      }
      if (response.status === 401 || response.status === 403) {
        results.replaceChildren();
        summary?.replaceChildren();
        message.textContent = "Tu sesión o tus permisos cambiaron. Vuelve a iniciar sesión.";
        feedback.classList.add("filter-error");
        return;
      }
      if (!response.ok || destination.origin !== location.origin || destination.pathname !== url.pathname ||
          !response.headers.get("content-type")?.includes("text/html")) throw new Error("Invalid response");
      const html = await response.text();
      if (ticket !== sequence) return;
      const document = new DOMParser().parseFromString(html, "text/html");
      const next = document.querySelector("[data-filter-results]");
      const nextSummary = document.querySelector("[data-filter-summary]");
      if (!next || (summary && !nextSummary)) throw new Error("Missing results");
      // Solo reemplaza resultados: los filtros mantienen el foco y los POST su borrador.
      results.replaceChildren(...next.childNodes);
      results.dataset.resultCount = next.dataset.resultCount;
      if (summary) summary.replaceChildren(...nextSummary.childNodes);
      if (history && url.href !== location.href) window.history.pushState(null, "", url);
      message.textContent = `${next.dataset.resultCount} resultado${next.dataset.resultCount === "1" ? "" : "s"}`;
      if (focus) { busy(false); results.focus({preventScroll: true}); }
    } catch (error) {
      if (ticket !== sequence) return;
      feedback.classList.add("filter-error");
      message.textContent = (timedOut ? "La consulta tardó demasiado." : "No se pudieron actualizar los resultados.") +
        " Se conservan los resultados anteriores. Reintenta la consulta.";
      retry.hidden = false;
    } finally {
      clearTimeout(timeout);
      if (ticket === sequence) busy(false);
    }
  }

  function schedule(wait = 0, url = inputURL(), options = {}) {
    const ticket = invalidate();
    desired = url;
    if (!form.checkValidity()) {
      message.textContent = "Revisa los valores de los filtros. Se conservan los resultados anteriores.";
      feedback.classList.add("filter-error");
      busy(false);
      return;
    }
    busy(true);
    message.textContent = "Actualizando resultados…";
    delay = setTimeout(() => load(url, ticket, options), wait);
  }

  form.addEventListener("input", event => {
    if (composing || event.isComposing) return;
    if (event.target.matches('input[type="text"], input[type="search"], input:not([type])')) schedule(300);
  });
  form.addEventListener("change", event => {
    if (event.target.matches('select, input[type="date"]')) schedule();
  });
  form.addEventListener("compositionstart", () => { composing = true; invalidate(); busy(false); });
  form.addEventListener("compositionend", () => { composing = false; schedule(300); });
  form.addEventListener("submit", event => {
    event.preventDefault();
    if (!composing) schedule();
  });

  function ordinaryClick(event) {
    return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
  }

  form.addEventListener("click", event => {
    const clear = event.target.closest("a[data-filter-clear]");
    if (!clear || !ordinaryClick(event)) return;
    const url = new URL(clear.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname) return;
    event.preventDefault();
    restoreFilters(url);
    schedule(0, url);
  });
  results.addEventListener("click", event => {
    const link = event.target.closest(".pagination a");
    if (!link || !ordinaryClick(event)) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname) return;
    event.preventDefault();
    schedule(0, url, {focus: true});
  });
  retry.addEventListener("click", () => schedule(0, desired));
  window.addEventListener("popstate", () => {
    const url = new URL(location.href);
    restoreFilters(url);
    schedule(0, url, {history: false});
  });
  window.addEventListener("pagehide", () => { invalidate(); busy(false); });
  window.addEventListener("pageshow", event => {
    if (event.persisted) {
      const url = new URL(location.href);
      restoreFilters(url);
      schedule(0, url, {history: false});
    }
  });
})();
