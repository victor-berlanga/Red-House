'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require(path.resolve(__dirname,'../.local/gcp-public/browser/node_modules/playwright'));
const input = JSON.parse(fs.readFileSync(0,'utf8'));
(async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const results = {checks:[],errors:[],cartography:'Tiles blocked during automated tests; no bulk requests to OSM',gateway:'Direct TLS test server, not production proxy'};
  try {
    for (const user of ['admin1','operator1','medical1','coordinator1','transport1','donor1','auditor1']) {
      const context = await browser.newContext({ignoreHTTPSErrors:true});
      const page = await context.newPage();
      page.on('pageerror',e=>results.errors.push(e.message));
      await context.route('https://tile.openstreetmap.org/**',r=>r.abort());
      await page.addInitScript(({target})=>{
        const Native = window.WebSocket; window.trackingConnections = 0;
        window.WebSocket = class extends Native { constructor(url,protocol){super(url.includes('/services/transporte/ws/') ? target : url, protocol); window.trackingConnections++;} };
      }, {target:input.socket});
      await page.goto(input.base+'/login');
      await page.locator('#login_email').fill(user); await page.locator('#password').fill(input.password);
      await Promise.all([page.waitForURL('**/panel'),page.locator('button[type=submit]').click()]);
      for (const width of [390,768,1440]) {
        await page.setViewportSize({width,height:900});
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth),user+' overflow '+width);
      }
      results.checks.push(user+' dashboard, three widths');
      if (user === 'transport1') {
        await page.goto(input.base+'/traslados/'+input.shipment+'/mapa');
        await page.waitForFunction(()=>document.querySelector('#tracking-status').textContent.includes('Sin señal'));
        await page.evaluate(async ({target,token,position})=>new Promise((resolve,reject)=>{
          const ws = new WebSocket(target,'redhouse.tracking.v1.json');
          const timer=setTimeout(()=>reject(new Error('publish timeout')),12000);
          ws.onopen=()=>ws.send(JSON.stringify({type:'authenticate',credential_kind:'device',credential:token}));
          ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.type==='authenticated')ws.send(JSON.stringify({type:'position.publish',position:{...position,captured_at:new Date().toISOString()}}));if(m.type==='position.ack'){clearTimeout(timer);ws.close();resolve();}if(m.type==='error')reject(new Error(m.code));};
        }),{target:input.socket,token:input.deviceToken,position:input.position});
        await page.waitForFunction(()=>document.querySelector('#tracking-source').textContent.includes('SIMULADO'));
        await page.locator('#tracking-focus').click();
        assert.ok(await page.locator('.leaflet-interactive').count() >= 1);
        const connections = await page.evaluate(()=>window.trackingConnections);
        await page.locator('#tracking-retry').click();
        await page.waitForFunction(previous=>window.trackingConnections > previous && document.querySelector('#tracking-status').textContent.includes('En vivo'), connections);
        for (const width of [390,768,1440]) {
          await page.setViewportSize({width,height:900});
          assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
          await page.screenshot({path:path.join(input.output,'map-'+width+'.png'),fullPage:true});
        }
        assert.ok((await page.locator('#tracking-tiles').innerText()).includes('no disponible'));
        results.checks.push('WSS simulator to marker; reconnect; tile failure; map three widths');
        assert.equal((await page.goto(input.base+'/traslados')).status(),200);
        assert.ok(await page.locator('a[href*="/traslados/'+input.shipment+'"]').count());
        assert.equal((await page.request.get(input.base+'/traslados/'+input.shipment)).status(),200);
        results.checks.push('Cartografía caída: listado y detalle privado del traslado persistido siguen disponibles');
      }
      if (user === 'donor1') assert.equal((await page.goto(input.base+'/traslados/'+input.shipment+'/mapa')).status(),403);
      await context.close();
    }
    assert.deepEqual(results.errors,[]); results.passed=true;
  } catch(e) {results.failure=e.message;process.exitCode=1;} finally {
    fs.writeFileSync(path.join(input.output,'browser.json'),JSON.stringify(results,null,2)); await browser.close();
  }
})();
