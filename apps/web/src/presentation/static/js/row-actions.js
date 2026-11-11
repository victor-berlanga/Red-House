/* Shared disclosure menus and focus/hover hints; never intercept business actions. */
(() => {
  let tooltip, owner;
  function hideHint() {
    tooltip?.remove(); tooltip = null;
    if (owner) {
      const ids = (owner.getAttribute('aria-describedby') || '').split(' ').filter(id => id !== 'row-action-hint');
      if (ids.length) owner.setAttribute('aria-describedby', ids.join(' '));
      else owner.removeAttribute('aria-describedby');
    }
    owner = null;
  }
  function place(element, anchor) {
    const rect = anchor.getBoundingClientRect();
    const box = element.getBoundingClientRect();
    element.style.left = `${Math.max(8, Math.min(rect.right - box.width, innerWidth - box.width - 8))}px`;
    element.style.top = `${rect.bottom + box.height + 8 < innerHeight ? rect.bottom + 6 : Math.max(8, rect.top - box.height - 6)}px`;
  }
  function hint(target) {
    const anchor = target.closest('[data-tooltip]');
    if (!anchor || owner === anchor) return;
    hideHint(); owner = anchor;
    tooltip = document.createElement('div'); tooltip.className = 'action-tooltip';
    tooltip.id = 'row-action-hint'; tooltip.setAttribute('role', 'tooltip');
    tooltip.textContent = anchor.dataset.tooltip;
    document.body.append(tooltip);
    anchor.setAttribute('aria-describedby', [anchor.getAttribute('aria-describedby'), tooltip.id].filter(Boolean).join(' '));
    place(tooltip, anchor);
  }
  function close(menu, returnFocus = false) {
    menu.open = false; menu.querySelector('summary').setAttribute('aria-expanded', 'false');
    if (returnFocus) menu.querySelector('summary').focus();
  }
  document.addEventListener('toggle', event => {
    const menu = event.target;
    if (!menu.matches?.('.row-action-menu')) return;
    const trigger = menu.querySelector('summary');
    trigger.setAttribute('aria-expanded', String(menu.open));
    if (menu.open) {
      hideHint();
      document.querySelectorAll('.row-action-menu[open]').forEach(other => { if (other !== menu) close(other); });
      const panel = menu.querySelector('.action-menu-panel');
      if (!panel.id) panel.id = `row-menu-${crypto.randomUUID()}`;
      trigger.setAttribute('aria-controls', panel.id);
      place(panel, trigger);
    }
  }, true);
  document.addEventListener('click', event => document.querySelectorAll('.row-action-menu[open]').forEach(menu => {
    if (!menu.contains(event.target)) close(menu);
  }));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      hideHint();
      document.querySelectorAll('.row-action-menu[open]').forEach(menu => close(menu, menu.contains(document.activeElement)));
    }
  });
  document.addEventListener('focusin', event => {
    hint(event.target);
    document.querySelectorAll('.row-action-menu[open]').forEach(menu => { if (!menu.contains(event.target)) close(menu); });
  });
  document.addEventListener('focusout', hideHint);
  document.addEventListener('pointerover', event => hint(event.target));
  document.addEventListener('pointerout', event => { if (owner && !owner.contains(event.relatedTarget)) hideHint(); });
  addEventListener('resize', () => { hideHint(); document.querySelectorAll('.row-action-menu[open]').forEach(menu => close(menu)); });
  document.addEventListener('scroll', event => {
    hideHint();
    document.querySelectorAll('.row-action-menu[open]').forEach(menu => { if (!menu.contains(event.target)) close(menu); });
  }, true);
})();
