'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const readline = require('node:readline');

(async () => {
  const channel = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  const messages = channel[Symbol.asyncIterator]();
  const input = JSON.parse((await messages.next()).value);
  const { chromium } = require(path.join(input.root, '.local/gcp-public/browser/node_modules/playwright'));
  const report = { passed: false, jobs: [], downloads: [], denied: [], javascript_errors: 0 };
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const contexts = [];
  const pages = [];
  let phase = 'login';
  async function control(name) {
    console.log(JSON.stringify({ control: name, jobs: report.jobs }));
    const answer = await messages.next();
    assert.ok(!answer.done);
    const parsed = JSON.parse(answer.value);
    assert.equal(parsed.control, name);
    assert.equal(parsed.passed, true);
    return parsed;
  }
  async function login() {
    const context = await browser.newContext({ ignoreHTTPSErrors: true, timezoneId: 'America/Monterrey', viewport: { width: 1280, height: 960 } });
    contexts.push(context);
    const page = await context.newPage();
    pages.push(page);
    page.on('pageerror', () => report.javascript_errors++);
    await page.goto(input.base + '/login');
    await page.locator('#login_email').fill('operator1');
    await page.locator('#password').fill(input.password);
    await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
    return page;
  }
  process.once('SIGTERM', () => { channel.close(); browser.close().catch(() => {}); });
  try {
    const owner = await login();
    for (const format of ['CSV', 'PDF', 'XLSX']) {
      phase = 'create-' + format;
      await owner.goto(input.base + '/reportes/nuevo');
      await owner.locator('#report').selectOption('INVENTORY');
      await owner.locator('#format').selectOption(format);
      await owner.locator('#from_at').fill(input.from_local);
      await owner.locator('#until_at').fill(input.until_local);
      await owner.locator('#filter_q').fill(input.prefix);
      await owner.locator('#filter_status').fill('QUARANTINE');
      await owner.locator('#order').selectOption('ID_ASC');
      const response = owner.waitForResponse(r => new URL(r.url()).pathname === '/reportes/nuevo' && r.request().method() === 'POST');
      await owner.locator('form.record-form button[type=submit]').click();
      assert.equal((await response).status(), 302);
      await owner.waitForURL(url => /^\/reportes\/[0-9a-f-]{36}$/.test(url.pathname));
      const id = new URL(owner.url()).pathname.split('/').pop();
      report.jobs.push({ id, format });
      assert.equal(await owner.getByRole('link', { name: 'Descargar reporte', exact: true }).count(), 0);
    }
    phase = 'worker-real';
    const ready = await control('process-jobs');
    assert.equal(ready.files.length, 3);
    const routes = [];
    for (const job of report.jobs) {
      await owner.goto(input.base + '/reportes/' + job.id);
      const href = await owner.getByRole('link', { name: 'Descargar reporte', exact: true }).getAttribute('href');
      assert.match(href, /^\/archivos\/[0-9a-f-]{36}\/descargar(?:\?|$)/);
      routes.push(href);
      await owner.screenshot({ path: path.join(input.output, 'reporte-' + job.format.toLowerCase() + '-completo.png'), fullPage: true });
    }
    // Conserva la cookie de la primera sesión antes del logout; nunca la escribe a disco.
    const stale = await browser.newContext({ ignoreHTTPSErrors: true, storageState: await owner.context().storageState() });
    contexts.push(stale);
    phase = 'logout-before-download';
    await owner.getByRole('button', { name: 'Cerrar sesión', exact: true }).first().click();
    await owner.waitForURL('**/login');
    for (const route of routes) {
      const result = await stale.request.get(input.base + route, { maxRedirects: 0 });
      assert.ok([302, 401].includes(result.status()));
      const headers = result.headers();
      assert.equal(headers['content-disposition'], undefined);
      const destination = headers.location;
      if (destination) assert.equal(new URL(destination, input.base).pathname, '/login');
      assert.ok(!(await result.text()).includes('/portal-storage/v1/objects/'));
      report.denied.push(result.status());
    }
    await owner.screenshot({ path: path.join(input.output, 'sesion-cerrada-sin-descarga.png'), fullPage: true });
    await control('revoked-before-download');
    phase = 'new-owner-session-downloads';
    const authorized = await login();
    for (const job of report.jobs) {
      await authorized.goto(input.base + '/reportes/' + job.id);
      const expected = ready.files.find(file => file.job === job.id);
      assert.ok(expected);
      const pending = authorized.waitForEvent('download');
      await authorized.getByRole('link', { name: 'Descargar reporte', exact: true }).click();
      const download = await pending;
      const name = 'reporte.' + job.format.toLowerCase();
      const target = path.join(input.output, name);
      await download.saveAs(target);
      const bytes = fs.readFileSync(target);
      assert.equal(bytes.length, expected.size);
      const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
      assert.equal(sha256, expected.sha256);
      report.downloads.push({ job: job.id, format: job.format, name, size: bytes.length, sha256 });
    }
    await control('downloads-complete');
    assert.equal(report.javascript_errors, 0);
    report.passed = true;
  } catch (error) {
    report.failure_phase = phase;
    report.failure_type = error.name;
    process.exitCode = 1;
    if (pages.length) await pages[pages.length - 1].screenshot({ path: path.join(input.output, 'fallo.png'), fullPage: true }).catch(() => {});
  } finally {
    for (const page of pages) {
      try {
        const close = page.getByRole('button', { name: 'Cerrar sesión', exact: true }).first();
        if (await close.isVisible()) await close.click();
      } catch (_) { /* El fixture privado conserva el fallo y cierra sus motores. */ }
    }
    fs.writeFileSync(path.join(input.output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    await browser.close();
    channel.close();
  }
})();
