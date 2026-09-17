const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const base=process.env.BASE_URL,data=JSON.parse(process.env.REGIONAL_DATA),out=process.env.BROWSER_ARTIFACTS;
 fs.mkdirSync(out,{recursive:true});const errors=[];
 async function login(role){const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(base+'/login');await p.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');await p.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);await p.getByRole('button',{name:'Iniciar sesión'}).click();await p.waitForURL(u=>u.pathname!='/login');return p;}
 async function filtered(p,name,value){await p.locator(`form[data-live-filter] [name="${name}"]`).selectOption(value);await p.waitForURL(u=>u.searchParams.get(name)===value);await p.waitForFunction(()=>!document.querySelector('[data-filter-results]').hasAttribute('inert'));}
 async function shot(p,name){await p.screenshot({path:path.join(out,name+'.png'),fullPage:true,animations:'disabled'});}
 try {
  const op=await login('operador');await op.goto(base+'/sangre/personas/donor');
  const form=op.locator('form[action="/sangre/personas/donor"][method=post]');
  for(const [name,value] of Object.entries({institution_id:data.north,record_code:'!',display_name:'Captura que se conserva',blood_group:'O-',restrictions:'Sin restricciones\nSegunda línea',donation_kind:'VOLUNTARY',background:'Primera línea\nSegunda línea',consent_reference:'REF-TEST',consent_at:'2020-01-01T08:30'})){
   const e=form.locator(`[name="${name}"]`);if(await e.evaluate(n=>n.tagName)==='SELECT') await e.selectOption(value);else await e.fill(value);
  }
  let posts=0;op.on('request',req=>{if(req.method()==='POST'&&new URL(req.url()).pathname==='/sangre/personas/donor')posts++;});
  await Promise.all([op.waitForResponse(r=>r.request().method()==='POST'&&r.status()===400),form.evaluate(f=>{f.requestSubmit();f.requestSubmit();})]);
  await op.locator('#form-error').waitFor();assert.equal(posts,1,'Doble envío bloqueado');
  assert.equal(await form.locator('[name=display_name]').inputValue(),'Captura que se conserva');
  assert.equal(await form.locator('textarea[name=background]').inputValue(),'Primera línea\nSegunda línea');
  assert((await form.locator('.danger-text').allTextContents()).some(t=>t.includes('folio')));
  await shot(op,'Captura_con_error_conservada');
  // Cancelar cambio de horario conserva la captura; confirmar aplica zona explícita.
  await form.locator('[name=display_name]').fill('Borrador de horario');
  await op.locator('#display-timezone').selectOption('America/Monterrey');
  op.once('dialog',d=>d.dismiss());await op.getByRole('button',{name:'Aplicar horario'}).click();
  assert.equal(await form.locator('[name=display_name]').inputValue(),'Borrador de horario');
  assert(await op.getByRole('button',{name:'Aplicar horario'}).isEnabled());
  op.once('dialog',d=>d.accept());await Promise.all([op.waitForNavigation(),op.getByRole('button',{name:'Aplicar horario'}).click()]);
  assert.equal(await op.locator('form[action="/sangre/personas/donor"] [name=_timezone]').inputValue(),'America/Monterrey');
  assert((await op.locator('main').innerText()).includes('Fecha del consentimiento (America/Monterrey)'));
  await op.goto(base+'/sangre/donaciones');
  const donationForm=op.locator('form[method=post][action="/sangre/donaciones"]');
  await donationForm.locator('[data-option-search]').fill('Persona ficticia');
  assert.equal(await donationForm.locator('select[name=donor_id] option').count(),2);
  await filtered(op,'status','PROCESSED');assert.equal(await op.locator('[data-filter-results]').getAttribute('data-result-count'),'1');
  await shot(op,'Donaciones_con_filtros');
  await op.goto(base+'/sangre/personas/donor');await op.locator('.table-link').first().click();
  assert.equal(await op.getByRole('heading',{name:'Actualizar expediente',exact:true}).count(),0);
  assert((await op.locator('main').innerText()).includes('Expediente de consulta'));
  await op.setViewportSize({width:390,height:844});await op.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth+1 && document.getElementById('sidebar').getBoundingClientRect().right<=1);await shot(op,'Expediente_consulta_mobile');
  const coord=await login('coordinador');await coord.goto(base+'/sangre/panel-regional');await coord.locator('#overview-chart .highcharts-root').waitFor();
  assert.equal(await coord.locator('.highcharts-root').count(),3);
  assert.equal(await coord.locator('[data-chart-type=line]').evaluate(e=>JSON.parse(e.dataset.chartValues).length),7);
  await shot(coord,'Panel_con_graficas');
  await coord.getByRole('link',{name:/Ver solicitudes urgentes/}).click();assert.equal(new URL(coord.url()).searchParams.get('urgency'),'URGENT');
  assert.equal(await coord.locator('[data-filter-results]').getAttribute('data-result-count'),'1');
  await filtered(coord,'urgency','ROUTINE');assert.equal(await coord.locator('[data-filter-results]').getAttribute('data-result-count'),'0');
  const admin=await login('admin');
  for(const entity of ['sites','locations']){await admin.goto(base+'/administracion/'+entity);assert.equal(await admin.locator('.sidebar-nav [aria-current=page]').getAttribute('href'),'/administracion/institutions');await filtered(admin,'state','ACTIVE');assert(await admin.locator('[data-filter-results] a').count()>0,'Acciones presentes en el fragmento');}
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'Browser_results.json'),JSON.stringify({result:'PASS',doubleSubmit:true,errorCapture:true,multiline:true,timezoneConfirmation:true,searchableOptions:true,newFilters:true,lockedDetails:true,mobile:true,charts:3,drilldown:true,adminNavigation:true,errors},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
