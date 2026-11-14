'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const { chromium } = require(path.join(input.root, '.local/gcp-public/browser/node_modules/playwright'));
const report = { passed: false, documents: [], checks: [] };

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const pages = [];
  let phase = 'login';
  try {
    async function login(username) {
      const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1280, height: 960 } });
      const page = await context.newPage();
      pages.push(page);
      await page.goto(input.base + '/login');
      await page.locator('#login_email').fill(username);
      await page.locator('#password').fill(input.password);
      await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
      return page;
    }
    const owner = await login('admin1');
    const create = '/documentos/nuevo?subject_kind=ACCREDITATION&subject_id=' + input.subject;
    async function upload(route, source, expected) {
      await owner.goto(input.base + route);
      await owner.locator('#evidence').setInputFiles(source.path);
      await owner.locator('#policy_reference').fill('Política sintética de prueba; sin uso operativo');
      const response = owner.waitForResponse(r => new URL(r.url()).pathname === '/documentos/nuevo' && r.request().method() === 'POST');
      await owner.getByRole('button', { name: 'Preparar, cargar y analizar', exact: true }).click();
      assert.equal((await response).status(), expected);
      if (expected === 303) {
        await owner.waitForURL(/\/documentos\/[0-9a-f-]{36}$/);
        return new URL(owner.url()).pathname.split('/').pop();
      }
      assert.ok(await owner.locator('#document-error').isVisible());
      return null;
    }
    async function download(identifier, source, name) {
      await owner.goto(input.base + '/documentos/' + identifier);
      const pending = owner.waitForEvent('download');
      await owner.getByRole('link', { name: 'Descargar objeto verificado', exact: true }).click();
      const item = await pending;
      const destination = path.join(input.output, name);
      await item.saveAs(destination);
      assert.equal(crypto.createHash('sha256').update(fs.readFileSync(destination)).digest('hex'), source.sha256);
    }
    phase = 'first-upload';
    const first = await upload(create, input.files[0], 303);
    report.documents.push(first);
    await owner.screenshot({ path: path.join(input.output, 'primera-version.png'), fullPage: true });
    await download(first, input.files[0], 'descarga-v1.png');
    phase = 'replacement';
    const second = await upload(create + '&supersedes=' + first, input.files[1], 303);
    report.documents.push(second);
    await download(second, input.files[1], 'descarga-v2.png');
    await download(first, input.files[0], 'descarga-v1-conservada.png');
    report.checks.push('Two real uploads and exact downloads; original version remains readable');
    phase = 'stale-version';
    await upload(create + '&supersedes=' + first, input.files[1], 412);
    await owner.screenshot({ path: path.join(input.output, 'version-obsoleta.png'), fullPage: true });
    report.checks.push('Stale predecessor rejects a branch with 412');
    phase = 'foreign-scope';
    const foreign = await login('admin2');
    assert.equal((await foreign.goto(input.base + '/documentos/' + second)).status(), 403);
    await owner.goto(input.base + '/documentos/' + second);
    const downloadPath = await owner.getByRole('link', { name: 'Descargar objeto verificado', exact: true }).getAttribute('href');
    assert.equal((await foreign.request.get(input.base + downloadPath, { maxRedirects: 0 })).status(), 403);
    await foreign.screenshot({ path: path.join(input.output, 'institucion-ajena.png'), fullPage: true });
    report.checks.push('Other institution receives 403 for detail and download authorization');
    phase = 'logout';
    await owner.getByRole('button', { name: 'Cerrar sesión', exact: true }).first().click();
    await owner.waitForURL('**/login');
    const after = await owner.request.get(input.base + downloadPath, { maxRedirects: 0 });
    assert.ok([302, 401].includes(after.status()));
    assert.equal(after.headers()['content-disposition'], undefined);
    report.checks.push('Logged-out browser cannot request a new download');
    report.passed = true;
  } catch (error) {
    // Exceptions can contain signed URLs or browser inputs; retain only the phase.
    report.failure_phase = phase;
    report.failure_type = error.name;
    process.exitCode = 1;
    if (!['login', 'foreign-scope'].includes(phase) && pages[0]) {
      await pages[0].screenshot({ path: path.join(input.output, 'fallo.png'), fullPage: true }).catch(() => {});
    }
  } finally {
    for (const page of pages) {
      try {
        const button = page.getByRole('button', { name: 'Cerrar sesión', exact: true }).first();
        if (await button.isVisible()) await button.click();
      } catch (_) { /* Fixture is private and is stopped by pytest on failure. */ }
    }
    fs.writeFileSync(path.join(input.output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ passed: report.passed, failure_phase: report.failure_phase }));
    await browser.close();
  }
})();
