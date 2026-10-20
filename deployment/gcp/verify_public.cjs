'use strict';
// Navegador cliente de GCP: no inicia servidores ni bases en el equipo local.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const base = process.env.REDHOUSE_ORIGIN || 'https://34.18.186.116';
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const output = 'documentation/evidencias/gcp/public/browser';
fs.mkdirSync(output, {recursive: true});
const swaggerOnly = process.argv.includes('--swagger-only');
const report = swaggerOnly
  ? JSON.parse(fs.readFileSync(path.join(output, 'results.json')))
  : {date: new Date().toISOString(), origin: base, pages: [], checks: [], errors: [], localRequests: []};
if (swaggerOnly) {
  assert.equal(report.origin, base);
  assert.equal(report.pages.length, 20, 'Complete the browser pages before resuming Swagger');
  assert.ok(report.checks.some(check => check.responsiveWidth === 390));
}

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  try {
    async function login(user, width = 1440) {
      const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
      const page = await context.newPage();
      page.on('pageerror', error => report.errors.push(error.message));
      page.on('request', request => {
        const url = new URL(request.url());
        if (['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) report.localRequests.push(url.pathname);
      });
      const response = await page.goto(base + '/login');
      assert.equal(response.status(), 200);
      const tls = await response.securityDetails();
      assert.ok(tls.protocol.startsWith('TLS'));
      await page.locator('#login_email').fill(user);
      await page.locator('#password').fill(state.password);
      await Promise.all([page.waitForURL('**/panel'), page.locator('button[type=submit]').click()]);
      const cookies = await context.cookies();
      for (const name of ['red_house_access', 'red_house_csrf']) {
        const cookie = cookies.find(item => item.name === name);
        assert.ok(cookie?.secure && cookie.httpOnly && cookie.sameSite === 'Lax', name);
      }
      return {context, page, cookies};
    }

    if (!swaggerOnly) {
    const routes = {
      admin1: ['/panel', '/administracion/users', '/catalogos/sites'],
      operator1: ['/panel', '/inventario', '/donaciones'],
      medical2: ['/panel', '/solicitudes', '/donantes/recipient'],
      coordinator1: ['/panel', '/disponibilidad', '/traslados', '/rutas'],
      transport1: ['/panel', '/traslados'],
      auditor1: ['/panel', '/auditoria'],
      donor1: ['/panel', '/campanas', '/citas']
    };
    for (const [user, paths] of Object.entries(routes)) {
      const {context, page, cookies} = await login(user);
      for (const route of paths) {
        const response = await page.goto(base + route, {waitUntil: 'networkidle'});
        assert.equal(response.status(), 200, user + ' ' + route);
        report.pages.push({user, route, status: 200});
        if (route === '/panel') {
          const charts = await page.evaluate(() => [...document.querySelectorAll('[data-chart-values]')].map(node => {
            const expected = JSON.parse(node.dataset.chartValues).map(item => item.value);
            const chart = window.Highcharts.charts[Number(node.dataset.highchartsChart)];
            return {expected, actual: chart?.series[0].data.map(item => item.y) || [], hidden: node.hidden};
          }));
          for (const chart of charts) {
            assert.deepEqual(chart.actual, chart.expected);
            assert.equal(chart.hidden, chart.expected.length === 0);
          }
          report.checks.push({user, chartsMatchServer: true, chartCount: charts.length});
        }
      }
      if (user === 'operator1') {
        await page.screenshot({path: path.join(output, 'portal-https.png')});
        const token = await page.locator('input[name=csrf_token]').first().inputValue();
        const renewed = await context.request.post(base + '/sesion/continuar', {
          form: {csrf_token: token}, headers: {Referer: page.url()}
        });
        assert.equal(renewed.status(), 200);
        const logout = await context.request.post(base + '/logout', {
          form: {csrf_token: token}, headers: {Referer: page.url()}, maxRedirects: 0
        });
        assert.equal(logout.status(), 302);
        const replay = await browser.newContext();
        await replay.addCookies(cookies);
        const denied = await replay.request.get(base + '/panel', {maxRedirects: 0});
        assert.equal(denied.status(), 302);
        assert.ok(denied.headers().location.includes('/login'));
        await replay.close();
        report.checks.push({secureCookies: true, renew: 200, logout: 302, closedCookieRejected: true});
      }
      await context.close();
    }
    const mobile = await login('operator1', 390);
    await mobile.page.goto(base + '/inventario', {waitUntil: 'networkidle'});
    assert.ok(await mobile.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await mobile.page.screenshot({path: path.join(output, 'inventory-mobile.png')});
    await mobile.context.close();
    report.checks.push({responsiveWidth: 390, horizontalOverflow: false});
    }

    const context = await browser.newContext();
    const page = await context.newPage();
    page.on('pageerror', error => report.errors.push(error.message));
    const auth = await context.request.post(base + '/services/identidad-acceso/api/v1/auth/login', {
      data: {username: 'operator1', password: state.password}
    });
    assert.equal(auth.status(), 200, 'API login');
    const access = (await auth.json()).data.access_token;
    const docs = base + '/services/inventario/docs/';
    assert.equal((await page.goto(docs)).status(), 200);
    // La UI aparece antes de terminar de cargar el contrato por HTTPS.
    // Autorizar únicamente cuando ya existe el esquema de seguridad.
    await page.waitForFunction(() => Boolean(window.ui?.getSystem().specSelectors.specJson().getIn(['components', 'securitySchemes', 'BearerJWT'])));
    await page.evaluate(value => window.ui.preauthorizeApiKey('BearerJWT', value), access);
    const operation = page.locator('.opblock-get').filter({has: page.locator('.opblock-summary-path').getByText('/api/v1/resources', {exact: true})});
    await operation.locator('.opblock-summary').click();
    await operation.getByRole('button', {name: 'Try it out', exact: true}).click();
    const result = page.waitForResponse(response => new URL(response.url()).pathname === '/services/inventario/api/v1/resources');
    await operation.getByRole('button', {name: 'Execute', exact: true}).click();
    const executed = await result;
    assert.ok((await executed.request().allHeaders()).authorization, 'Swagger must send JWT');
    assert.equal(executed.status(), 200, 'Swagger Execute');
    report.checks.push({swagger: docs, execute: 200, prefix: '/services/inventario'});
    await context.close();
    assert.deepEqual(report.errors, []);
    assert.deepEqual(report.localRequests, []);
    report.status = 'passed';
    delete report.failure;
    report.completedAt = new Date().toISOString();
  } catch (error) {
    report.status = 'failed';
    report.failure = error.message;
    throw error;
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  }
  console.log(JSON.stringify({status: report.status, pages: report.pages.length, checks: report.checks.length, errors: report.errors.length}));
})().catch(error => {console.error(error.message); process.exitCode = 1;});
