'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const readline = require('node:readline');

(async () => {
  const channel = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  const input = JSON.parse((await channel[Symbol.asyncIterator]().next()).value);
  channel.close();
  const { chromium } = require(path.join(input.root, '.local/gcp-public/browser/node_modules/playwright'));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const report = { passed: false, pages: [], javascript_errors: 0, business_posts: [] };
  const contexts = [];
  process.once('SIGTERM', () => { browser.close().finally(() => process.exit(1)); });
  let phase = 'login';
  let current;
  async function login(username) {
    const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 960 } });
    contexts.push(context);
    const page = await context.newPage();
    page.on('pageerror', () => report.javascript_errors++);
    page.on('request', request => {
      if (['GET', 'HEAD'].includes(request.method())) return;
      const route = new URL(request.url()).pathname;
      if (!['/login', '/logout', '/sesion/continuar'].includes(route)) report.business_posts.push({ route, method: request.method() });
    });
    await page.goto(input.base + '/login');
    await page.locator('#login_email').fill(username);
    await page.locator('#password').fill(input.password);
    await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
    return page;
  }
  async function open(route, title, state, screenshot) {
    assert.equal((await current.goto(input.base + route)).status(), 200);
    if (title) assert.equal((await current.locator('h1').textContent()).trim(), title);
    if (state) assert.ok(await current.locator('.page-heading .status-' + state.toLowerCase()).isVisible());
    if (screenshot) await current.screenshot({ path: path.join(input.output, screenshot), fullPage: true });
    report.pages.push({ route, status: 200, state });
  }
  try {
    current = await login(input.operator);
    phase = 'appointment';
    await open('/citas/' + input.appointment.id, 'Inscripción a campaña', input.appointment.status, 'cita-ios-consultada-web.png');
    assert.ok((await current.locator('main').textContent()).includes(input.donor.display_name));
    phase = 'donor';
    await open('/donantes/donor/' + input.donor.id, input.donor.folio, input.donor.status);
    phase = 'donation';
    await open('/donaciones/' + input.donation.id, 'Donación ' + input.donation.id.slice(0, 8).toUpperCase(), 'PROCESSED', 'procesamiento-escritorio-consultado-web.png');
    const processing = current.locator('section.record-section').filter({ has: current.getByRole('heading', { name: 'Procesamiento', exact: true }) });
    assert.equal(await processing.locator('.status-collected').count(), 1);
    assert.equal(await processing.locator('.status-processed').count(), 1);
    phase = 'parent';
    await open('/inventario/' + input.parent.id, input.parent.folio, 'WITHDRAWN');
    phase = 'lineage';
    await open('/inventario/' + input.parent.id + '/linaje', 'Linaje · ' + input.parent.folio, null, 'derivados-escritorio-consultados-web.png');
    assert.ok((await current.locator('main').textContent()).includes(input.donation.id));
    const lines = current.locator('table.records-table tbody tr');
    assert.equal(await lines.count(), input.children.length);
    for (const child of input.children) {
      const row = lines.filter({ has: current.getByRole('link', { name: child.folio, exact: true }) });
      assert.equal(await row.count(), 1);
      assert.ok((await row.textContent()).includes(child.status));
      const href = await row.getByRole('link', { name: child.folio, exact: true }).getAttribute('href');
      assert.equal(new URL(href, input.base).pathname, '/inventario/' + child.id);
    }
    for (const child of input.children) {
      phase = 'child';
      await open('/inventario/' + child.id, child.folio, child.status);
    }
    phase = 'foreign-institution';
    current = await login('operator2');
    const denied = await current.goto(input.base + '/inventario/' + input.parent.id);
    assert.equal(denied.status(), 403);
    assert.ok(!(await current.locator('main').textContent()).includes(input.parent.folio));
    report.foreign_status = 403;
    assert.equal(report.javascript_errors, 0);
    assert.deepEqual(report.business_posts, []);
    report.passed = true;
  } catch (error) {
    report.failure_phase = phase;
    report.failure_type = error.name;
    process.exitCode = 1;
    if (current) await current.screenshot({ path: path.join(input.output, 'fallo.png'), fullPage: true }).catch(() => {});
  } finally {
    for (const context of contexts) {
      for (const page of context.pages()) {
        try {
          const close = page.getByRole('button', { name: 'Cerrar sesión', exact: true }).first();
          if (await close.isVisible()) await Promise.all([page.waitForURL('**/login'), close.click()]);
        } catch (_) { /* El runner conserva recibo de fallo y cierra el navegador propio. */ }
      }
    }
    await browser.close();
    fs.writeFileSync(path.join(input.output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
  }
})();
