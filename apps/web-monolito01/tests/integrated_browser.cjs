/* Recorrido real de Chrome. Lee credenciales privadas; el informe nunca las publica. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const args = process.argv.slice(2);
function option(name) { const i=args.indexOf(name); if(i<0 || !args[i+1]) throw Error('Falta '+name); return args[i+1]; }
const state = JSON.parse(fs.readFileSync(option('--state'),'utf8'));
const output = option('--output');
const base = state.web_url;
fs.mkdirSync(output,{recursive:true});
const report = {browser:'Chrome',base,checks:[],captures:[],javascriptErrors:0,staticFailures:0,errorDetails:[]};

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    async function context(user,width=1440,height=1000) {
      const ctx=await browser.newContext({viewport:{width,height},reducedMotion:'reduce'});
      const page=await ctx.newPage();
      page.on('pageerror',error=>{ report.javascriptErrors++; report.errorDetails.push({route:new URL(page.url()).pathname,message:error.message}); });
      page.on('response',r=>{ if(r.url().includes('/static/') && r.status()>=400) report.staticFailures++; });
      await page.goto(base+'/login');
      await page.locator('#login_email').fill(user);
      await page.locator('#password').fill(state.password);
      await Promise.all([page.waitForURL('**/panel'),page.locator('button[type=submit]').click()]);
      return {ctx,page};
    }
    async function inspect(page,route,capture) {
      const response=await page.goto(base+route,{waitUntil:'networkidle'});
      assert.equal(response.status(),200,route);
      assert.ok(!page.url().includes('/login'),route);
      const metrics=await page.evaluate(()=>({width:innerWidth,document:document.documentElement.scrollWidth,
        heading:document.querySelector('h1')?.textContent.trim(),rows:document.querySelectorAll('tbody tr').length,
        charts:window.Highcharts?.charts.filter(Boolean).length||0}));
      assert.ok(metrics.document<=metrics.width+1,'Desbordamiento en '+route+' '+JSON.stringify(metrics));
      report.checks.push({route,...metrics});
      if(capture) { await page.screenshot({path:path.join(output,capture),fullPage:false}); report.captures.push(capture); }
      return metrics;
    }
    const medical=await context('medical1');
    const metrics=await inspect(medical.page,'/panel','01-panel-medico.png');
    assert.ok(metrics.charts>=2,'Highcharts debe mostrar datos reales');
    await inspect(medical.page,'/inventario','02-inventario.png');
    const inventoryRows=await medical.page.locator('tbody tr').count(); assert.ok(inventoryRows>=10);
    await medical.page.locator('#filter-q').fill('SAN-');
    await Promise.all([medical.page.waitForURL('**/inventario?**'),medical.page.getByRole('button',{name:'Aplicar filtros'}).click()]);
    assert.ok(await medical.page.locator('tbody tr').count()>=10);
    await inspect(medical.page,'/disponibilidad','03-disponibilidad.png');
    await inspect(medical.page,'/organos','04-organos.png');
    await inspect(medical.page,'/solicitudes');
    await inspect(medical.page,'/donantes/donor');
    await inspect(medical.page,'/inventario/nuevo');
    const search=medical.page.locator('[data-service-option-search]').first();
    const lookup=medical.page.waitForResponse(r=>r.url().includes('/opciones/') && r.request().method()==='GET');
    await search.fill('DEMO');
    assert.equal((await lookup).status(),200,'Búsqueda HTTP del selector');
    await medical.page.locator('[data-service-option-status]').first().filter({hasText:'opciones encontradas'}).waitFor();
    report.selectorSearch='passed';
    assert.ok(await medical.page.locator('input[name=idempotency_key]').count());
    await medical.ctx.close();
    const destination=await context('medical2');
    await inspect(destination.page,'/solicitudes');
    const tokenResponse=await destination.ctx.request.post(state.urls.identidad_acceso+'/api/v1/auth/login',
      {data:{username:'medical2',password:state.password}});
    assert.equal(tokenResponse.status(),200);
    const token=(await tokenResponse.json()).data.access_token;
    const evResponse=await destination.ctx.request.get(state.urls.compatibilidad+'/api/v1/evaluations',
      {headers:{Authorization:'Bearer '+token}});
    const evaluations=(await evResponse.json()).data.items;
    assert.ok(evaluations.length);
    await inspect(destination.page,'/evaluaciones/'+evaluations[0].id,'05-compatibilidad.png');
    await inspect(destination.page,'/traslados');
    const detail=await destination.page.locator('tbody a').first().getAttribute('href');
    await inspect(destination.page,detail,'06-traslado-custodia.png');
    await destination.ctx.close();
    for(const [user,routes] of Object.entries({
      admin1:['/administracion/institutions','/administracion/users','/catalogos/sites','/catalogos/contacts','/catalogos/schedules','/catalogos/capacities','/catalogos/locations','/catalogos/sites/nuevo','/monitoreo'],
      coordinator1:['/reservas','/rutas','/traslados'],transport1:['/traslados'],
      auditor1:['/auditoria','/monitoreo'],donor1:['/campanas','/citas','/notificaciones']})) {
      const view=await context(user);
      for(const route of routes) await inspect(view.page,route,user==='admin1'&&route==='/monitoreo'?'07-monitoreo.png':null);
      if(user==='admin1') assert.equal((await view.page.goto(base+'/inventario')).status(),403);
      await view.ctx.close();
    }
    const mobile=await context('medical1',390,844);
    for(const route of ['/panel','/inventario','/inventario/nuevo','/organos']) await inspect(mobile.page,route,route==='/inventario'?'08-inventario-movil.png':null);
    await mobile.page.getByRole('button',{name:'Abrir menú',exact:true}).click();
    await mobile.page.locator('#sidebar').waitFor({state:'visible'});
    assert.equal(await mobile.page.getByRole('button',{name:'Abrir menú',exact:true}).getAttribute('aria-expanded'),'true');
    await mobile.ctx.close();
    assert.equal(report.javascriptErrors,0); assert.equal(report.staticFailures,0);
    report.result='passed';
  } finally { await browser.close(); fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n'); }
  console.log(JSON.stringify({result:report.result,pages:report.checks.length,captures:report.captures.length,javascriptErrors:report.javascriptErrors,staticFailures:report.staticFailures}));
})().catch(e=>{console.error(e.message); process.exitCode=1;});
