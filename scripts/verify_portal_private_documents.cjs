'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const readline = require('node:readline');
const report = { passed: false, documents: [], checks: [] };

(async () => {
  const channel = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  const commands = channel[Symbol.asyncIterator]();
  const initial = await commands.next();
  const input = JSON.parse(initial.value);
  const { chromium } = require(path.join(input.root, '.local/gcp-public/browser/node_modules/playwright'));
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  if (input.scenario === 'scanner-failure') {
    // El orquestador puede abortar durante un control; cerrar también Chrome.
    process.once('SIGTERM', () => {
      channel.close();
      browser.close().catch(() => {});
    });
  }
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
      await owner.locator('#evidence').setInputFiles(source.mime ? {
        name: path.basename(source.path), mimeType: source.mime, buffer: fs.readFileSync(source.path),
      } : source.path);
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
    async function scannerControl(action, document) {
      console.log(JSON.stringify({ control: action, document }));
      let timer;
      let next;
      try {
        next = await Promise.race([commands.next(), new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error('Scanner control timed out')), 150000);
        })]);
      } finally { clearTimeout(timer); }
      assert.equal(next.done, false);
      const answer = JSON.parse(next.value);
      assert.deepEqual(answer, { control: action, passed: true });
    }
    async function preparedAfterFailure() {
      const link = owner.getByRole('link', { name: 'Consultar el documento preparado y recuperar su verificación', exact: true });
      const href = await link.getAttribute('href');
      assert.match(href, /^\/documentos\/[0-9a-f-]{36}$/);
      await link.click();
      await owner.waitForURL(input.base + href);
      return href.split('/').pop();
    }
    async function deniedDownload(identifier) {
      assert.equal(await owner.getByRole('link', { name: 'Descargar objeto verificado', exact: true }).count(), 0);
      const response = await owner.request.get(input.base + '/archivos/' + identifier + '/descargar', { maxRedirects: 0 });
      assert.equal(response.status(), 409);
      assert.equal(response.headers()['location'], undefined);
      assert.equal(response.headers()['content-disposition'], undefined);
    }
    if (input.scenario === 'scanner-failure') {
      report.scenario = input.scenario;
      assert.equal(input.files[0].mime, 'application/pdf');
      assert.equal(input.files[1].mime, 'image/png');
      report.scope = ['I06-03', 'I06-04', 'I06-05'];
      const mutations = { prepare: 0, verify: 0 };
      owner.on('request', request => {
        if (request.method() !== 'POST') return;
        const route = new URL(request.url()).pathname;
        if (route === '/documentos/nuevo') mutations.prepare++;
        if (/^\/documentos\/[0-9a-f-]{36}\/verificar$/.test(route)) mutations.verify++;
      });
      phase = 'infected-upload';
      await upload(create, input.files[0], 422);
      const infected = await preparedAfterFailure();
      report.documents.push(infected);
      await deniedDownload(infected);
      await owner.screenshot({ path: path.join(input.output, 'infectado-rechazado.png'), fullPage: true });
      report.checks.push('Admitted infected PDF rejects verification and download');
      phase = 'scanner-stop';
      await scannerControl('scanner-stop', infected);
      phase = 'scanner-down-upload';
      await upload(create, input.files[1], 503);
      const recovering = await preparedAfterFailure();
      report.documents.push(recovering);
      assert.notEqual(recovering, infected);
      await deniedDownload(recovering);
      await owner.screenshot({ path: path.join(input.output, 'scanner-no-disponible.png'), fullPage: true });
      report.checks.push('Stopped real scanner leaves document unavailable for download');
      phase = 'scanner-restart';
      await scannerControl('scanner-start', recovering);
      phase = 'recover-same-document';
      await owner.getByRole('link', { name: 'Analizar y verificar', exact: true }).click();
      const verifyPath = '/documentos/' + recovering + '/verificar';
      await owner.waitForURL(url => url.pathname === verifyPath);
      const verified = owner.waitForResponse(r => new URL(r.url()).pathname === verifyPath && r.request().method() === 'POST');
      await owner.locator('form.record-form button[type=submit]').click();
      assert.equal((await verified).status(), 302);
      await owner.waitForURL(url => url.pathname !== verifyPath);
      await download(recovering, input.files[1], 'descarga-recuperada.png');
      await owner.screenshot({ path: path.join(input.output, 'mismo-documento-recuperado.png'), fullPage: true });
      await owner.goto(input.base + '/documentos/' + infected);
      await deniedDownload(infected);
      assert.deepEqual(mutations, { prepare: 2, verify: 1 });
      report.mutations = mutations;
      report.checks.push('Same prepared document verified after restart; exact download; infected file remains blocked');
      await scannerControl('scanner-complete', recovering);
      report.scanner_passed = true;
      report.conservation = { passed: false };
      phase = 'conservation-open';
      await owner.goto(input.base + '/documentos/' + recovering);
      await owner.getByRole('link', { name: 'Conservación y bloqueo', exact: true }).click();
      const policyPath = '/documentos/' + recovering + '/conservacion';
      await owner.waitForURL(url => url.pathname === policyPath);
      const stale = await owner.context().newPage();
      pages.push(stale);
      await stale.goto(owner.url());
      assert.equal(await stale.locator('form.record-form input[name=policy_version]').inputValue(), '1');
      async function savePolicy(page, date, reason, version, expected) {
        const form = page.locator('form.record-form');
        assert.equal(await form.locator('input[name=policy_version]').inputValue(), version);
        assert.equal(await form.locator('input[name=_timezone]').inputValue(), input.conservation.timezone);
        await form.locator('#retention_until').fill(date);
        await form.locator('#legal_hold').check();
        await form.locator('#policy_reference').fill(input.conservation.reference);
        await form.locator('#reason').fill(reason);
        await form.locator('#human_confirmation').check();
        const response = page.waitForResponse(r => new URL(r.url()).pathname === policyPath && r.request().method() === 'POST');
        await form.locator('button[type=submit]').click();
        assert.equal((await response).status(), expected);
        if (expected === 302) await page.waitForURL(url => url.pathname !== policyPath);
        else assert.ok(await page.locator('#form-error').isVisible());
      }
      async function persistedPolicy() {
        await owner.goto(input.base + '/documentos/' + recovering);
        await owner.reload();
        const fact = label => owner.locator('dl.regional-facts > div').filter({ has: owner.getByText(label, { exact: true }) }).locator('dd');
        assert.equal(Date.parse(await fact('Conservación hasta').locator('time').getAttribute('datetime')), Date.parse(input.conservation.until_utc));
        assert.equal((await fact('Bloqueo de eliminación').textContent()).trim(), 'Sí');
      }
      phase = 'conservation-save';
      await savePolicy(owner, input.conservation.until_local, input.conservation.reason, '1', 302);
      await persistedPolicy();
      await scannerControl('conservation-saved', recovering);
      phase = 'conservation-stale';
      await savePolicy(stale, input.conservation.until_local, 'Ensayo sintético: formulario anterior sin autorización de sobrescritura.', '1', 412);
      assert.match(await stale.locator('#form-error').textContent(), /Política de conservación modificada/);
      report.conservation.stale_status = 412;
      phase = 'conservation-hold';
      await owner.getByRole('link', { name: 'Conservación y bloqueo', exact: true }).click();
      await owner.waitForURL(url => url.pathname === policyPath);
      await savePolicy(owner, input.conservation.shorter_local, 'Ensayo sintético: reducción rechazada por bloqueo vigente.', '2', 409);
      assert.match(await owner.locator('#form-error').textContent(), /bloqueo vigente impide reducir conservación/);
      report.conservation.hold_status = 409;
      await owner.screenshot({ path: path.join(input.output, 'conservacion-bloqueo.png'), fullPage: true });
      await persistedPolicy();
      await scannerControl('conservation-rejected', recovering);
      report.conservation.passed = true;
      report.checks.push('I06-03: retention saved, stale form 412 and hold reduction 409; policy remains unchanged');
      report.passed = true;
      return;
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
    if (input.scenario === 'scanner-failure') report.failure_scope = phase.startsWith('conservation-') ? 'I06-03' : (phase === 'login' ? 'setup' : (['infected-upload', 'scanner-stop'].includes(phase) ? 'I06-04' : 'I06-05'));
    report.failure_type = error.name;
    if (typeof error.actual === 'number' && typeof error.expected === 'number') {
      report.actual_status = error.actual;
      report.expected_status = error.expected;
    }
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
    channel.close();
  }
})();
