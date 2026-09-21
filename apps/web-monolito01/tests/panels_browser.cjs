const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const base=process.env.BASE_URL,output=process.env.BROWSER_ARTIFACTS;
 fs.mkdirSync(output,{recursive:true});
 const errors=[],posts=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(r.method()==='POST')posts.push(r.url());});
 async function login(role){
   await page.goto(base+'/login');
   await page.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');
   await page.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);
   await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Iniciar sesión'}).click()]);
 }
 async function screenshot(name){await page.screenshot({path:path.join(output,name+'.png'),fullPage:!(await page.locator('dialog[open]').count())});}
 async function open(){
   const form=page.locator('form[data-confirm-edit]');
   await form.locator('dialog').waitFor({state:'attached'});
   await form.locator('button[type=submit]').click();
   const dialog=form.locator('dialog[open]');
   await dialog.waitFor(); return dialog;
 }
 async function confirm(dialog){
   await dialog.locator('[name=audit_reason]').fill('Cambio de prueba autorizado');
   await Promise.all([page.waitForNavigation(),dialog.locator('[data-confirm-accept]').click()]);
 }
 try{
   await login('admin');
   for(const [entity,field] of [['institutions','institution_name'],['sites','site_name'],['locations','location_description'],['components','component_name'],['users','party_name']]){
     await page.goto(base+`/administracion/${entity}`+(entity==='users'?'?q=Operador':''));
     await page.locator('main a[href$="/editar"]').first().click();
     const form=page.locator('form[data-confirm-edit]');
     await form.locator('dialog').waitFor({state:'attached'});
     assert.equal(await page.locator('.form-aside').count(),0);
     assert(!(await form.locator('[name=audit_reason]').isVisible()));
     const before=posts.length;
     await form.locator('button[type=submit]').click();
     assert.equal(await form.locator('dialog[open]').count(),0);
     assert(await form.getByRole('status').innerText()==='No hay cambios para guardar.');
     const input=form.locator(`[name=${field}]`),old=await input.inputValue();
     await input.fill(old+' actualizado');
     let dialog=await open();
     assert((await dialog.locator('.change-summary').innerText()).includes(entity==='users'?'contenido reservado':'→'));
     await dialog.locator('[data-confirm-accept]').click();
     assert.equal(posts.length,before);
     assert(await dialog.isVisible());
     await dialog.locator('[name=audit_reason]').fill('   ');
     await dialog.locator('[data-confirm-accept]').click();
     assert.equal(posts.length,before);
     await page.keyboard.press('Escape');
     assert.equal(await form.locator('dialog[open]').count(),0);
     assert.equal(await input.inputValue(),old+' actualizado');
     assert(await form.locator('button[type=submit]').evaluate(el=>el===document.activeElement));
     if(entity==='users'){
       const secret='Not-a-real-password-293!';
       await form.locator('[name=password]').fill(secret);
       dialog=await open();
       assert(!(await dialog.innerText()).includes(secret));
       assert((await dialog.innerText()).includes('valor oculto'));
       assert((await dialog.innerText()).includes('revocarán las sesiones'));
       await dialog.locator('[data-confirm-cancel]').click();
       await form.locator('[name=password]').fill('');
     }
     if(entity==='components'){
       await form.locator('[name=is_active]').uncheck();
       dialog=await open();
       assert((await dialog.locator('.confirmation-warning').innerText()).includes('historial se conserva'));
       await dialog.locator('[data-confirm-cancel]').click();
       await form.locator('[name=is_active]').check();
     }
     dialog=await open();
     if(entity==='institutions')await screenshot('Institucion_confirmacion');
     await confirm(dialog);
     assert.equal(posts.length,before+1);
     assert((await page.locator('main').innerText()).includes(old+' actualizado'));
   }
   await page.goto(base+'/administracion/configuracion/parametros');
   await page.setViewportSize({width:390,height:844});
   await page.locator('[name=hours]').fill('48');
   let dialog=await open();
   assert((await dialog.locator('.change-summary').innerText()).includes('72 → 48'));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
   await screenshot('Parametro_confirmacion_mobile');
   await confirm(dialog);
   assert.equal(await page.locator('[name=hours]').inputValue(),'48');
   await page.setViewportSize({width:1440,height:1000});
   // Contexto separado para no reutilizar la sesión administrativa.
   await page.context().clearCookies(); await login('coordinador');
   await page.goto(base+'/sangre/rutas');
   await page.locator('main a[href$="/editar"]').first().click();
   assert.equal(await page.locator('.unified-record').count(),1);
   assert.equal(await page.locator('.unified-record .card').count(),0);
   assert.equal(await page.getByText('Distancia (km)',{exact:true}).count(),0); // Etiqueta lleva asterisco, no detalle duplicado.
   await page.locator('[name=distance_km]').fill('42');
   dialog=await open();
   assert((await dialog.locator('.change-summary').innerText()).includes('30 → 42'));
   await screenshot('Ruta_confirmacion');
   await confirm(dialog);
   assert.equal(await page.locator('[name=distance_km]').inputValue(),'42');
   await screenshot('Ruta_unificada');
   assert.deepEqual(errors,[]);
   console.log(JSON.stringify({result:'PASS',panels:7,checks:['no-change','required-reason','cancel','escape-focus','password-redaction','revocation-warning','inactivation-warning','single-post','mobile','saved-values'],javascriptErrors:errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
