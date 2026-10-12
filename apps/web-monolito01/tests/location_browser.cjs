/* Solo contra el entorno desechable preparado por test_product_ui.py. */
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const state=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),output=process.argv[3];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const report={checks:[],errors:[]};
 try {
  const ctx=await browser.newContext({viewport:{width:390,height:950}}),page=await ctx.newPage();
  page.on('pageerror',e=>report.errors.push(e.message));
  await ctx.addCookies([{name:state.cookie_name,value:state.cookie_value,url:state.url,httpOnly:true,sameSite:'Lax'}]);
  let writes=0;page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname===state.path)writes++;});
  await page.goto(state.url+state.path,{waitUntil:'networkidle'});
  assert.equal(await page.locator('#latitude').inputValue(),'');
  await ctx.grantPermissions(['geolocation'],{origin:state.url});await ctx.setGeolocation({latitude:25.6866,longitude:-100.3161,accuracy:20});
  await page.getByRole('button',{name:'Usar mi ubicación actual',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#latitude').value==='25.686600');
  assert.equal(await page.locator('#longitude').inputValue(),'-100.316100');assert.equal(writes,0);
  assert.equal(await page.locator('#display-timezone').isDisabled(),false);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  report.checks.push('Captura solicitada por botón, coordenadas/fecha completadas y ninguna escritura automática');
  await page.screenshot({path:output+'/location-mobile.png'});
  await page.evaluate(()=>{navigator.geolocation.getCurrentPosition=(_ok,fail)=>fail({code:1});});
  await page.getByRole('button',{name:'Usar mi ubicación actual',exact:true}).click();
  await page.getByText('Permiso de ubicación denegado.',{exact:false}).waitFor();
  assert.equal(await page.locator('#latitude').inputValue(),'25.686600');assert.equal(writes,0);
  report.checks.push('Denegación conserva datos, edición manual y controles disponibles');
  await Promise.all([page.waitForURL(state.url+state.path.replace('/ubicacion','')),page.locator('.record-form button[type=submit]').click()]);
  assert.equal(writes,1);report.checks.push('Guardar envía una sola operación real al traslado temporal autorizado');
  assert.deepEqual(report.errors,[]);report.result='passed';
 }finally{await browser.close();fs.writeFileSync(output+'/location-report.json',JSON.stringify(report,null,2)+'\n');}
 console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
