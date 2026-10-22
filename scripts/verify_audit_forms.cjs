'use strict';
// Solo un entorno de pruebas aislado: credenciales por stdin, sin registrarlas.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.REDHOUSE_PLAYWRIGHT || path.resolve(__dirname, '../.local/gcp-public/browser/node_modules/playwright'));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
assert.equal(new URL(input.base).hostname, '127.0.0.1');
const report = {checks: [], errors: [], startedAt: new Date().toISOString()};
const check = text => report.checks.push(text);

(async () => {
  fs.mkdirSync(input.output, {recursive: true});
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  let page;
  try {
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
    page = await context.newPage();
    page.on('pageerror', error => report.errors.push(error.message));
    const login = async user => {
      await context.clearCookies();
      await page.goto(input.base + '/login');
      await page.locator('#login_email').fill(user);
      await page.locator('#password').fill(input.password);
      await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
    };
    const save = async expected => {
      await Promise.all([page.waitForURL(expected), page.locator('main form button[type=submit]').last().click()]);
    };
    await login('medical1');
    await page.goto(input.base + '/donantes/donor/nuevo');
    assert.equal(await page.locator('[aria-invalid=true]').count(), 0);
    await page.locator('#folio').fill('BROWSER-' + Date.now());
    await page.locator('#display_name').fill('Persona ficticia de verificación');
    await page.locator('#blood_group').selectOption('O+');
    await page.locator('#consent').check();
    await page.locator('#restrictions').fill('abc');
    await page.locator('#background').fill('abcd');
    assert.equal(await page.locator('[aria-invalid=true]').count(), 0);
    assert.ok(await page.locator('#restrictions-help').isVisible());
    await page.locator('main form button[type=submit]').click();
    assert.equal(await page.locator('[aria-invalid=true]').count(), 2);
    assert.equal(await page.locator('#background').evaluate(e => getComputedStyle(e).borderColor), 'rgb(162, 28, 50)', 'Borde de error visible');
    assert.equal(await page.locator('#form-error').evaluate(e => document.activeElement === e), true, 'Foco inicial en resumen');
    await page.locator('#form-error a').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#restrictions').evaluate(e => document.activeElement === e), true, 'Enlace con teclado enfoca el campo');
    await page.setViewportSize({width: 390, height: 844});
    // Esperar a que termine la transición responsive de la barra lateral.
    await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth, null, {timeout:5000});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'El formulario cabe en 390 píxeles');
    await page.screenshot({path: path.join(input.output, 'errores-movil.png'), fullPage: true});
    check('Sin errores iniciales; ayuda permanente; dos errores tras enviar; foco, enlaces con teclado y vista móvil');
    await page.locator('#restrictions').fill('Restricciones documentadas');
    await page.locator('#background').fill('Antecedentes documentados');
    await page.locator('#consent_reference').fill('Referencia de consentimiento ficticia');
    await page.locator('main form button[type=submit]').click();
    await page.waitForLoadState('networkidle');
    assert.equal(await page.locator('[aria-invalid=true]').count(), 2);
    assert.equal(await page.locator('#consent').isChecked(), true);
    assert.equal(await page.locator('#display_name').inputValue(), 'Persona ficticia de verificación');
    assert.equal(await page.locator('#form-error').evaluate(e => document.activeElement === e), true, 'El resumen del servidor recibe foco');
    await page.locator('#consent_at').fill('2026-10-01T10:00');
    await save(/\/donantes\/donor\/[a-f0-9-]+$/);
    const donor = new URL(page.url()).pathname.split('/').pop();
    check('Dependencia de consentimiento detectada por servidor; datos y confirmación conservados; corrección guardada');
    // Las API de prueba centralizan el outbox antes de investigar el nuevo registro.
    const drained = await page.request.post(input.base + '/test/drain');
    assert.equal(drained.status(), 200, 'Eventos centralizados en entorno de prueba');
    await page.setViewportSize({width: 1440, height: 1000});
    await login('auditor1');
    await page.goto(input.base + '/auditoria');
    assert.equal(await page.locator('[name=categories]:checked').count(), 3);
    await page.locator('#filter-resource').fill(donor);
    await page.locator('button[type=submit]').filter({hasText:'Aplicar filtros'}).click();
    await page.waitForLoadState('networkidle');
    assert.ok((await page.locator('main').innerText()).includes('Donante registrado'));
    await page.screenshot({path: path.join(input.output, 'auditoria-filtrada.png'), fullPage: true});
    const download = page.waitForEvent('download');
    await page.getByText('Exportar resultados filtrados', {exact:true}).click();
    await (await download).saveAs(path.join(input.output, 'auditoria.csv'));
    await page.getByText('Investigar', {exact:true}).first().click();
    assert.ok((await page.getByText('Volver al listado filtrado').getAttribute('href')).includes(donor));
    await page.getByText('Registrar hallazgo', {exact:true}).click();
    await page.locator('#description').fill('Revisar evidencia documental de la operación ficticia');
    await page.locator('#priority').selectOption('HIGH');
    await page.locator('#assignee_id').selectOption(input.coordinator);
    await page.locator('#evidence').fill('Acta de revisión del entorno de pruebas');
    await save(/\/hallazgos\/[a-f0-9-]+$/);
    const findingPath = new URL(page.url()).pathname;
    check('Categorías iniciales, filtro, CSV completo, regreso al listado y alta de hallazgo desde evento');
    await login('coordinator1');
    await page.goto(input.base + findingPath);
    await page.getByText('Iniciar atención', {exact:true}).click();
    await page.locator('#corrective_action').fill('Revisar el documento y registrar la corrección');
    await page.locator('#reason').fill('Atender el hallazgo asignado');
    await page.locator('#human_confirmation').check();
    await save(/\/hallazgos\/[a-f0-9-]+$/);
    await page.getByText('Enviar a verificación', {exact:true}).click();
    await page.locator('#corrective_action').fill('Documento revisado y evidencia agregada');
    await page.locator('#reason').fill('Solicitar verificación del auditor');
    await page.locator('#evidence').fill('Referencia del documento corregido de prueba');
    await page.locator('#human_confirmation').check();
    await save(/\/hallazgos\/[a-f0-9-]+$/);
    await login('auditor1');
    await page.goto(input.base + findingPath);
    await page.getByText('Verificar y cerrar', {exact:true}).click();
    await page.locator('#reason').fill('Verificación independiente completada');
    await page.locator('#human_confirmation').check();
    await page.locator('main form button[type=submit]').click();
    assert.equal(await page.locator('#evidence').getAttribute('aria-invalid'), 'true');
    await page.locator('#evidence').fill('Evidencia de verificación independiente de prueba');
    await save(/\/hallazgos\/[a-f0-9-]+$/);
    assert.ok((await page.locator('main').innerText()).includes('Cerrado'));
    await page.screenshot({path: path.join(input.output, 'hallazgo-cerrado.png'), fullPage:true});
    check('Atención por coordinación, envío a verificación y cierre por auditoría; evidencia obligatoria e historial visible');
    assert.deepEqual(report.errors, []);
    report.passed = true;
    fs.rmSync(path.join(input.output, 'fallo.png'), {force:true});
    await context.close();
  } catch (error) {
    report.passed = false;
    report.failure = error.message;
    if (page && !page.isClosed()) {
      await page.screenshot({path: path.join(input.output, 'fallo.png'), fullPage:true});
      report.focus = await page.evaluate(() => document.activeElement?.id);
    }
    throw error;
  } finally {
    await browser.close();
    report.finishedAt = new Date().toISOString();
    fs.writeFileSync(path.join(input.output, 'navegador.json'), JSON.stringify(report, null, 2));
  }
  console.log(JSON.stringify({checks:report.checks.length, errors:report.errors.length}));
})().catch(error => {console.error(error.message); process.exitCode=1;});
