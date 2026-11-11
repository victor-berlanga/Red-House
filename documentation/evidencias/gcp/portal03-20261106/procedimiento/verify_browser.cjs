'use strict';
// Cliente real del despliegue; datos ficticios propios, sin cortar dependencias.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require(path.resolve('.local/gcp-public/browser/node_modules/playwright'));
const input=JSON.parse(fs.readFileSync(0,'utf8'));
assert.equal(input.base,'https://34.18.186.116');
const output=input.output;fs.mkdirSync(output,{recursive:true});const resumed=Boolean(input.resumeCampaignTitle);
const report={startedAt:new Date().toISOString(),passed:false,checks:[],pages:[],records:{},consoleErrors:[],negative:[],wss:[],limits:['Prueba dirigida del despliegue, no repetición de los 90 casos locales','Sin ensayo de caída total, GCS/antivirus o GPS físico']};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function otp(secret){let bits='';for(const c of secret.replace(/=/g,''))bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5,'0');const bytes=[];for(let i=0;i+8<=bits.length;i+=8)bytes.push(parseInt(bits.slice(i,i+8),2));const count=Buffer.alloc(8);count.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const h=crypto.createHmac('sha1',Buffer.from(bytes)).update(count).digest();return ((h.readUInt32BE(h[19]&15)&0x7fffffff)%1000000).toString().padStart(6,'0');}
const factor={admin1:input.accounts.admin.secret,medical1:input.accounts.origin.secret,coordinator1:input.accounts.coordinator.secret};
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const contexts=[];try{
 const probe=await browser.newContext();contexts.push(probe);report.publicHttp=[];
 const readyUntil=Date.now()+240000;while(true){const r=await probe.request.get(input.base+'/login');if(r.status()===200)break;assert.ok(Date.now()<readyUntil,'Portal no terminó de arrancar');await pause(3000);}
 if(!resumed)for(const service of ['identidad-acceso','donantes','receptores','inventario','compatibilidad','priorizacion-geografia','transporte','custodia','alertas','auditoria','monitoreo','documentos']){
  for(const endpoint of ['/health/live','/health/ready','/internal/v1/institutions']){
   const url='/services/'+service+endpoint;const r=await probe.request.get(input.base+url);assert.equal(r.status(),endpoint.startsWith('/internal/')?404:200,url);report.publicHttp.push({path:url,status:r.status()});
  }
 }
 if(!resumed){const anonymous=await probe.request.get(input.base+'/services/inventario/api/v1/resources');assert.equal(anonymous.status(),401);report.publicHttp.push({path:'/services/inventario/api/v1/resources',status:401});}
 async function login(user){const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});contexts.push(context);const page=await context.newPage();page.setDefaultTimeout(45000);page.on('pageerror',e=>report.consoleErrors.push(e.message));
  const response=await page.goto(input.base+'/login');assert.equal(response.status(),200);assert.ok((await response.securityDetails()).protocol.startsWith('TLS'));
  await page.locator('#login_email').fill(user);await page.locator('#password').fill(input.password);if(factor[user]){if(Date.now()%30000>26000)await pause(31000-Date.now()%30000);await page.locator('#otp').fill(otp(factor[user]));}
  await Promise.all([page.waitForURL('**/panel'),page.locator('main form button[type=submit]').click()]);assert.ok((await context.cookies()).every(c=>c.secure));return{context,page};}
 async function goto(page,url,user){const response=await page.goto(input.base+url);assert.equal(response.status(),200,user+' '+url);report.pages.push({user,path:url,status:response.status()});return response;}
 async function submit(page,destination){await Promise.all([page.waitForURL(destination),page.locator('main form button[type=submit]').click()]);}
 const sessions={};
 const routes={admin1:['/configuracion','/configuracion/politica','/administracion/dispositivos','/documentos'],operator1:['/campanas','/citas','/laboratorio/muestras','/inventario'],medical1:['/solicitudes','/laboratorio','/documentos','/reportes'],coordinator1:['/traslados','/disponibilidad'],transport1:['/traslados'],auditor1:['/auditoria','/hallazgos','/reportes'],donor1:['/campanas','/citas','/donantes/donor']};
 for(const[user,paths]of Object.entries(routes)){if(resumed&&!['admin1','operator1','coordinator1','transport1','donor1'].includes(user))continue;const s=await login(user);sessions[user]=s;if(resumed)continue;
  await s.page.waitForFunction(()=>window.Highcharts?.charts?.filter(Boolean).length>0||document.querySelectorAll('[data-chart-values]').length===0);
  const charts=await s.page.evaluate(()=>[...document.querySelectorAll('[data-chart-values]')].map(n=>({expected:JSON.parse(n.dataset.chartValues).map(x=>x.value),actual:window.Highcharts?.charts[Number(n.dataset.highchartsChart)]?.series[0].data.map(x=>x.y)||[]})));
  for(const c of charts)assert.deepEqual(c.actual,c.expected);report.checks.push({profile:user,login:true,mfa:Boolean(factor[user]),chartsCompared:charts.length});
  for(const url of paths)await goto(s.page,url,user);
 }
 const op=sessions.operator1.page;
 const title=input.resumeCampaignTitle||'Comprobación ficticia GCP portal03 '+crypto.randomUUID().slice(0,8);report.records.title=title;
 if(!resumed){await goto(op,'/campanas/nueva','operator1');await op.locator('[name=title]').fill(title);await op.locator('[name=capacity]').fill('1');await submit(op,/\/campanas$/);}
 const apiLogin=await probe.request.post(input.base+'/services/identidad-acceso/api/v1/auth/login',{data:{username:'operator1',password:input.password}});assert.equal(apiLogin.status(),200);const apiToken=(await apiLogin.json()).data.access_token;
 const lookup=await probe.request.get(input.base+'/services/donantes/api/v1/campaigns?q='+encodeURIComponent(title),{headers:{Authorization:'Bearer '+apiToken}});assert.equal(lookup.status(),200);const matches=(await lookup.json()).data.items.filter(c=>c.title===title);assert.equal(matches.length,1);const id=matches[0].id;const detail='/campanas/'+id;report.records.campaign=id;report.resumedCampaign=resumed;await goto(op,detail,'operator1');assert.ok((await op.locator('main').innerText()).includes(title));
 if(!input.publicationAlreadyCreated){ await goto(op,detail+'/publicacion','operator1');await op.locator('[name=published]').uncheck();await op.locator('[name=venue]').fill('Sede sintética, no convocatoria pública');await op.locator('[name=information]').fill('Prueba de despliegue; no es campaña para personas.');await op.locator('[name=human_confirmation]').check();await op.locator('[name=reason]').fill('Verificar persistencia del portal actualizado');await submit(op,new RegExp('/campanas/'+id+'$'));await op.reload();
}
 await goto(op,detail+'/publicacion','operator1');assert.equal(await op.locator('[name=version]').inputValue(),'1');assert.equal(await op.locator('[name=published]').isChecked(),false);assert.match(await op.locator('[name=venue]').inputValue(),/Sede sintética/);report.checks.push({campaignPublicationPersisted:true,published:false});

 for(const format of ['json','xml']){const r=await probe.request.get(input.base+'/services/donantes/api/v1/campaigns/'+id,{headers:{Authorization:'Bearer '+apiToken,Accept:'application/'+format}});assert.equal(r.status(),200);assert.ok(r.headers()['content-type'].includes(format));if(format==='json')assert.equal((await r.json()).data.id,id);else{const text=await r.text();assert.ok(await op.evaluate(({text,id})=>{const d=new DOMParser().parseFromString(text,'application/xml');return !d.querySelector('parsererror')&&d.querySelector('response > field[name="data"] > field[name="id"]')?.textContent===id;},{text,id}));}report.checks.push({publicApiRead:format,sameBrowserCampaign:true});}
 const apiLogout=await probe.request.post(input.base+'/services/identidad-acceso/api/v1/auth/logout',{data:{},headers:{Authorization:'Bearer '+apiToken,'Idempotency-Key':crypto.randomUUID()}});assert.equal(apiLogout.status(),200);
 if(!input.slotAlreadyCreated){ await goto(op,detail+'/horarios/nuevo','operator1');const site=await op.locator('[name=site_id] option').evaluateAll(ns=>ns.map(n=>n.value).find(Boolean));assert.ok(site);await op.locator('[name=site_id]').selectOption(site);await op.locator('[name=capacity]').fill('1');await submit(op,new RegExp('/campanas/'+id+'/horarios$'));await op.reload();assert.match(await op.locator('main').innerText(),/Horarios por sede/);report.records.site=site;report.checks.push({campaignSlotCreated:true});
}else{await goto(op,detail+'/horarios','operator1');report.records.site=input.site;assert.equal(await op.locator('tbody tr').count(),1);report.checks.push({existingCampaignSlotPersisted:true});}
 for(const width of[390,768,1440]){await op.setViewportSize({width,height:1000});await op.waitForTimeout(600);assert.ok(await op.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await op.screenshot({path:path.join(output,'horario-'+width+'.png'),fullPage:true});}
 for(const[user,url]of[['donor1',detail+'/publicacion'],['donor1','/configuracion/politica']]){const r=await sessions[user].page.goto(input.base+url);assert.equal(r.status(),403);report.negative.push({user,path:url,status:r.status()});}
 const foreign=await login('operator2');const denied=await foreign.page.goto(input.base+detail+'/publicacion');assert.equal(denied.status(),403);report.negative.push({user:'operator2',path:detail+'/publicacion',status:403});
 // Las asignaciones antiguas pueden estar vencidas: se concede una nueva ventana
 // de prueba mediante los formularios autorizados, sin cambiar el estado del traslado.
 const transport=sessions.transport1.page;await goto(transport,'/traslados','transport1');
 const candidates=await transport.locator('tbody tr').evaluateAll(rows=>[...new Set(rows.filter(r=>/Preparado|Recolectado|En tránsito|Incidencia|Entregado/.test(r.textContent)).flatMap(r=>[...r.querySelectorAll('a[href^="/traslados/"]')].map(n=>new URL(n.href).pathname)).filter(u=>/^\/traslados\/[0-9a-f-]{36}$/.test(u)))]);
 assert.ok(candidates.length,'Se requiere un traslado ficticio activo de transport1');
 const admin=sessions.admin1.page;await goto(admin,'/administracion/dispositivos/nuevo','admin1');
 const device=await admin.locator('[name=id]').inputValue();report.records.device=device;
 await admin.locator('[name=user_id]').selectOption({label:'transport1'});await admin.locator('[name=source]').selectOption('SIMULATOR');await admin.locator('[name=label]').fill('Prueba ficticia GCP portal03, sin GPS físico');
 const expires=new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Monterrey',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(Date.now()+2*3600000)).replace(' ','T');
 await admin.locator('[name=expires_at]').fill(expires);await submit(admin,new RegExp('/administracion/dispositivos/'+device+'$'));
 const co=sessions.coordinator1.page;await goto(co,candidates[0]+'/rastreo/asignar','coordinator1');await co.locator('[name=device_id]').selectOption(device);await co.locator('[name=human_confirmation]').check();await co.locator('[name=reason]').fill('Ventana sintética de comprobación del gateway; no captura física');await submit(co,new RegExp(candidates[0]+'/rastreo$'));report.checks.push({trackingAssignmentCreatedByForm:true,source:'SIMULATOR'});
 let subscription=false;
 for(const item of candidates.slice(0,1)){const events=[];const listener=ws=>{assert.ok(ws.url().startsWith('wss://34.18.186.116/'));ws.on('framereceived',frame=>{try{const m=JSON.parse(frame.payload);events.push({type:m.type,code:m.type==='error'?m.code:undefined});}catch{}});};co.on('websocket',listener);
  const r=await co.goto(input.base+item+'/mapa');assert.equal(r.status(),200);await pause(1600);if(!(await co.locator('#tracking-status').innerText()).includes('Finalizado')){const until=Date.now()+20000;while(Date.now()<until&&!events.some(x=>x.type==='subscribed'))await pause(250);if(events.some(x=>x.type==='subscribed')){report.wss=events;report.records.mapShipment=item.split('/').pop();subscription=true;await co.screenshot({path:path.join(output,'mapa-gateway.png'),fullPage:true});co.off('websocket',listener);break;}}
  co.off('websocket',listener);
 }
 assert.ok(subscription,'No se encontró suscripción WSS autorizada por el gateway');report.checks.push({publicGatewayWssAuthenticated:true,subscribed:true,positionsPublished:false});
 const mapDenied=await sessions.donor1.page.goto(input.base+'/traslados/'+report.records.mapShipment+'/mapa');assert.equal(mapDenied.status(),403);report.negative.push({user:'donor1',map:true,status:403});
 await goto(admin,'/administracion/dispositivos/'+device+'/revocar','admin1');await admin.locator('[name=human_confirmation]').check();await admin.locator('[name=reason]').fill('Terminar permiso temporal de comprobación del despliegue');await submit(admin,new RegExp('/administracion/dispositivos/'+device+'$'));report.records.deviceRevoked=true;
 await co.waitForFunction(()=>document.getElementById('tracking-status').textContent.includes('Finalizado'),{},{timeout:45000});report.checks.push({openMapPermissionRevocation:true});await co.screenshot({path:path.join(output,'mapa-permiso-terminado.png'),fullPage:true});
 await goto(sessions.operator1.page,'/panel','operator1');const token=await op.locator('input[name=csrf_token]').first().inputValue();const logout=await sessions.operator1.context.request.post(input.base+'/logout',{form:{csrf_token:token},headers:{Referer:op.url()},maxRedirects:0});assert.equal(logout.status(),302);const after=await sessions.operator1.context.request.get(input.base+'/panel',{maxRedirects:0});assert.equal(after.status(),302);report.checks.push({logoutRejected:true});
 assert.deepEqual(report.consoleErrors,[]);report.passed=true;
 }catch(e){report.failure=e.message;report.failureLocation=e.stack.split('\n').slice(1,4);process.exitCode=1;}finally{for(const c of contexts)await c.close();await browser.close();report.completedAt=new Date().toISOString();fs.writeFileSync(path.join(output,'browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,pages:report.pages.length,checks:report.checks.length,failure:report.failure}));}})();
