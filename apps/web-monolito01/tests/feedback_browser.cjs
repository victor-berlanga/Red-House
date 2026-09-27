const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const p=await context.newPage(),errors=[];
 p.on('pageerror',e=>errors.push(e.message));
 const base=process.env.BASE_URL,out=process.env.BROWSER_ARTIFACTS;
 fs.mkdirSync(out,{recursive:true});
 try{
  await p.goto(base+'/login');await p.getByLabel('Correo electrónico',{exact:true}).fill('medico@red-house.test');await p.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);await p.getByRole('button',{name:'Iniciar sesión'}).click();await p.waitForURL('**/sangre/panel-regional');
  await p.clock.install();
  await p.goto(base+'/sangre/personas/donor');
  const second=await context.newPage();await second.goto(base+'/sangre/personas/donor');
  await p.getByRole('link',{name:'Nuevo registro',exact:true}).click();
  await p.locator('[name=display_name]').fill('Borrador conservado');
  await p.locator('[name=record_code]').fill('AB');
  assert.equal(await p.locator('[name=record_code]').evaluate(e=>e.checkValidity()),false);
  await p.locator('[name=record_code]').fill('DON-123456');
  assert.equal(await p.locator('[name=record_code]').evaluate(e=>e.checkValidity()),true);
  await p.waitForTimeout(300);
  await p.clock.fastForward(35000);
  await p.locator('#session-dialog[open]').waitFor();
  const warning=await p.locator('[data-session-message]').innerText();
  assert(warning.includes('Tu sesión está por finalizar'));
  await p.clock.fastForward(2000);
  assert.equal(await p.locator('[data-session-message]').innerText(),warning);
  await p.screenshot({path:path.join(out,'Sesion_aviso_mobile.png')});
  const cookiesBefore=await context.cookies();const old=cookiesBefore.find(c=>c.name==='red_house_access').value;
  await p.getByRole('button',{name:'Continuar sesión',exact:true}).click();
  await p.waitForFunction(()=>!document.getElementById('session-dialog').open);
  const updated=(await context.cookies()).find(c=>c.name==='red_house_access').value;
  assert.notEqual(updated,old);
  assert.equal(await p.locator('[name=display_name]').inputValue(),'Borrador conservado');
  const state=await second.evaluate(async()=>{const r=await fetch('/sesion/estado');return {status:r.status,data:await r.json()};});
  assert.equal(state.status,200);
  assert(state.data.expires_at-state.data.server_time>300);
  await p.screenshot({path:path.join(out,'Donante_alta_mobile.png'),fullPage:true});
  // Aviso de salida conserva la captura si se cancela.
  const nextDialog=p.waitForEvent('dialog');
  const navigation=p.goto(base+'/sangre/donaciones').catch(()=>{});
  const dialog=await nextDialog;assert.equal(dialog.type(),'beforeunload');await dialog.dismiss();await navigation;
  assert.equal(await p.locator('[name=display_name]').inputValue(),'Borrador conservado');
  // Una sesión ya inválida redirige sin modal ni aviso de borrador.
  let expiryDialogs=0;
  p.on('dialog',async dialog=>{expiryDialogs++;await dialog.dismiss();});
  await context.clearCookies();
  await p.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
  await p.waitForURL('**/login');
  assert.equal(expiryDialogs,0);
  assert.equal(await p.locator('#session-dialog').count(),0);
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'Session_browser.json'),JSON.stringify({result:'PASS',fixedWarning:true,automaticExit:true,rotation:true,draftPreserved:true,sharedTabs:true,folioValidation:true,unsavedWarning:true,errors},null,2));
 }finally{await context.close();await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
