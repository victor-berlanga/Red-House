/* Reloj acelerado y endpoints simulados: prueba el script real sin tocar cuentas ni esperar 15 minutos. */
'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require('playwright');
const script = fs.readFileSync(path.join(__dirname, '../src/presentation/static/js/session.js'), 'utf8');
const minute = 60000, start = Date.UTC(2026, 9, 12, 12);
const html = `<!doctype html><html><head><meta charset="utf-8"></head><body><label>Borrador<input id="draft"></label>
<dialog id="session-dialog"><p data-session-message></p><button data-session-renew>Continuar sesión</button>
<form action="/logout" method="post"><input name="csrf_token" type="hidden" value="csrf-initial"><button>Salir</button></form></dialog>
<script src="/session.js"></script></body></html>`;
const report = {checks:[], errors:[]};
async function until(page, predicate) {
 const end = Date.now() + 5000;
 while (!(await page.evaluate(predicate))) {
  assert.ok(Date.now() < end, 'Estado esperado no alcanzado');
  await new Promise(resolve => setTimeout(resolve, 20));
 }
}
(async () => {
 const browser = await chromium.launch({channel:'chrome', headless:true});
 try {
  async function fixture() {
   const ctx = await browser.newContext();
   const server = {expires:start + 15 * minute, renewals:0, status:0, renewStatus:200};
   await ctx.route('http://session.test/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/session.js') return route.fulfill({contentType:'text/javascript', body:script});
    if (url.pathname.startsWith('/sesion/')) {
     const now = await route.request().frame().evaluate(() => Date.now());
     const renewing = url.pathname === '/sesion/continuar';
     if (renewing) {
      server.renewals++;
      assert.equal(route.request().method(), 'POST');
      assert.ok(route.request().headers()['x-csrftoken'].startsWith('csrf-'));
      if (server.renewStatus !== 200) return route.fulfill({status:server.renewStatus, json:{}});
      server.expires = now + 15 * minute;
     } else {
      server.status++;
      if (now >= server.expires) return route.fulfill({status:401, json:{}});
     }
     return route.fulfill({json:{expires_at:server.expires / 1000, server_time:now / 1000, csrf_token:'csrf-rotated'}});
    }
    return route.fulfill({contentType:'text/html', body:url.pathname === '/login' ? '<h1>Login</h1>' : html});
   });
   async function newPage(at = start) {
    const page = await ctx.newPage(); page.setDefaultTimeout(5000);
    page.on('pageerror', error => report.errors.push(error.message));
    await page.clock.install({time:at}); await page.clock.pauseAt(at);
    await page.goto('http://session.test/form');
    await until(page, () => document.querySelector('[name=csrf_token]').value === 'csrf-rotated');
    return page;
   }
   const page = await newPage();
   return {ctx, page, server, newPage};
  }
  async function settle(page) { await page.waitForTimeout(80); }
  async function advance(page, ms) { await page.clock.fastForward(ms); await settle(page); }
  async function closed(page) { assert.equal(await page.locator('#session-dialog').evaluate(d => d.open), false); }

  // Trabajo continuo durante más de dos periodos originales del JWT.
  {
   const {ctx, page, server} = await fixture();
   await page.locator('#draft').fill('Borrador conservado');
   for (let i = 0; i < 12; i++) {
    await advance(page, 3 * minute);
    if (i % 3 === 0) await page.locator('#draft').press('ArrowLeft');
    else if (i % 3 === 1) await page.mouse.move(50 + i, 100);
    else await page.mouse.wheel(0, 20);
    await settle(page); await closed(page);
   }
   assert.ok(server.renewals >= 3); assert.ok(server.renewals <= 4);
   assert.equal(await page.locator('#draft').inputValue(), 'Borrador conservado');
   assert.equal(new URL(page.url()).pathname, '/form');
   report.checks.push('36 minutos con teclado, ratón y desplazamiento: renovación automática limitada, sin aviso ni pérdida del borrador');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   for (let i = 0; i < 10; i++) {
    await page.evaluate(() => document.dispatchEvent(new Event('input', {bubbles:true})));
    await advance(page, minute);
   }
   assert.equal(server.renewals, 0); assert.ok(server.status > 1);
   assert.equal(await page.locator('#session-dialog').evaluate(d => d.open), true);
   assert.ok((await page.locator('[data-session-message]').innerText()).includes('actividad reciente'));
   await advance(page, 5 * minute); await page.waitForURL('**/login');
   report.checks.push('Inactividad: polling y eventos sintéticos no renuevan; aviso y salida al vencer');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   await page.locator('#draft').fill('Sin perder captura');
   for (let i = 0; i < 10; i++) await advance(page, minute);
   assert.equal(await page.locator('#session-dialog').evaluate(d => d.open), true, JSON.stringify(server));
   await page.getByRole('button', {name:'Continuar sesión'}).press('Enter');
   await until(page, () => !document.querySelector('#session-dialog').open);
   assert.equal(server.renewals, 1);
   assert.equal(await page.locator('#draft').inputValue(), 'Sin perder captura');
   report.checks.push('Continuación manual tras inactividad renueva una vez y conserva captura');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   server.renewStatus = 503;
   await advance(page, 8 * minute); await page.locator('#draft').press('a');
   await advance(page, 2 * minute);
   await page.getByText('No se pudo renovar la sesión automáticamente.', {exact:false}).waitFor();
   const attempts = server.renewals;
   await advance(page, 20000); assert.equal(server.renewals, attempts);
   server.renewStatus = 200;
   await page.getByRole('button', {name:'Continuar sesión'}).press('Enter');
   await until(page, () => !document.querySelector('#session-dialog').open);
   report.checks.push('503: mensaje de conexión, sin bucle de peticiones y reintento manual recupera sesión');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   server.renewStatus = 409;
   await advance(page, 8 * minute); await page.locator('#draft').press('a');
   await advance(page, 2 * minute); assert.equal(server.renewals, 1); await closed(page);
   server.expires = start + 25 * minute; server.renewStatus = 200;
   await advance(page, 1000); await advance(page, 5000); assert.equal(server.renewals, 1); await closed(page);
   report.checks.push('409 de otra renovación: consulta el nuevo vencimiento sin mostrar aviso ni duplicar renovación');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   server.renewStatus = 401;
   await advance(page, 8 * minute); await page.locator('#draft').press('a');
   await advance(page, 2 * minute); await page.waitForURL('**/login');
   assert.equal(server.renewals, 1);
   report.checks.push('401/revocación conserva salida a login aunque haya actividad');
   await ctx.close();
  }
  {
   const {ctx, page, server, newPage} = await fixture();
   const peer = await newPage();
   await advance(page, 8 * minute); // El reloj se comparte entre páginas del contexto.
   await page.locator('#draft').press('a'); await settle(peer);
   await advance(peer, 2 * minute); await closed(peer); await closed(page);
   assert.ok(server.renewals >= 1 && server.renewals <= 2);
   await page.evaluate(() => { const c = new BroadcastChannel('red-house-session'); c.postMessage('logout'); c.close(); });
   await peer.waitForURL('**/login');
   report.checks.push('Pestañas: actividad compartida evita aviso en la otra pestaña; cierre compartido sigue vigente');
   await ctx.close();
  }
  {
   const {ctx, page, server} = await fixture();
   // Simula una renovación en otra pestaña cuyo aviso se perdió durante la suspensión.
   server.expires = start + 30 * minute;
   await advance(page, 16 * minute);
   assert.equal(new URL(page.url()).pathname, '/form'); await closed(page);
   assert.equal(server.renewals, 0);
   report.checks.push('Pestaña reanudada valida el vencimiento del servidor antes de salir con un plazo local obsoleto');
   await ctx.close();
  }
  assert.deepEqual(report.errors, []); report.result = 'passed';
 } finally {
  await browser.close();
  const output = process.argv[2];
  if (output) fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
 }
 console.log(JSON.stringify(report, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
