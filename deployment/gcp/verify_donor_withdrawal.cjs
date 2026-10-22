'use strict';
// Cliente HTTPS: crea dos expedientes propios de prueba y da de baja ambos.
// No inicia servidores locales ni interviene registros preexistentes.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const {chromium} = require('playwright');
const base = 'https://34.18.186.116';
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const output = 'documentation/evidencias/gcp/bajas-donantes';
fs.mkdirSync(output, {recursive: true});
const report = {startedAt: new Date().toISOString(), origin: base, checks: [], records: [], dialogs: [], errors: []};

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  let access;
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('dialog', async dialog => {report.dialogs.push(dialog.type()); await dialog.accept();});
  const api = async (method, route, data, expected = 200) => {
    const response = await context.request.fetch(base + '/services/donantes' + route, {
      method, data,
      headers: {Authorization: 'Bearer ' + access, 'Idempotency-Key': crypto.randomUUID()}
    });
    assert.equal(response.status(), expected, method + ' ' + route);
    return expected < 300 ? (await response.json()).data : undefined;
  };
  try {
    const login = await context.request.post(base + '/services/identidad-acceso/api/v1/auth/login', {
      data: {username: 'medical1', password: state.password}
    });
    assert.equal(login.status(), 200, 'API login');
    access = (await login.json()).data.access_token;
    assert.equal((await page.goto(base + '/login')).status(), 200);
    await page.locator('#login_email').fill('medical1');
    await page.locator('#password').fill(state.password);
    await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);

    for (const withHistory of [false, true]) {
      const folio = 'CHECK-' + crypto.randomUUID().slice(0, 8).toUpperCase();
      const donor = await api('POST', '/api/v1/donors', {
        folio, display_name: 'Registro temporal de verificación', blood_group: 'O+', consent: true
      }, 201);
      const record = {id: donor.id, folio, withHistory};
      report.records.push(record);
      if (withHistory) {
        await api('POST', '/api/v1/donors/' + donor.id + '/reviews', {
          version: donor.version, decision: 'ELIGIBLE', human_confirmation: true,
          reason: 'Verificación de conservación del historial al dar de baja'
        }, 201);
      } else {
        const edit = base + '/registros/donors/' + donor.id + '/editar';
        for (const selector of ['a.back-link', 'a[data-action-cancel]']) {
          assert.equal((await page.goto(edit)).status(), 200);
          await page.locator('#display_name').fill('Cambio que se descarta al salir');
          await Promise.all([page.waitForURL(url => url.pathname !== new URL(edit).pathname), page.locator(selector).click()]);
          assert.equal((await api('GET', '/api/v1/donors/' + donor.id)).display_name, 'Registro temporal de verificación');
          report.checks.push({name: selector === 'a.back-link' ? 'Volver sin aviso' : 'Cancelar sin aviso', passed: true});
        }
        await page.goto(edit);
        await page.locator('#display_name').fill('Cambio descartado al recargar');
        assert.equal((await page.reload()).status(), 200);
        assert.equal(await page.locator('#display_name').inputValue(), 'Registro temporal de verificación');
        report.checks.push({name: 'Recargar sin aviso y sin guardar', passed: true});
      }
      await page.goto(base + '/donantes/donor?q=' + folio);
      await Promise.all([
        page.waitForURL('**/' + donor.id + '/baja*'),
        page.getByRole('link', {name: 'Retirar donante ' + folio, exact: true}).click()
      ]);
      await page.locator('#reason').fill('Baja del registro creado para verificar esta función');
      await page.locator('#human_confirmation').check();
      await Promise.all([
        page.waitForURL(url => url.pathname === '/donantes/donor'),
        page.getByRole('button', {name: 'Retirar donante', exact: true}).click()
      ]);
      assert.equal(Number(await page.locator('#filter-results').getAttribute('data-result-count')), 0);
      assert.equal((await api('GET', '/api/v1/donors?q=' + folio)).total, 0);
      if (withHistory) {
        const archived = await api('GET', '/api/v1/donors/' + donor.id);
        assert.equal(archived.status, 'INACTIVE');
        assert.equal(archived.reviews.length, 1);
        assert.ok(archived.decisions.some(row => row.action === 'DONOR_WITHDRAWN'));
        await page.goto(base + '/donantes/donor/' + donor.id);
        assert.ok((await page.locator('main').innerText()).includes('Puedes consultar sus antecedentes'));
        assert.equal(await page.locator('a[href*="/baja"]').count(), 0);
        assert.equal(await page.getByRole('link', {name: 'Registrar donación', exact: true}).count(), 0);
        await page.screenshot({path: path.join(output, 'baja-con-historial.png')});
        record.result = 'INACTIVE';
      } else {
        await api('GET', '/api/v1/donors/' + donor.id, undefined, 404);
        record.result = 'DELETED';
      }
      report.checks.push({name: withHistory ? 'Baja conserva historial' : 'Baja elimina registro vacío', passed: true});
    }
    assert.deepEqual(report.dialogs, []);
    assert.deepEqual(report.errors, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed';
    report.failure = error.message;
    throw error;
  } finally {
    try {
      if (access) await context.request.post(base + '/services/identidad-acceso/api/v1/auth/logout', {
        headers: {Authorization: 'Bearer ' + access}
      });
      const csrf = page.locator('input[name=csrf_token]').first();
      if (await csrf.count()) await context.request.post(base + '/logout', {
        form: {csrf_token: await csrf.inputValue()}, headers: {Referer: page.url()}, maxRedirects: 0
      });
    } finally {
      await browser.close();
      report.completedAt = new Date().toISOString();
      fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
    }
  }
  console.log(JSON.stringify({result: report.result, checks: report.checks.length, dialogs: report.dialogs.length, errors: report.errors.length}));
})().catch(error => {console.error(error.message); process.exitCode = 1;});
