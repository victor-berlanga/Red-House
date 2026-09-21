const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const base=process.env.BASE_URL,data=JSON.parse(process.env.DETAIL_DATA),out=process.env.BROWSER_ARTIFACTS;
 fs.mkdirSync(out,{recursive:true});const errors=[];
 async function login(role){const context=await browser.newContext({viewport:{width:1440,height:1000}});const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(base+'/login');await p.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');await p.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);await p.getByRole('button',{name:'Iniciar sesión'}).click();await p.waitForURL(u=>u.pathname!='/login');return p;}
 try{
  const p=await login('operador');await p.goto(base+'/inventario');
  const eye=p.locator('[data-record-view]').first(); const url=p.url();
  await eye.click();const dialog=p.locator('#record-dialog');await dialog.locator('[data-detail-content]').waitFor();
  assert.equal(p.url(),url);assert.equal(await dialog.locator('form,input,select,textarea').count(),0);
  assert((await dialog.innerText()).includes('Historial de movimientos'));
  await p.screenshot({path:path.join(out,'Detalle_inventario.png')});
  await p.keyboard.press('Escape');assert(await eye.evaluate(e=>e===document.activeElement));
  await p.locator('.row-actions a[aria-label^="Editar"]').first().click();await p.waitForURL(/\/editar$/);
  assert(await p.getByRole('button',{name:'Guardar cambios',exact:true}).isVisible());
  await p.goto(base+'/inventario');await p.locator('input[name=q]').fill('UNIT-01');
  await p.waitForURL(u=>u.searchParams.get('q')==='UNIT-01');await p.waitForFunction(()=>!document.querySelector('[data-filter-results]').hasAttribute('inert'));
  await p.locator('[data-record-view]').first().click();await dialog.locator('[data-detail-content]').waitFor();assert.equal(new URL(p.url()).searchParams.get('q'),'UNIT-01');
  await dialog.getByRole('button',{name:'Cerrar detalle'}).click();
  await p.goto(base+'/sangre/personas/donor');await p.locator('[data-record-view]').first().click();await dialog.locator('[data-detail-content]').waitFor();
  assert((await dialog.innerText()).includes('SECRETO-CLINICO-ANTECEDENTES'));assert.equal(await dialog.locator('form').count(),0);
  await p.setViewportSize({width:390,height:844});await p.waitForFunction(()=>document.getElementById('sidebar').getBoundingClientRect().right<=1);await p.screenshot({path:path.join(out,'Detalle_movil.png')});
  assert(await dialog.evaluate(e=>e.getBoundingClientRect().width<=innerWidth));
  await p.keyboard.press('Tab');assert(await p.evaluate(()=>document.getElementById('record-dialog').contains(document.activeElement)));
  await p.keyboard.press('Escape');
  const audit=await login('auditor');await audit.goto(base+'/inventario');assert.equal(await audit.locator('.row-actions a[aria-label^="Editar"]').count(),0);
  const response=await audit.goto(base+'/inventario/'+data.resource+'/editar');assert.equal(response.status(),403);
  assert.equal(await audit.locator('#record-dialog[open]').count(),0);
  assert.equal(await audit.getByRole('heading',{name:'No tienes los permisos requeridos',exact:true}).count(),1);
  await audit.screenshot({path:path.join(out,'Acceso_denegado.png'),fullPage:true});
  await audit.getByRole('link',{name:'Volver al panel'}).click();await audit.waitForURL(/\/panel$/);
  await audit.goto(base+'/auditoria');await audit.locator('[data-record-view]').first().click();await audit.locator('#record-dialog [data-detail-content]').waitFor();assert((await audit.locator('#record-dialog').innerText()).includes('Correlación'));
  await audit.keyboard.press('Escape');await audit.goto(base+'/sangre/panel-regional');await audit.locator('[data-row-preview]').first().click();assert.equal(await audit.locator('#record-dialog-title').innerText(),'Disponibilidad por ABO/Rh');assert.equal(await audit.locator('#record-dialog form').count(),0);await audit.keyboard.press('Escape');
  const admin=await login('admin');for(const entity of ['institutions','users','sites','locations','components']){await admin.goto(base+'/administracion/'+entity);const current=admin.url();await admin.locator('[data-record-view]').first().click();await admin.locator('#record-dialog [data-detail-content]').waitFor();assert.equal(admin.url(),current);assert.equal(await admin.locator('#record-dialog form').count(),0);await admin.keyboard.press('Escape');}
  // Recuperación de red sin abandonar el listado y nueva autorización al reintentar.
  await p.setViewportSize({width:1440,height:1000});await p.goto(base+'/inventario');
  await p.route('**/inventario/*',route=>route.abort());await p.locator('[data-record-view]').first().click();await dialog.getByRole('button',{name:'Reintentar'}).waitFor();await p.unroute('**/inventario/*');await dialog.getByRole('button',{name:'Reintentar'}).click();await dialog.locator('[data-detail-content]').waitFor();await p.keyboard.press('Escape');
  await p.context().clearCookies();await p.locator('[data-record-view]').first().click();await dialog.getByRole('link',{name:'Iniciar sesión'}).waitFor();assert.equal(new URL(p.url()).pathname,'/inventario');
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'Details_browser.json'),JSON.stringify({result:'PASS',modal:true,fullDetail:true,editNavigation:true,permissions:true,filters:true,mobile:true,focus:true,networkRetry:true,expiredSession:true,errors},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
