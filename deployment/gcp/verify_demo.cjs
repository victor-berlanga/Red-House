'use strict';
// Cliente del portal GCP; no inicia servidores ni modifica registros de negocio.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const base = 'https://34.18.186.116';
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const output = 'documentation/evidencias/gcp/datos-demo';
fs.mkdirSync(output, {recursive: true});
const report = {date: new Date().toISOString(), origin: base, pages: [], errors: [], localRequests: []};

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  try {
    for (const institution of [1, 2]) {
      const cases = [
        ['operator', ['/donantes/donor', '/donantes/donor?page=2', '/campanas', '/campanas?page=2', '/citas', '/donaciones', '/inventario']],
        ['medical', ['/donantes/recipient', '/solicitudes']],
        ['donor', ['/donantes/donor', '/campanas', '/citas']],
        ['admin', ['/catalogos/sites', '/catalogos/contacts', '/catalogos/schedules', '/catalogos/capacities', '/catalogos/locations']]
      ];
      for (const [role, routes] of cases) {
        const user = role + institution;
        const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: 'reduce'});
        const page = await context.newPage();
        page.on('pageerror', error => report.errors.push(error.message));
        page.on('request', request => {
          const url = new URL(request.url());
          if (['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) report.localRequests.push(url.pathname);
        });
        try {
          assert.equal((await page.goto(base + '/login')).status(), 200);
          await page.locator('#login_email').fill(user);
          await page.locator('#password').fill(state.password);
          await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
          for (const route of routes) {
            const response = await page.goto(base + route, {waitUntil: 'networkidle'});
            assert.equal(response.status(), 200, user + ' ' + route);
            const results = page.locator('#filter-results');
            const total = Number(await results.getAttribute('data-result-count'));
            const number = Number(await results.getAttribute('data-page'));
            const rows = await results.locator('tbody tr').count();
            const ownProfile = role === 'donor' && route === '/donantes/donor';
            assert.ok(total >= (ownProfile ? 1 : 30), user + ' ' + route + ' total=' + total);
            if (ownProfile) assert.equal(total, 1, 'Donor sees only their own file');
            assert.equal(number, route.includes('page=2') ? 2 : 1);
            assert.equal(rows, Math.min(20, total - (number - 1) * 20));
            if (role === 'operator' && route === '/donantes/donor') {
              assert.ok((await results.innerText()).includes('RH26-D-H' + institution));
            }
            assert.ok(!/demo/i.test(await results.innerText()), user + ' ' + route + ' has an old label');
            report.pages.push({user, route, status: 200, total, page: number, rows});
            if (institution === 1 && role === 'operator' && ['/donantes/donor', '/campanas'].includes(route)) {
              const name = route === '/campanas' ? 'campanas.png' : 'donantes.png';
              await page.screenshot({path: path.join(output, name)});
            }
          }
        } finally {
          const csrf = page.locator('input[name=csrf_token]').first();
          if (await csrf.count()) {
            const response = await context.request.post(base + '/logout', {
              form: {csrf_token: await csrf.inputValue()},
              headers: {Referer: page.url()}, maxRedirects: 0
            });
            assert.equal(response.status(), 302, 'Logout ' + user);
          }
          await context.close();
        }
      }
    }
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.localRequests, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed';
    report.failure = error.message;
    throw error;
  } finally {
    await browser.close();
    report.completedAt = new Date().toISOString();
    fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(report, null, 2) + '\n');
  }
  console.log(JSON.stringify({result: report.result, pages: report.pages.length, errors: report.errors.length}));
})().catch(error => {console.error(error.message); process.exitCode = 1;});
