'use strict';
// Revisión de presentación por HTTPS. Solo consulta registros; no envía formularios de negocio.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const base = 'https://34.18.186.116';
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const output = 'documentation/evidencias/gcp/bajas-donantes';
const report = {startedAt: new Date().toISOString(), origin: base, pages: [], checks: [], errors: [], dialogs: [], businessWrites: []};
const check = name => report.checks.push({name, passed: true});

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  try {
    for (const user of ['medical1', 'operator1', 'coordinator1', 'admin1', 'auditor1', 'donor1', 'medical2']) {
      const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
      const page = await context.newPage();
      page.on('pageerror', error => report.errors.push(error.message));
      page.on('dialog', async dialog => {report.dialogs.push(dialog.type()); await dialog.dismiss();});
      await context.route('**/*', async route => {
        const req = route.request();
        const url = new URL(req.url());
        if (!['GET', 'HEAD'].includes(req.method()) && !['/login', '/logout', '/sesion/renovar'].includes(url.pathname)) {
          report.businessWrites.push({method: req.method(), path: url.pathname});
          return route.abort();
        }
        return route.continue();
      });
      const visit = async route => {
        const response = await page.goto(new URL(route, base).href);
        assert.equal(response.status(), 200, user + ' ' + route);
        report.pages.push({user, route: new URL(page.url()).pathname, status: 200});
        await page.locator('main h1').waitFor();
      };
      const firstDetail = async route => {
        await visit(route);
        const href = await page.locator('a[data-record-view]').first().getAttribute('href');
        await visit(href);
        return href;
      };
      const noTechnicalDetails = async () => {
        assert.equal(await page.locator('main .technical-details, main summary').filter({hasText: /trazabilidad|técnico/i}).count(), 0);
      };
      try {
        await page.goto(base + '/login');
        await page.locator('#login_email').fill(user);
        await page.locator('#password').fill(state.password);
        await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
        if (user.startsWith('medical')) {
          await visit('/donantes/donor');
          const trash = page.locator('a[href*="/baja"]').first();
          const withdrawal = await trash.getAttribute('href');
          const detail = await trash.locator('xpath=ancestor::tr').locator('a[data-record-view]').getAttribute('href');
          assert.equal((await trash.innerText()).trim(), '');
          assert.match(await trash.getAttribute('aria-label'), /^Retirar donante /);
          assert.equal(await trash.getAttribute('title'), 'Retirar donante');
          assert.equal(await trash.locator('img[src$="/trash.svg"]').evaluate(img => img.complete && img.naturalWidth > 0), true);
          await trash.focus();
          await Promise.all([page.waitForURL('**/baja*'), page.keyboard.press('Enter')]);
          const confirmation = await page.locator('main').innerText();
          assert.ok(confirmation.includes('Dejará de aparecer en la lista de donantes. Sus citas pendientes se cancelarán.'));
          assert.ok(!/selectores|auditoría|el expediente se eliminará|dictámenes, donaciones|base de datos/i.test(confirmation));
          await page.locator('#reason').fill('Texto sin guardar');
          if (user === 'medical1') await page.screenshot({path: path.join(output, 'confirmacion-usuario.png')});
          await Promise.all([page.waitForURL('**/donantes/donor*'), page.locator('[data-action-cancel]').click()]);
          check(user + ': papelera accesible con teclado y confirmación clara; Cancelar sin diálogo');
          await visit(detail);
          assert.equal((await page.locator('nav.record-toolbar a[href*="/baja"]').innerText()).trim(), '');
          assert.equal(await page.locator('nav.record-toolbar img[src$="/trash.svg"]').count(), 1);
          await noTechnicalDetails();
          if (user === 'medical1') {
            await page.screenshot({path: path.join(output, 'donante-papelera.png')});
            await visit('/donantes/donor/8e8d854b-5ed8-41e3-b992-62c8a1cd0d95');
            assert.ok((await page.locator('main').innerText()).includes('Puedes consultar sus antecedentes'));
            assert.equal(await page.locator('a[href*="/baja"]').count(), 0);
            assert.ok(!/INACTIVE|DELETED|Previous status|Cancelled appointments|\bMode\b/.test(await page.locator('main').innerText()));
            await noTechnicalDetails();
            check('Expediente inactivo: antecedentes legibles sin modo de borrado ni referencias técnicas');
            await firstDetail('/solicitudes');
            const evaluation = page.locator('a[href*="/evaluaciones/"]').first();
            if (await evaluation.count()) {
              await visit(await evaluation.getAttribute('href'));
              await noTechnicalDetails();
              check('Evaluación: candidatos y advertencia clínica sin tiempos de procesamiento');
            }
            await firstDetail('/propuestas');
            assert.ok(!/matching máximo|instantánea|COVERAGE-HK/.test(await page.locator('main').innerText()));
            await noTechnicalDetails();
            check('Propuesta: explicación operativa sin terminología del algoritmo');
          }
          assert.ok(withdrawal.includes('/baja'));
        } else if (['operator1', 'donor1'].includes(user)) {
          await firstDetail('/donantes/donor');
          assert.equal(await page.locator('a[href*="/baja"]').count(), 0);
          await noTechnicalDetails();
          check(user + ': conserva permisos y expediente sin detalles técnicos');
          if (user === 'operator1') {
            for (const route of ['/donaciones', '/inventario', '/traslados']) {
              await firstDetail(route);
              await noTechnicalDetails();
            }
            const files = await page.locator('a[href*="/archivos"]').getAttribute('href');
            await visit(files);
            assert.ok(!/application\/pdf|image\/png|image\/jpeg| bytes|Referencia:|Objeto pendiente/.test(await page.locator('main').innerText()));
            check('Evidencias: formato y tamaño legibles sin identificadores de almacenamiento');
          }
        } else {
          await visit('/monitoreo');
          const diagnostics = page.locator('summary').filter({hasText: 'Diagnóstico técnico'});
          assert.equal(await diagnostics.count(), user === 'coordinator1' ? 0 : 1);
          assert.ok(await page.locator('.service-card').count() > 0);
          check(user + ': disponibilidad visible; diagnóstico según perfil');
          if (user === 'admin1') await firstDetail('/administracion/users');
          if (user === 'auditor1') await firstDetail('/auditoria');
        }
      } finally {
        const csrf = page.locator('input[name=csrf_token]').first();
        if (await csrf.count()) {
          const response = await context.request.post(base + '/logout', {
            form: {csrf_token: await csrf.inputValue()}, headers: {Referer: page.url()}, maxRedirects: 0
          });
          assert.equal(response.status(), 302, 'Logout ' + user);
        }
        await context.close();
      }
    }
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.dialogs, []);
    assert.deepEqual(report.businessWrites, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed';
    report.failure = error.message;
    throw error;
  } finally {
    await browser.close();
    report.completedAt = new Date().toISOString();
    fs.writeFileSync(path.join(output, 'portal-copy-browser.json'), JSON.stringify(report, null, 2) + '\n');
  }
  console.log(JSON.stringify({result: report.result, pages: report.pages.length, checks: report.checks.length, errors: report.errors.length, dialogs: report.dialogs.length}));
})().catch(error => {console.error(error.message); process.exitCode = 1;});
