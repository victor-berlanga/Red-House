/* Navegación de siete perfiles, confirmaciones sin escrituras y ubicación puntual. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const args=process.argv.slice(2),option=n=>args[args.indexOf(n)+1];
const state=JSON.parse(fs.readFileSync(option('--state'),'utf8')),output=option('--output');
fs.mkdirSync(output,{recursive:true});
const report={pages:[],checks:[],errors:[],captures:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  async function login(user,width=1440,js=true){
   const ctx=await browser.newContext({viewport:{width,height:1000},javaScriptEnabled:js,reducedMotion:'reduce'}),page=await ctx.newPage();
   page.setDefaultTimeout(20000);
   page.on('pageerror',e=>report.errors.push(e.message));
   page.on('response',r=>{if(r.url().includes('/static/')&&r.status()>=400)report.errors.push(new URL(r.url()).pathname);});
   await page.goto(state.web_url+'/login');await page.locator('#login_email').fill(user);await page.locator('#password').fill(state.password);
   await Promise.all([page.waitForURL('**/panel'),page.locator('button[type=submit]').click()]);return {ctx,page};
  }
  async function inspect(page,user,route,capture){
   const response=await page.goto(state.web_url+route,{waitUntil:'networkidle'});assert.equal(response.status(),200,user+' '+route);
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Desbordamiento '+route);
   report.pages.push({user,route,width:page.viewportSize().width});
   if(capture){await page.screenshot({path:path.join(output,capture)});report.captures.push(capture);}
  }
  const routes={admin1:['/panel','/configuracion','/administracion/components','/catalogos/sites','/catalogos/contacts','/catalogos/schedules','/catalogos/capacities','/catalogos/locations','/catalogos/schedules/nuevo','/administracion/users','/administracion/institutions','/monitoreo'],operator1:['/panel','/inventario','/disponibilidad','/donantes/donor','/donantes/recipient','/donaciones','/campanas','/citas','/rutas','/traslados','/organos','/notificaciones'],medical1:['/panel','/solicitudes','/propuestas','/organos'],coordinator1:['/panel','/monitoreo','/reservas','/traslados'],transport1:['/panel','/traslados','/rutas'],auditor1:['/panel','/auditoria','/monitoreo'],donor1:['/panel','/donantes/donor','/citas','/campanas']};
  for(const [user,paths] of Object.entries(routes)){
   const {ctx,page}=await login(user);
   for(const route of paths)await inspect(page,user,route,route==='/panel'&&['donor1','auditor1'].includes(user)?user+'-panel.png':null);
   assert.equal(await page.getByRole('link',{name:'Roles y parámetros',exact:true}).count(),0);
   assert.equal(await page.locator('main .timezone-picker').count(),0);
   if(user==='admin1'){
    await inspect(page,user,'/catalogos/sites','catalogues.png');
    await inspect(page,user,'/administracion/users');
    await page.locator('[data-record-view]').first().click();await page.locator('[data-detail-content]').waitFor();
    assert.equal(await page.locator('#record-dialog-body form').count(),0);await page.keyboard.press('Escape');
    await page.locator('a[href*="/estado"]').first().click();
    assert.equal(await page.locator('input[name=version]').getAttribute('type'),'hidden');
   }
   if(user==='operator1'){
    await inspect(page,user,'/notificaciones');assert.equal(await page.locator('[data-row-preview]').count(),0);
    assert.ok(!(await page.locator('main').innerText()).includes('DONOR_REGISTERED'));
    await inspect(page,user,'/citas');
    const cancel=page.locator('[data-action-dialog]').first();assert.ok(await cancel.count(),'Inscripción activa para comprobar confirmación');
    const original=page.url();await cancel.click();await page.locator('#action-dialog [data-action-content]').waitFor();
    assert.equal(page.url(),original);assert.ok(!(await page.locator('#action-dialog').innerText()).includes('campos marcados'));
    assert.ok(await page.locator('#action-dialog .action-prompt').count());
    assert.ok((await page.locator('#action-dialog form').getAttribute('action')).includes('/cancelar'));
    await page.screenshot({path:path.join(output,'cancel-dialog.png')});report.captures.push('cancel-dialog.png');
    await page.keyboard.press('Escape');assert.equal(await cancel.evaluate(e=>e===document.activeElement),true);
    report.checks.push('Cancelar inscripción muestra campaña en diálogo y conserva listado/foco sin enviar operación');
    await page.route('**/citas/*/cancelar*',route=>route.fulfill({status:503,body:'Temporalmente inaccesible'}));
    await cancel.click();await page.getByRole('link',{name:'Abrir operación',exact:true}).waitFor();await page.keyboard.press('Escape');
    await page.unroute('**/citas/*/cancelar*');report.checks.push('Confirmación fallida ofrece acceso alternativo y permite cerrar');
    await inspect(page,user,'/inventario/nuevo');
    await page.locator('#folio').fill('BORRADOR-NO-GUARDADO');await page.locator('#expires_at').fill('2026-10-20T12:30');
    await page.locator('.timezone-menu > summary').click();
    const zone=page.locator('#display-timezone'),previous=await zone.inputValue(),next=previous==='UTC'?'America/Monterrey':'UTC';
    await zone.selectOption(next);await page.waitForFunction(z=>document.querySelector('.record-form input[name="_timezone"]').value===z,next);
    assert.equal(await page.locator('#folio').inputValue(),'BORRADOR-NO-GUARDADO');
    assert.equal(await page.locator('#expires_at').inputValue(),previous==='UTC'?'2026-10-20T06:30':'2026-10-20T18:30');
    await page.route('**/preferencias/horario',route=>route.fulfill({status:503,body:'Temporalmente inaccesible'}));
    await zone.selectOption(previous);await page.getByText('No se pudo cambiar el horario.',{exact:false}).waitFor();
    assert.equal(await zone.inputValue(),next);await page.unroute('**/preferencias/horario');
    await page.setViewportSize({width:390,height:1000});await page.waitForFunction(()=>document.querySelector('#sidebar').getBoundingClientRect().right<=1);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.screenshot({path:path.join(output,'timezone-mobile.png')});report.captures.push('timezone-mobile.png');
    report.checks.push('Horario en cabecera conserva borrador/instante, revierte ante 503 y cabe en móvil');
   }
   await ctx.close();
  }
  const mobile=await login('donor1',390);for(const route of ['/panel','/citas','/campanas'])await inspect(mobile.page,'donor1-mobile',route,route==='/citas'?'registrations-mobile.png':null);await mobile.ctx.close();
  const fallback=await login('operator1',1440,false);await inspect(fallback.page,'operator1-no-js','/citas');
  await fallback.page.locator('[data-action-dialog]').first().click();assert.ok(await fallback.page.locator('.action-prompt').count());
  await fallback.page.locator('.timezone-menu > summary').click();assert.equal(await fallback.page.getByRole('button',{name:'Aplicar horario',exact:true}).isVisible(),true);await fallback.ctx.close();
  report.checks.push('Sin JavaScript: confirmación completa y selector horario funcionan');
  assert.deepEqual(report.errors,[]);report.result='passed';
 } finally {await browser.close();fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2)+'\n');}
 console.log(JSON.stringify({result:report.result,pages:report.pages.length,checks:report.checks,errors:report.errors}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
