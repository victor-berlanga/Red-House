/* UI real: Jinja parcial, navegación, consulta, permisos visibles y móvil.
 * NODE_PATH=/ruta/node_modules node tests/integrated_ui_browser.cjs --state /privado/state.json --output /tmp/evidencia
 * Solo lectura; nunca imprime credenciales ni tokens. */
'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const {chromium}=require('playwright');
const args=process.argv.slice(2);
function option(name){const i=args.indexOf(name);if(i<0||!args[i+1])throw Error('Falta '+name);return args[i+1];}
const state=JSON.parse(fs.readFileSync(option('--state'),'utf8')), output=option('--output');
fs.mkdirSync(output,{recursive:true});
const report={checks:[],pages:[],errors:[],captures:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  async function login(user,width=1440){
   const ctx=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'}), page=await ctx.newPage();
   page.setDefaultTimeout(25000);
   page.on('pageerror',e=>report.errors.push(e.message));
   page.on('response',r=>{if(r.url().includes('/static/')&&r.status()>=400)report.errors.push('Static '+new URL(r.url()).pathname);});
   await page.goto(state.web_url+'/login');
   await page.locator('#login_email').fill(user);await page.locator('#password').fill(state.password);
   await Promise.all([page.waitForURL('**/panel'),page.locator('button[type=submit]').click()]);
   return {ctx,page};
  }
  async function inspect(page,user,route,capture){
   const response=await page.goto(state.web_url+route,{waitUntil:'networkidle'});
   assert.equal(response.status(),200,user+' '+route);
   const metrics=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
   assert.ok(metrics.scroll<=metrics.width+1,'Desbordamiento '+route+' '+JSON.stringify(metrics));
   report.pages.push({user,route,...metrics});
   if(capture){await page.screenshot({path:path.join(output,capture)});report.captures.push(capture);}
  }
  const op=await login('operator1'), page=op.page;
  await page.clock.install();
  await inspect(page,'operator1','/inventario','inventory-desktop.png');
  await page.evaluate(()=>{window.uiCheck='preserved';});
  let mainNavigations=0;
  page.on('request',request=>{if(request.isNavigationRequest() && request.frame()===page.mainFrame())mainNavigations++;});
  const folio=(await page.locator('tbody td').first().innerText()).trim();
  const response=page.waitForResponse(r=>r.request().headers()['x-filter-fragment']==='1');
  await page.locator('#filter-q').fill(folio);assert.equal((await response).status(),200);
  await page.waitForFunction(()=>document.querySelector('[data-filter-results]').dataset.resultCount==='1');
  assert.equal(await page.evaluate(()=>window.uiCheck),'preserved');assert.equal(mainNavigations,0);
  assert.equal(await page.locator('#filter-q').evaluate(e=>e===document.activeElement),true);
  const target=new URL(page.url()).pathname+new URL(page.url()).search;
  assert.equal(new URL(await page.locator('[data-list-return]').getAttribute('href'),state.web_url).searchParams.get('return_to'),target);
  report.checks.push('Filtro parcial sin navegación, conserva foco y actualiza regreso del alta');
  await page.locator('[data-record-view]').first().click();
  await page.locator('[data-detail-content]').waitFor();
  assert.equal(await page.locator('#record-dialog-body form, #record-dialog-body .record-toolbar').count(),0);
  await page.screenshot({path:path.join(output,'record-detail.png')});report.captures.push('record-detail.png');
  await page.keyboard.press('Escape');assert.equal(await page.locator('[data-record-view]').first().evaluate(e=>e===document.activeElement),true);
  assert.equal(new URL(page.url()).searchParams.get('q'),folio);report.checks.push('Ojo solo consulta; Escape devuelve foco y mantiene filtros');
  const edit=page.locator('a[title="Editar"]').first();
  await edit.click();await page.waitForURL('**/editar?**');
  assert.equal(await page.locator('input[name=return_to]').inputValue(),target);
  await page.getByRole('link',{name:'Cancelar',exact:true}).click();await page.waitForURL(state.web_url+target);
  report.checks.push('Lápiz abre edición; cancelar regresa al filtro');
  // Red fallida: no sustituir la tabla por un error ni abandonar el foco.
  const old=await page.locator('[data-filter-results]').innerText();
  const failedRoute=async route=>route.request().headers()['x-filter-fragment']==='1'?route.fulfill({status:503,contentType:'text/html',body:'Temporalmente inaccesible'}):route.continue();
  await page.route('**/inventario?**',failedRoute);
  await page.locator('#filter-q').fill('SIN-COINCIDENCIA-UX');
  await page.getByRole('button',{name:'Reintentar',exact:true}).waitFor();
  assert.equal(await page.locator('[data-filter-results]').innerText(),old);
  await page.unroute('**/inventario?**',failedRoute);
  await page.getByRole('button',{name:'Reintentar',exact:true}).click();
  await page.getByRole('heading',{name:'No hay resultados',exact:true}).waitFor();
  report.checks.push('503 conserva tabla; reintento recupera estado vacío');
  await page.goBack();await page.waitForFunction(f=>document.querySelector('#filter-q').value===f,folio);
  await page.waitForFunction(()=>document.querySelector('[data-filter-results]').dataset.resultCount==='1');
  report.checks.push('Atrás restaura filtros y resultados parciales');
  // Reloj del navegador: comprobar 30 s sin espera real ni escrituras de negocio.
  await page.locator('[data-auto-refresh]').check();
  const poll=page.waitForResponse(r=>r.request().headers()['x-filter-fragment']==='1');
  await page.clock.runFor(31000);assert.equal((await poll).status(),200);
  report.checks.push('Actualización opcional cada 30 s consulta fragmento autorizado');
  await op.ctx.close();
  const routes={
   admin1:['/panel','/administracion/institutions','/administracion/users','/administracion/components','/catalogos/sites','/catalogos/contacts','/catalogos/schedules','/catalogos/capacities','/catalogos/locations'],
   medical1:['/panel','/inventario','/organos','/solicitudes','/donantes/donor','/donantes/recipient','/donaciones'],
   coordinator1:['/panel','/inventario','/disponibilidad','/traslados','/reservas','/rutas'],
   transport1:['/panel','/traslados'],auditor1:['/panel','/auditoria'],donor1:['/panel','/campanas','/citas','/donantes/donor']
  };
  for(const [user,paths] of Object.entries(routes)){
   const {ctx,page}=await login(user);
   for(const route of paths) await inspect(page,user,route,route==='/panel'&&user==='medical1'?'medical-dashboard.png':null);
   if(user==='admin1'){
    await inspect(page,user,'/administracion/users');await page.locator('[data-record-view]').first().click();await page.locator('[data-detail-content]').waitFor();
    assert.equal(await page.locator('#record-dialog-body form').count(),0);report.checks.push('Vista de usuario separada de activar/desactivar');
   }
   await ctx.close();
  }
  const mobile=await login('operator1',390);
  for(const route of ['/inventario','/donantes/donor','/campanas','/inventario/nuevo'])await inspect(mobile.page,'operator1-mobile',route,route==='/inventario'?'inventory-mobile.png':null);
  await mobile.ctx.close();
  assert.deepEqual(report.errors,[]);report.result='passed';
 }finally{await browser.close();fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');}
 console.log(JSON.stringify({result:report.result,pages:report.pages.length,checks:report.checks,errors:report.errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
