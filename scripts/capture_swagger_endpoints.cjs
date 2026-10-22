'use strict';
// Capturas de Swagger ejecutado contra GCP; nunca fabrica respuestas HTTP.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const playwrightPath = process.env.REDHOUSE_PLAYWRIGHT || [path.resolve('.local/gcp-public/browser/node_modules/playwright'), '/private/tmp/redhouse-doc-tools/node_modules/playwright'].find(p => fs.existsSync(p)) || 'playwright';
const {chromium} = require(playwrightPath);
const BASE = 'https://34.18.186.116';
const OUTPUT = path.resolve('documentation/evidencias/gcp/swagger-endpoints');
const PRIVATE = path.resolve('.local/swagger-capture');
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const services = ['identidad-acceso','donantes','receptores','inventario','compatibilidad','priorizacion-geografia','transporte','custodia','alertas','auditoria','monitoreo'];
fs.mkdirSync(OUTPUT,{recursive:true});fs.mkdirSync(PRIVATE,{recursive:true,mode:0o700});
const report = fs.existsSync(path.join(OUTPUT,'manifest.json')) ? JSON.parse(fs.readFileSync(path.join(OUTPUT,'manifest.json'))) : {origin:BASE,startedAt:new Date().toISOString(),captures:[],issues:[]};
if(process.argv.includes('--refresh-availability'))report.captures=report.captures.filter(c=>!(c.service==='inventario'&&c.route==='/api/v1/availability'));
const save = () => fs.writeFileSync(path.join(OUTPUT,'manifest.json'),JSON.stringify(report,null,2)+'\n');
const privateFile=path.join(PRIVATE,'results.json');
const results=fs.existsSync(privateFile)?JSON.parse(fs.readFileSync(privateFile)):{run:Date.now().toString(36),outputs:{},fixtures:{}};
const savePrivate=()=>fs.writeFileSync(privateFile,JSON.stringify(results,null,2),{mode:0o600});
const iso=(minutes=0)=>new Date(Date.now()+minutes*60000).toISOString();
const confirm={human_confirmation:true,reason:'Demostración ficticia de Swagger con trazabilidad autorizada'};
async function once(key,fn){if(results.fixtures[key])return results.fixtures[key];const value=await fn();results.fixtures[key]=value;savePrivate();return value;}
const redact = value => {
  if(Array.isArray(value)) return value.map(redact);
  if(value && typeof value==='object') return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,/password|token|authorization|signature|upload_url|download_url|signed_url|refresh/i.test(k)?'[OCULTO]':redact(v)]));
  return typeof value==='string' ? value.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,'[JWT OCULTO]') : value;
};
let browser, context, request;const sessions={},specs={},pages={};
async function login(user){
  if(sessions[user] && sessions[user].until>Date.now()+60000) return sessions[user].token;
  const res=await request.post(BASE+'/services/identidad-acceso/api/v1/auth/login',{data:{username:user,password:state.password},timeout:30000});
  assert.equal(res.status(),200,'login '+user);const d=(await res.json()).data;
  sessions[user]={token:d.access_token,refresh:d.refresh_token,until:Date.now()+800000};return d.access_token;
}
async function api(service,method,route,data,user='medical2'){
 const token=user?await login(user):null;
 const res=await request.fetch(BASE+'/services/'+service+route,{method,data,headers:{Accept:'application/json',...(token?{Authorization:'Bearer '+token}:{}),'Idempotency-Key':crypto.randomUUID()},timeout:45000});
 const v=await res.json();if(res.status()>=300)throw Error(service+' '+method+' '+route+' '+res.status()+' '+JSON.stringify(redact(v)));
 return v.data;
}
async function waitShipment(identifier){
 for(let i=0;i<30;i++){
  const s=await api('transporte','GET','/api/v1/shipments/'+identifier,undefined,'coordinator1');
  if(!s.inventory_pending)return s;await new Promise(r=>setTimeout(r,1500));
 }
 throw Error('Traslado pendiente de sincronización '+identifier);
}
async function pageFor(service){
 if(pages[service])return pages[service];
 const page=await context.newPage();await page.goto(BASE+'/services/'+service+'/docs/',{waitUntil:'networkidle',timeout:45000});
 try {await page.waitForFunction(()=>window.ui?.specActions);await page.locator('.opblock').first().waitFor({timeout:30000});}
 catch(e){await page.screenshot({path:path.join(PRIVATE,'swagger-debug.png')});console.error((await page.locator('body').innerText()).slice(0,1800));throw e;}
 await page.addStyleTag({content:'.responses-inner > .responses-table,.curl-command{display:none!important}.highlight-code{max-height:550px;overflow:auto!important}'});
 pages[service]=page;return page;
}
async function capture(service,method,route,{user='medical2',data,params={},query={},failure=false,label}={}){
 const key=service+' '+method+' '+route+' '+(failure?'error':'success');
 if(report.captures.some(c=>c.key===key))return results.outputs[key];
 const page=await pageFor(service);const token=user?await login(user):null;
 await page.evaluate(token=>{window.ui.authActions.logout(['BearerJWT']);if(token)window.ui.preauthorizeApiKey('BearerJWT',token);},token);
 const operation=page.locator('.opblock-'+method.toLowerCase()).filter({has:page.locator('.opblock-summary-path').filter({hasText:route})}).filter({has:page.locator('.opblock-summary-path[data-path="'+route+'"]')});
 assert.equal(await operation.count(),1,'operation '+key);
 if(!await operation.locator('.opblock-body').count())await operation.locator('.opblock-summary').click();
 await operation.getByRole('button',{name:/^(Try it out|Cancel)$/}).waitFor();
 const tryButton=operation.getByRole('button',{name:'Try it out',exact:true});if(await tryButton.count())await tryButton.click();
 for(const [name,value] of Object.entries({page_size:3,...params,...query,'Idempotency-Key':crypto.randomUUID()})){
   const row=operation.locator('tr[data-param-name="'+name+'"]');if(!await row.count())continue;
   const input=row.locator('input');if(await input.count())await input.fill(String(value));
 }
 if(data!==undefined)await operation.locator('textarea').first().fill(JSON.stringify(data,null,2));
 const actual=Object.entries(params).reduce((r,[k,v])=>r.replace('{'+k+'}',v),route);
 const waiter=page.waitForResponse(r=>r.request().method()===method && new URL(r.url()).pathname===('/services/'+service+actual),{timeout:60000});
 await operation.getByRole('button',{name:'Execute',exact:true}).click();const response=await waiter;
 const status=response.status();await response.finished();await operation.locator('.live-responses-table').waitFor();await page.waitForTimeout(250);
 const success=status>=200&&status<300;
 if(failure?success:!success){let body;try{body=redact(await response.json());}catch{body='non-json'}throw Error(key+' unexpected '+status+' '+JSON.stringify(body));}
 // Captura nativa de Chromium. Se ocultan únicamente credenciales y URLs firmadas.
 const masks=[operation.locator('.curl-command')];
 const sensitiveRequest=service==='identidad-acceso'&&data&&('password'in data||'refresh_token'in data);
 if(sensitiveRequest)masks.push(operation.locator('textarea'));
 const sensitiveResponse=service==='identidad-acceso'&&/\/auth\/(login|refresh)$/.test(route)||service==='transporte'&&(/\/download$/.test(route)||method==='POST'&&/\/files$/.test(route));
 if(sensitiveResponse)masks.push(operation.locator('.live-responses-table .highlight-code'));
 await operation.scrollIntoViewIfNeeded();
 const folder=path.join(OUTPUT,service);fs.mkdirSync(folder,{recursive:true});
 const filename=method.toLowerCase()+'-'+route.replace(/^\//,'').replaceAll('/','-').replace(/[{}]/g,'')+'-'+(failure?'error':'exito')+'.png';
 await operation.screenshot({path:path.join(folder,filename),mask:masks,maskColor:'#555',animations:'disabled',timeout:30000});
 const item={key,service,method,route,status,result:failure?'error':'success',capture:service+'/'+filename,url:response.url(),at:new Date().toISOString(),label:label||specs[service].paths[route][method.toLowerCase()].summary};
 const body=await response.json();results.outputs[key]=body.data;savePrivate();
 report.captures.push(item);save();console.log(JSON.stringify({capture:key,status,total:report.captures.length}));
 await operation.locator('.opblock-summary').click();
 return body.data;
}
async function main(){
 browser=await chromium.launch({channel:'chrome',headless:true});
 context=await browser.newContext({viewport:{width:1600,height:1100},reducedMotion:'reduce'});request=context.request;
 await Promise.all(services.map(async service=>{const r=await request.get(BASE+'/services/'+service+'/openapi.json');assert.equal(r.status(),200);specs[service]=await r.json();}));
 const inventory={};
 for(const service of services)inventory[service]=Object.entries(specs[service].paths).flatMap(([p,ops])=>Object.entries(ops).filter(([m])=>['get','post','put','patch','delete'].includes(m)).map(([m,o])=>({method:m.toUpperCase(),path:p,operationId:o.operationId,summary:o.summary,internal:p.startsWith('/internal/')})));
 fs.writeFileSync(path.join(OUTPUT,'inventory.json'),JSON.stringify(inventory,null,2)+'\n');
 await capture('inventario','GET','/api/v1/availability',{user:null,failure:true});
 await capture('inventario','GET','/api/v1/availability',{user:'medical2'});
 if(process.argv.includes('--pilot'))return;
 await fullRun();
}
async function fullRun(){
 const C=capture, A=api, tag='SW-'+results.run;
 // Un error real y un éxito en una consulta protegida de cada propietario.
 for(const [s,r,u] of [
 ['identidad-acceso','/api/v1/auth/me','admin1'],['donantes','/api/v1/donors','medical1'],
 ['receptores','/api/v1/recipients','medical2'],['compatibilidad','/api/v1/evaluations','medical2'],
 ['priorizacion-geografia','/api/v1/routes','coordinator1'],['transporte','/api/v1/shipments','coordinator1'],
 ['alertas','/api/v1/alerts','operator1'],['auditoria','/api/v1/events','auditor1'],['monitoreo','/api/v1/status','admin1']]){
  await C(s,'GET',r,{user:null,failure:true});await C(s,'GET',r,{user:u});
 }
 // Identidad: se modifican solo la institución y las cuentas creadas para esta ejecución.
 const inst=await C('identidad-acceso','POST','/api/v1/institutions',{user:'admin1',data:{name:'Institución ficticia Swagger '+results.run}});
 const newAdmin='swadmin-'+results.run;
 await C('identidad-acceso','POST','/api/v1/institutions/{identifier}/administrator',{user:'admin1',params:{identifier:inst.id},data:{username:newAdmin,password:state.password,...confirm}});
 await C('identidad-acceso','GET','/api/v1/institutions',{user:'admin1'});
 await C('identidad-acceso','GET','/api/v1/institutions/{identifier}',{user:'admin1',params:{identifier:inst.id}});
 await C('identidad-acceso','PATCH','/api/v1/institutions/{identifier}',{user:newAdmin,params:{identifier:inst.id},data:{name:'Institución ficticia Swagger verificada '+results.run,version:inst.version,...confirm}});
 const user=await C('identidad-acceso','POST','/api/v1/users',{user:'admin1',data:{username:'swuser-'+results.run,password:state.password,tenant_id:state.tenants[0],role:'OPERATOR'}});
 await C('identidad-acceso','GET','/api/v1/users',{user:'admin1'});
 await C('identidad-acceso','PATCH','/api/v1/users/{identifier}',{user:'admin1',params:{identifier:user.id},data:{version:user.version,active:false}});
 await C('identidad-acceso','GET','/api/v1/audit-assignees',{user:'auditor1'});
 let site;
 for(const [kind,extra] of [['sites',{municipality:'Monterrey',address:'Dirección ficticia de demostración'}],['contacts',{value:'contacto@example.invalid'}],['schedules',{weekday:1,opens_at:'08:00',closes_at:'16:00'}],['capacities',{component:'RBC',quantity:10}],['locations',{description:'Ubicación ficticia para evidencia Swagger'}]]){
  const data={name:'Swagger '+kind+' '+results.run,...extra,...(site&&kind!=='contacts'?{parent_id:site.id}:{})};
  const row=await C('identidad-acceso','POST','/api/v1/catalogues/'+kind,{user:'admin1',data});
  if(kind==='sites')site=row;
  await C('identidad-acceso','GET','/api/v1/catalogues/'+kind,{user:'admin1'});
  await C('identidad-acceso','GET','/api/v1/catalogues/'+kind+'/{identifier}',{user:'admin1',params:{identifier:row.id}});
  await C('identidad-acceso','PATCH','/api/v1/catalogues/'+kind+'/{identifier}',{user:'admin1',params:{identifier:row.id},data:{...data,name:data.name+' revisado',version:row.version,active:true,...confirm}});
 }
 // Expediente y donación propios de Hospital 1.
 const donorData={folio:tag+'-DON',display_name:'Donante ficticio Swagger',blood_group:'O-',consent:true};
 let donor=await C('donantes','POST','/api/v1/donors',{user:'medical1',data:donorData});
 donor=await C('donantes','PATCH','/api/v1/donors/{identifier}',{user:'medical1',params:{identifier:donor.id},data:{...donorData,background:'Antecedentes ficticios de demostración',version:donor.version,...confirm}});
 await C('donantes','GET','/api/v1/donors/{identifier}',{user:'medical1',params:{identifier:donor.id}});
 await C('donantes','POST','/api/v1/donors/{identifier}/reviews',{user:'medical1',params:{identifier:donor.id},data:{decision:'ELIGIBLE',version:donor.version,...confirm}});
 const campaignData=await once('campaignData',async()=>({title:'Campaña ficticia Swagger '+results.run,starts_at:iso(60),ends_at:iso(1440),capacity:10}));
 let campaign=await C('donantes','POST','/api/v1/campaigns',{user:'operator1',data:campaignData});
 campaign=await C('donantes','PATCH','/api/v1/campaigns/{identifier}',{user:'operator1',params:{identifier:campaign.id},data:{...campaignData,capacity:12,version:campaign.version,...confirm}});
 await C('donantes','GET','/api/v1/campaigns',{user:'operator1'});
 await C('donantes','GET','/api/v1/campaigns/{identifier}',{user:'operator1',params:{identifier:campaign.id}});
 const appointment=await C('donantes','POST','/api/v1/appointments',{user:'operator1',data:{donor_id:donor.id,campaign_id:campaign.id}});
 await C('donantes','GET','/api/v1/appointments',{user:'operator1'});
 await C('donantes','POST','/api/v1/appointments/{identifier}/cancel',{user:'operator1',params:{identifier:appointment.id}});
 const donationData=await once('donationData',async()=>({donor_id:donor.id,kind:'BLOOD',component:'RBC',collected_at:iso(-10),...confirm}));
 let donation=await C('donantes','POST','/api/v1/donations',{user:'medical1',data:donationData});
 donation=await C('donantes','PATCH','/api/v1/donations/{identifier}',{user:'medical1',params:{identifier:donation.id},data:{collected_at:donationData.collected_at,version:donation.version,...confirm}});
 await C('donantes','GET','/api/v1/donations',{user:'operator1'});
 await C('donantes','GET','/api/v1/donations/{identifier}',{user:'operator1',params:{identifier:donation.id}});
 await C('donantes','POST','/api/v1/donations/{identifier}/steps',{user:'operator1',params:{identifier:donation.id},data:{state:'PROCESSED',version:donation.version,...confirm}});
 await C('donantes','GET','/api/v1/summary',{user:'operator1'});
 // Receptor y solicitud propios de Hospital 2, editados antes de crear relaciones.
 const recipientData={folio:tag+'-REC',display_name:'Receptor ficticio Swagger',kind:'BLOOD',blood_group:'A+',organ_type:null,studies:'Estudios ficticios para demostración autorizada'};
 let recipient=await C('receptores','POST','/api/v1/recipients',{user:'medical2',data:recipientData});
 recipient=await C('receptores','PATCH','/api/v1/recipients/{identifier}',{user:'medical2',params:{identifier:recipient.id},data:{...recipientData,restrictions:'Restricciones ficticias de demostración',version:recipient.version,...confirm}});
 await C('receptores','GET','/api/v1/recipients/{identifier}',{user:'medical2',params:{identifier:recipient.id}});
 const requestData={recipient_id:recipient.id,component:'RBC',quantity:1,urgency:2};
 let demand=await C('receptores','POST','/api/v1/requests',{data:requestData});
 demand=await C('receptores','PATCH','/api/v1/requests/{identifier}',{params:{identifier:demand.id},data:{component:'RBC',quantity:1,urgency:3,version:demand.version,...confirm}});
 await C('receptores','GET','/api/v1/requests');
 await C('receptores','GET','/api/v1/requests/{identifier}',{params:{identifier:demand.id}});
 await C('receptores','GET','/api/v1/summary');
 // Ruta y unidad trazable; no se cambian recursos anteriores.
 const routeData={origin_id:state.tenants[0],destination_id:inst.id,distance_km:10,travel_minutes:15,source:'Estimación ficticia para capturas de Swagger'};
 let route=await C('priorizacion-geografia','POST','/api/v1/routes',{user:'coordinator1',data:routeData});
 route=await C('priorizacion-geografia','PATCH','/api/v1/routes/{identifier}',{user:'coordinator1',params:{identifier:route.id},data:{distance_km:11,travel_minutes:16,source:routeData.source,version:route.version}});
 await C('priorizacion-geografia','GET','/api/v1/routes/{identifier}',{user:'coordinator1',params:{identifier:route.id}});
 const resourceData=await once('resourceData',async()=>({folio:tag+'-UNIT',kind:'BLOOD',component:'RBC',blood_group:'O-',expires_at:iso(2880),donation_id:donation.id}));
 let resource=await C('inventario','POST','/api/v1/resources',{user:'operator1',data:resourceData});
 resource=await C('inventario','PATCH','/api/v1/resources/{identifier}',{user:'operator1',params:{identifier:resource.id},data:{...resourceData,version:resource.version,...confirm}});
 await C('inventario','POST','/api/v1/resources/{identifier}/release',{user:'medical1',params:{identifier:resource.id},data:{version:resource.version,...confirm}});
 await C('inventario','GET','/api/v1/resources',{user:'operator1'});
 await C('inventario','GET','/api/v1/resources/{identifier}',{user:'operator1',params:{identifier:resource.id}});
 await C('inventario','GET','/api/v1/summary',{user:'operator1'});
 const evaluation=await C('compatibilidad','POST','/api/v1/evaluations',{data:{request_id:demand.id}});
 assert(evaluation.candidates.some(c=>c.resource_id===resource.id),'Unidad propia debe aparecer entre candidatos');
 await C('compatibilidad','GET','/api/v1/evaluations/{identifier}',{params:{identifier:evaluation.id}});
 await C('compatibilidad','POST','/api/v1/evaluations/{identifier}/reviews',{params:{identifier:evaluation.id},data:{resource_id:resource.id,decision:'FAVORABLE',...confirm}});
 const ranking=await C('priorizacion-geografia','POST','/api/v1/rankings',{data:{evaluation_id:evaluation.id}});
 await C('priorizacion-geografia','GET','/api/v1/rankings');
 await C('priorizacion-geografia','GET','/api/v1/rankings/{identifier}',{params:{identifier:ranking.id}});
 const proposal=await C('priorizacion-geografia','POST','/api/v1/allocation-proposals',{data:{evaluation_ids:[evaluation.id]}});
 await C('priorizacion-geografia','GET','/api/v1/allocation-proposals');
 await C('priorizacion-geografia','GET','/api/v1/allocation-proposals/{identifier}',{params:{identifier:proposal.id}});
 const operation=await C('inventario','POST','/api/v1/reservations',{data:{evaluation_id:evaluation.id,resource_id:resource.id,...confirm}});
 await C('inventario','GET','/api/v1/operations/{identifier}',{params:{identifier:operation.operation_id}});
 await C('inventario','POST','/api/v1/operations/{identifier}/resume',{params:{identifier:operation.operation_id}});
 let reservation=operation.reservation;
 await C('inventario','GET','/api/v1/reservations',{user:'coordinator1'});
 await C('inventario','GET','/api/v1/reservations/{identifier}',{user:'coordinator1',params:{identifier:reservation.id}});
 await C('inventario','POST','/api/v1/reservations/{identifier}/cancel',{params:{identifier:reservation.id},data:confirm});
 reservation=await once('secondReservation',async()=>{
   const e=await A('compatibilidad','POST','/api/v1/evaluations',{request_id:demand.id});
   await A('compatibilidad','POST','/api/v1/evaluations/'+e.id+'/reviews',{resource_id:resource.id,decision:'FAVORABLE',...confirm});
   return (await A('inventario','POST','/api/v1/reservations',{evaluation_id:e.id,resource_id:resource.id,...confirm})).reservation;
 });
 const shipmentData=await once('shipmentData',async()=>({reservation_id:reservation.id,transport_user_id:state.accounts.transport1.id,departure_at:iso(1),eta:iso(60),...confirm}));
 let shipment=await C('transporte','POST','/api/v1/shipments',{user:'coordinator1',data:shipmentData});
 await C('transporte','GET','/api/v1/shipments/{identifier}',{user:'coordinator1',params:{identifier:shipment.id}});
 shipment=await waitShipment(shipment.id);
 shipment=await C('transporte','POST','/api/v1/shipments/{identifier}/transitions',{user:'operator1',params:{identifier:shipment.id},data:{state:'PREPARED',version:shipment.version,...confirm}});
 shipment=await once('collected',async()=>{const s=await waitShipment(shipment.id);return A('transporte','POST','/api/v1/shipments/'+s.id+'/transitions',{state:'COLLECTED',version:s.version,...confirm},'transport1');});
 await C('transporte','POST','/api/v1/shipments/{identifier}/telemetry',{user:'transport1',params:{identifier:shipment.id},data:{latitude:25.68,longitude:-100.31,captured_at:iso()}});
 await C('transporte','GET','/api/v1/shipments/{identifier}/telemetry',{user:'transport1',params:{identifier:shipment.id}});
 const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEklEQVR4nGP8z4AdMOEQH6QSAM1BAQ/oQeJvAAAAAElFTkSuQmCC','base64');
 const prepared=await C('transporte','POST','/api/v1/shipments/{identifier}/files',{user:'coordinator1',params:{identifier:shipment.id},data:{mime_type:'image/png',size:png.length,sha256:crypto.createHash('sha256').update(png).digest('hex')}});
 await once('upload',async()=>{const r=await request.put(prepared.upload_url,{data:png,headers:prepared.upload_headers,timeout:45000});assert([200,201,412].includes(r.status()),'GCS upload '+r.status());return {uploaded:true};});
 await C('transporte','POST','/api/v1/files/{identifier}/verify',{user:'coordinator1',params:{identifier:prepared.file.id}});
 await C('transporte','GET','/api/v1/files/{identifier}/download',{user:'coordinator1',params:{identifier:prepared.file.id}});
 await C('transporte','GET','/api/v1/shipments/{identifier}/files',{user:'coordinator1',params:{identifier:shipment.id}});
 await C('transporte','GET','/api/v1/summary',{user:'coordinator1'});
 await once('finishShipment',async()=>{
   let s=await waitShipment(shipment.id);
   for(const [st,u] of [['IN_TRANSIT','transport1'],['DELIVERED','transport1'],['ACCEPTED','operator2']]){
    s=await waitShipment(s.id);s=await A('transporte','POST','/api/v1/shipments/'+s.id+'/transitions',{state:st,version:s.version,...confirm},u);
   }
   return waitShipment(s.id);
 });
 await C('custodia','GET','/api/v1/chains/{identifier}',{user:null,params:{identifier:shipment.id},failure:true});
 await C('custodia','GET','/api/v1/chains/{identifier}',{user:'coordinator1',params:{identifier:shipment.id}});
 await C('transporte','GET','/api/v1/shipments/{identifier}/tracking',{user:'coordinator1',params:{identifier:shipment.id}});
 await C('transporte','GET','/api/v1/shipment-statistics',{user:'coordinator1'});
 // Evidencias adicionales sobre registros propios: baja, retiro y cancelación.
 await C('donantes','POST','/api/v1/donors/{identifier}/withdraw',{user:'medical1',params:{identifier:donor.id},data:{version:(await A('donantes','GET','/api/v1/donors/'+donor.id,undefined,'medical1')).version,...confirm}});
 const disposable=await once('disposableResource',()=>A('inventario','POST','/api/v1/resources',{...resourceData,folio:tag+'-RET',donation_id:null},'operator1'));
 await C('inventario','POST','/api/v1/resources/{identifier}/withdraw',{user:'operator1',params:{identifier:disposable.id},data:{version:disposable.version,...confirm}});
 const cancellable=await once('cancellableRequest',()=>A('receptores','POST','/api/v1/requests',requestData));
 await C('receptores','POST','/api/v1/requests/{identifier}/cancel',{params:{identifier:cancellable.id},data:{version:cancellable.version,...confirm}});
 const alerts=await A('alertas','GET','/api/v1/alerts?page_size=100',undefined,'operator1');
 const ownResources=[donor.id,shipment.id,resource.id,appointment.id,operation.reservation.id,reservation.id];
 const alert=alerts.items.find(r=>r.status==='OPEN'&&ownResources.includes(r.resource_id));assert(alert,'Notificación propia disponible');
 await C('alertas','POST','/api/v1/alerts/{identifier}/acknowledge',{user:'operator1',params:{identifier:alert.id}});
 await C('monitoreo','GET','/api/v1/checks',{user:'admin1'});
 await C('auditoria','GET','/api/v1/event-options',{user:'auditor1'});
 const events=await A('auditoria','GET','/api/v1/events?resource='+resource.id,undefined,'auditor1');assert(events.items.length,'Evento propio centralizado');
 const event=events.items[0];
 await C('auditoria','GET','/api/v1/events/{identifier}',{user:'auditor1',params:{identifier:event.id}});
 await C('auditoria','GET','/api/v1/events/{identifier}/related',{user:'auditor1',params:{identifier:event.id}});
 await C('auditoria','GET','/api/v1/events/export',{user:'auditor1',query:{resource:resource.id}});
 await C('auditoria','GET','/api/v1/documentary-events',{user:'auditor1'});
 const finding=await C('auditoria','POST','/api/v1/findings',{user:'auditor1',data:{description:'Hallazgo ficticio de verificación Swagger '+results.run,priority:'LOW',assignee_id:state.accounts.coordinator1.id,event_ids:[event.id],evidence:'Capturas reales de la operación ficticia'}});
 await C('auditoria','GET','/api/v1/findings',{user:'auditor1'});
 await C('auditoria','GET','/api/v1/findings/{identifier}',{user:'auditor1',params:{identifier:finding.id}});
 let findingAction=await C('auditoria','POST','/api/v1/findings/{identifier}/actions',{user:'coordinator1',params:{identifier:finding.id},data:{status:'IN_PROGRESS',version:finding.version,corrective_action:'Revisar la demostración ficticia y su trazabilidad',...confirm}});
 await once('closeFinding',async()=>{
   const f=await A('auditoria','POST','/api/v1/findings/'+finding.id+'/actions',{status:'PENDING_VERIFICATION',version:findingAction.version,corrective_action:'Demostración ficticia revisada',evidence:'Peticiones exitosas y capturas de Swagger',...confirm},'coordinator1');
   return A('auditoria','POST','/api/v1/findings/'+finding.id+'/actions',{status:'CLOSED',version:f.version,evidence:'Evidencia ficticia contrastada para la captura',...confirm},'auditor1');
 });
 // Emisión, rotación y revocación en sesiones independientes de la automatización.
 const authLogin=await C('identidad-acceso','POST','/api/v1/auth/login',{user:null,data:{username:'medical1',password:state.password}});
 const authRefresh=await C('identidad-acceso','POST','/api/v1/auth/refresh',{user:null,data:{refresh_token:authLogin.refresh_token}});
 await C('identidad-acceso','POST','/api/v1/auth/revoke',{user:null,data:{refresh_token:authRefresh.refresh_token}});
 await C('identidad-acceso','POST','/api/v1/auth/logout',{user:'donor2'});delete sessions.donor2;
 report.publicCompletedAt=new Date().toISOString();save();
}
main().catch(e=>{report.issues.push({at:new Date().toISOString(),message:e.message});save();console.error(e.message);process.exitCode=1;}).finally(async()=>{
 for(const s of Object.values(sessions)){try{await request.post(BASE+'/services/identidad-acceso/api/v1/auth/logout',{headers:{Authorization:'Bearer '+s.token,'Idempotency-Key':crypto.randomUUID()}});}catch{}}
 if(browser)await browser.close();
});
