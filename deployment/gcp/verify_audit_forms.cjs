'use strict';
// Verificación autorizada del despliegue académico. Conserva un hallazgo ficticio cerrado.
// Credenciales por stdin; los formularios de donantes solo se envían con datos inválidos.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.REDHOUSE_PLAYWRIGHT || path.resolve(__dirname, '../../.local/gcp-public/browser/node_modules/playwright'));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const base = 'https://34.18.186.116';
const report = {origin: base, startedAt: new Date().toISOString(), checks: [], validations: [], errors: [], pages: []};
const check = name => report.checks.push({name, passed: true});

(async () => {
  fs.mkdirSync(input.output, {recursive: true});
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  let page;
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
  try {
    page = await context.newPage();
    page.on('pageerror', error => report.errors.push(error.message));
    const visit = async route => {
      const response = await page.goto(base + route);
      assert.equal(response.status(), 200, route);
      report.pages.push(route);
    };
    const logout = async () => {
      const csrf = page.locator('input[name=csrf_token]').first();
      if (await csrf.count()) {
        const response = await context.request.post(base + '/logout', {
          form: {csrf_token: await csrf.inputValue()}, headers: {Referer: page.url()}, maxRedirects: 0
        });
        assert.equal(response.status(), 302);
      }
      await context.clearCookies();
    };
    const login = async user => {
      if (page.url().startsWith(base)) await logout();
      await visit('/login');
      await page.locator('#login_email').fill(user);
      await page.locator('#password').fill(input.password);
      await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
    };
    const save = async () => {
      await Promise.all([
        page.waitForURL(/\/hallazgos\/[a-f0-9-]+$/),
        page.locator('main form button[type=submit]').last().click()
      ]);
    };
    await login('medical1');
    await visit('/donantes/donor/nuevo');
    assert.equal(await page.locator('[aria-invalid=true]').count(), 0);
    const fillDonor = async () => {
      await page.locator('#folio').fill('CHECK-' + Date.now());
      await page.locator('#display_name').fill('Validación ficticia sin guardar');
      await page.locator('#blood_group').selectOption('O+');
      await page.locator('#consent').check();
    };
    await fillDonor();
    await page.locator('#restrictions').fill('abc');
    await page.locator('#background').fill('abcd');
    assert.equal(await page.locator('[aria-invalid=true]').count(), 0);
    assert.ok(await page.locator('#restrictions-help').isVisible());
    await page.locator('main form button[type=submit]').click();
    assert.equal(await page.locator('[aria-invalid=true]').count(), 2);
    assert.equal(await page.locator('#form-error').evaluate(el => document.activeElement === el), true);
    await page.locator('#form-error a').first().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#restrictions').evaluate(el => document.activeElement === el), true);
    await page.setViewportSize({width: 390, height: 844});
    await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth);
    await page.screenshot({path: path.join(input.output, 'errores-movil.png'), fullPage: true});
    check('Ayudas y límites; errores después de enviar; foco y teclado; formulario móvil sin desbordamiento');
    await page.setViewportSize({width: 1440, height: 1000});
    const cases = [
      ['Restricciones de tres caracteres', {restrictions: 'abc'}, ['restrictions']],
      ['Antecedentes de cuatro caracteres', {background: 'abcd'}, ['background']],
      ['Referencia de consentimiento sin fecha', {consent_reference: 'Referencia ficticia'}, ['consent_reference', 'consent_at']],
      ['Consentimiento con fecha futura', {consent_reference: 'Referencia ficticia', consent_at: '2099-01-01T10:00'}, ['consent_at']]
    ];
    for (const [name, values, fields] of cases) {
      await visit('/donantes/donor/nuevo');
      await fillDonor();
      for (const [key, value] of Object.entries(values)) await page.locator('#' + key).fill(value);
      const waiting = page.waitForResponse(response => response.request().method() === 'POST' && new URL(response.url()).pathname === '/donantes/donor/nuevo');
      await page.locator('main form').evaluate(form => form.submit());
      const response = await waiting;
      assert.equal(response.status(), 422, name);
      await page.waitForLoadState('networkidle');
      assert.equal(await page.locator('#display_name').inputValue(), 'Validación ficticia sin guardar');
      assert.equal(await page.locator('#consent').isChecked(), true);
      for (const field of fields) assert.equal(await page.locator('#' + field).getAttribute('aria-invalid'), 'true', field);
      report.validations.push({name, status: response.status(), fields, summary: await page.locator('#form-error').innerText(), valuesPreserved: true});
    }
    await page.screenshot({path: path.join(input.output, 'errores-servidor.png'), fullPage: true});
    check('Cuatro errores originales: HTTP 422 con campos y mensajes concretos; valores y consentimiento conservados');
    await visit('/donantes/donor');
    const donorPath = await page.locator('a[data-record-view]').first().getAttribute('href');
    const donor = new URL(donorPath, base).pathname.split('/').pop();
    report.resourceId = donor;
    await login('auditor1');
    await visit('/auditoria');
    assert.equal(await page.locator('[name=categories]:checked').count(), 3);
    await page.locator('#filter-resource').fill(donor);
    await page.getByRole('button', {name: 'Aplicar filtros'}).click();
    await page.waitForLoadState('networkidle');
    assert.ok((await page.locator('main').innerText()).includes('Donante registrado'));
    await page.screenshot({path: path.join(input.output, 'auditoria-filtrada.png'), fullPage: true});
    const downloading = page.waitForEvent('download');
    await page.getByText('Exportar resultados filtrados', {exact: true}).click();
    await (await downloading).saveAs(path.join(input.output, 'auditoria.csv'));
    await page.getByText('Investigar', {exact: true}).first().click();
    report.eventId = new URL(page.url()).pathname.split('/').pop();
    assert.ok((await page.getByText('Volver al listado filtrado').getAttribute('href')).includes(donor));
    await page.getByText('Registrar hallazgo', {exact: true}).click();
    await page.locator('#description').fill('Verificación técnica ficticia de auditoría y formularios tras el despliegue de GCP del 21 de octubre de 2026');
    await page.locator('#priority').selectOption('LOW');
    await page.locator('#assignee_id').selectOption(input.coordinator);
    await page.locator('#evidence').fill('Prueba académica del seguimiento; sin incidencia clínica ni cambio del expediente vinculado');
    await save();
    report.findingPath = new URL(page.url()).pathname;
    // Guardar la referencia inmediatamente para no duplicar el hallazgo si una comprobación posterior falla.
    fs.writeFileSync(path.join(input.output, 'navegador.json'), JSON.stringify(report, null, 2) + '\n');
    check('Categorías, filtro por recurso, CSV, detalle y regreso; alta de un hallazgo ficticio vinculado');
    await login('coordinator1');
    await visit(report.findingPath);
    await page.getByText('Iniciar atención', {exact: true}).click();
    await page.locator('#corrective_action').fill('Comprobar formularios y trazabilidad de la publicación académica');
    await page.locator('#reason').fill('Atender la comprobación técnica ficticia asignada');
    await page.locator('#human_confirmation').check();
    await save();
    await page.getByText('Enviar a verificación', {exact: true}).click();
    await page.locator('#corrective_action').fill('Formularios y seguimiento comprobados sobre el despliegue HTTPS');
    await page.locator('#reason').fill('Solicitar revisión independiente del resultado de la prueba');
    await page.locator('#evidence').fill('Capturas e informe de despliegue en documentation/evidencias/gcp/auditoria-formularios');
    await page.locator('#human_confirmation').check();
    await save();
    await login('auditor1');
    await visit(report.findingPath);
    await page.getByText('Verificar y cerrar', {exact: true}).click();
    await page.locator('#reason').fill('Verificación técnica independiente completada sin cambios clínicos');
    await page.locator('#human_confirmation').check();
    await page.locator('main form button[type=submit]').click();
    assert.equal(await page.locator('#evidence').getAttribute('aria-invalid'), 'true');
    await page.locator('#evidence').fill('Informe y capturas de la verificación académica del despliegue HTTPS');
    await save();
    assert.ok((await page.locator('main').innerText()).includes('Cerrado'));
    await page.screenshot({path: path.join(input.output, 'hallazgo-cerrado.png'), fullPage: true});
    check('Atención por responsable, verificación por auditor y cierre con evidencia obligatoria e historial');
    await logout();
    assert.deepEqual(report.errors, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed';
    report.failure = error.message;
    if (page && !page.isClosed()) await page.screenshot({path: path.join(input.output, 'fallo.png'), fullPage: true});
    throw error;
  } finally {
    report.finishedAt = new Date().toISOString();
    await context.close();
    await browser.close();
    fs.writeFileSync(path.join(input.output, 'navegador.json'), JSON.stringify(report, null, 2) + '\n');
  }
  console.log(JSON.stringify({result: report.result, checks: report.checks.length, validations: report.validations.length, errors: report.errors.length}));
})().catch(error => {console.error(error.message); process.exitCode = 1;});
