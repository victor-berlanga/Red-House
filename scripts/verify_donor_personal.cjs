'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const {chromium} = require(path.join(input.browserRoot, '.local/gcp-public/browser/node_modules/playwright'));

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  const report = {passed: false, stage: 'context', checks: [], certificate: 'self-signed isolated fixture; exception limited to browser context'};
  try {
    const context = await browser.newContext({ignoreHTTPSErrors: true, viewport: {width: 1280, height: 900}});
    const page = await context.newPage();
    report.stage = 'login-page';
    await page.goto(input.base + '/login', {waitUntil: 'domcontentloaded'});
    report.stage = 'credentials';
    await page.locator('#login_email').fill(input.user);
    await page.locator('#password').fill(input.password);
    report.stage = 'login-submit';
    await Promise.all([page.waitForURL('**/panel', {waitUntil: 'domcontentloaded'}), page.locator('button[type=submit]').click()]);
    report.stage = 'donor-detail';
    await page.goto(input.base + '/donantes/donor/' + input.donorId, {waitUntil: 'domcontentloaded'});
    report.stage = 'edit-link';
    await page.getByRole('link', {name: 'Editar mi nombre', exact: true}).click();
    report.stage = 'edit-form';
    await page.locator('#display_name').waitFor({state: 'visible'});
    assert.equal(await page.locator('#display_name').inputValue(), input.previousName);
    assert.equal(await page.locator('form.record-form input:not([type=hidden])').count(), 1);
    report.stage = 'visual-capture';
    for (const width of [390, 1280]) {
      await page.setViewportSize({width, height: 900});
      // Let the real responsive navigation transition finish before evidence capture.
      await page.waitForTimeout(500);
      await page.screenshot({path: path.join(input.output, 'editar-nombre-' + width + '.png'), fullPage: true});
    }
    report.stage = 'keyboard';
    await page.locator('#display_name').focus();
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
    await page.keyboard.type(input.newName);
    await page.keyboard.press('Tab');
    assert.ok(await page.locator('form.record-form').evaluate(form => form.contains(document.activeElement)));
    report.stage = 'save';
    const changed = page.waitForResponse(response => response.request().method() === 'POST' && new URL(response.url()).pathname.endsWith('/mis-datos'));
    await page.locator('form.record-form button[type=submit]').click();
    assert.equal((await changed).status(), 302);
    report.stage = 'donor-detail';
    await page.goto(input.base + '/donantes/donor/' + input.donorId, {waitUntil: 'domcontentloaded'});
    assert.ok((await page.locator('main').innerText()).includes(input.newName));
    assert.ok(!/\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i.test(await page.locator('main').innerText()));
    await page.screenshot({path: path.join(input.output, 'nombre-guardado.png'), fullPage: true});
    report.checks.push('Enlace del expediente propio, formulario limitado a nombre, teclado y guardado real tras recargar');
    report.stage = 'complete';
    report.passed = true;
  } catch (error) {
    // No serializar contexto, peticiones ni argumentos que contienen credenciales.
    report.errorType = error.name;
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(input.output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report));
    await browser.close();
  }
})();
