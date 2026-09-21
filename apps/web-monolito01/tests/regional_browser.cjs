const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const base=process.env.BASE_URL, data=JSON.parse(process.env.REGIONAL_DATA), output=process.env.BROWSER_ARTIFACTS;
 fs.mkdirSync(output,{recursive:true});
 const failures=[],assets=[],pages={};
 async function login(role){
   if(pages[role]) return pages[role];
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   const p=await context.newPage();pages[role]=p;
   p.on('pageerror',e=>failures.push(e.message));
   p.on('response',r=>{if(r.url().includes('/static/')&&r.status()>=400)assets.push(r.url());});
   await p.goto(base+'/login');
   await p.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');
   await p.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);
   await p.getByRole('button',{name:'Iniciar sesión'}).click();
   await p.waitForURL(u=>!u.pathname.includes('/login'));
   return p;
 }
 async function submit(p,title,values){
   const section=p.locator('section').filter({has:p.getByRole('heading',{name:title,exact:true})});
   assert.equal(await section.count(),1,title);
   for(const [name,value] of Object.entries(values)){
      const el=section.locator(`[name="${name}"]`);
      if(await el.isDisabled())continue; // El motivo solo se captura al confirmar.
      const tag=await el.evaluate(e=>e.tagName);
      if(tag==='SELECT') await el.selectOption(String(value));
      else if((await el.getAttribute('type'))==='checkbox') await el.check();
      else await el.fill(String(value));
   }
   const form=section.locator('form');
   const submit=section.locator('button[type=submit]');
   if(await form.getAttribute('data-confirm-edit')){
     await submit.click();
     const dialog=section.locator('dialog[open]');
     assert.equal(await dialog.count(),1);
     const reason=dialog.locator('textarea');
     if(await reason.count())await reason.fill(String(values[await reason.getAttribute('name')] || 'Operación de prueba confirmada'));
     await Promise.all([p.waitForNavigation(),dialog.locator('[data-confirm-accept]').click()]);
   }else await Promise.all([p.waitForNavigation(),submit.click()]);
   assert.equal(await p.locator('h1').count(),1);
   await navigation(p);
   assert(!await p.getByText('Operación no completada',{exact:true}).count(),await p.locator('body').innerText());
 }
 async function navigation(p){
   const current=new URL(p.url()).pathname;
   const target=['/sangre/personas/donor','/sangre/personas/recipient','/sangre/donaciones','/sangre/solicitudes','/sangre/traslados','/sangre/rutas','/sangre/panel-regional','/auditoria'].find(x=>current===x||current.startsWith(x+'/'));
   if(!target)return;
   const active=p.locator('.sidebar-nav a[aria-current="page"]');
   assert.equal(await active.count(),1,current);
   assert.equal(await active.getAttribute('href'),target);
   assert(await active.evaluate(el=>el.classList.contains('active')));
   assert.equal(await p.locator(`.sidebar-nav a[href="${target}"]`).count(),1);
 }
 async function capture(p,name){await navigation(p);await p.evaluate(()=>scrollTo(0,0));await p.screenshot({path:path.join(output,name+'.png'),fullPage:true,animations:'disabled'});await p.screenshot({path:path.join(output,name+'_vista.png'),fullPage:false,animations:'disabled'});}
 async function overflow(p){assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Desbordamiento horizontal fuera de tablas');}
 try{
   const op=await login('operador');
   await op.goto(base+'/sangre/personas/donor');
   await capture(op,'Donantes_lista');
   assert(!/fictici|académico/i.test((await op.locator('main label').allTextContents()).join(' ')));
   assert(!(await op.locator('body').innerText()).includes('ENTORNO ACADÉMICO'));
   await submit(op,'Registrar expediente',{institution_id:data.north,record_code:'BROWSER-DONOR',display_name:'Donante ficticio de prueba',blood_group:'O-',restrictions:'Ninguna registrada DEMO',donation_kind:'VOLUNTARY',background:'SECRETO-CLINICO-ANTECEDENTES',consent_reference:'CONSENT-BROWSER',consent_at:new Date(Date.now()-60000).toISOString().slice(0,16)});
   const donorUrl=op.url(),donorId=donorUrl.split('/').at(-1);
   await op.locator('[name=restrictions]').fill('Actualización reservada DEMO');
   assert(!await op.locator('[name=audit_reason]').isVisible());
   await submit(op,'Actualizar expediente',{audit_reason:'Corrección documental autorizada'});
   const med=await login('medico');await med.goto(donorUrl);
   await submit(med,'Registrar evaluación del donante',{decision:'ELIGIBLE',reason:'Evaluación humana ficticia',human_confirmation:true});
   await capture(med,'Donante_revision');
   assert((await med.locator('.regional-facts').innerText()).includes('Elegible'));
   await med.setViewportSize({width:390,height:844});
   await med.getByRole('button',{name:'Abrir menú'}).click();
   assert(await med.locator('.sidebar-nav a[aria-current="page"]').isVisible());
   await capture(med,'Donantes_navegacion_mobile');
   await med.keyboard.press('Escape');await med.setViewportSize({width:1440,height:1000});
   await op.goto(base+'/sangre/donaciones');
   await submit(op,'Registrar donación',{donation_code:'BROWSER-DONATION',donor_id:donorId});
   const donationUrl=op.url();
   await submit(op,'Registrar etapa',{status:'COLLECTED',observation:'Recolección demostrativa realizada'});
   await submit(op,'Registrar etapa',{status:'PROCESSED',observation:'Procesamiento demostrativo documentado'});
   await med.goto(donationUrl);
   await submit(med,'Liberar unidad / componente',{traceability_code:'BROWSER-UNIT',component_id:data.component,location_id:data.northLocation,expires_at:new Date(Date.now()+86400000).toISOString().slice(0,16),release_reference:'PRUEBAS-BROWSER',human_confirmation:true});
   await med.goto(donationUrl);await capture(med,'Donacion_procesamiento');
   const dest=await login('medico.valle');await dest.goto(base+'/sangre/personas/recipient');
   await submit(dest,'Registrar expediente',{institution_id:data.valley,record_code:'BROWSER-RECIPIENT',display_name:'Receptor ficticio de prueba',blood_group:'O-',restrictions:'Ninguna registrada DEMO',requirement:'SECRETO-CLINICO-REQUERIMIENTO',urgency:'URGENT',studies:'SECRETO-CLINICO-ESTUDIOS',current_status:'ACTIVE'});
   const recipientId=dest.url().split('/').at(-1);
   await dest.locator('[name=studies]').fill('SECRETO-CLINICO-ESTUDIOS actualizado');
   await submit(dest,'Actualizar expediente',{audit_reason:'Corrección documental autorizada'});
   await dest.goto(base+'/sangre/solicitudes');
   await submit(dest,'Crear solicitud de receptor',{request_code:'BROWSER-REQUEST',recipient_id:recipientId,component_id:data.component,quantity:1,urgency:'URGENT',justification:'SECRETO-CLINICO-JUSTIFICACION'});
   const requestUrl=dest.url();
   const coord=await login('coordinador');await coord.goto(base+'/sangre/rutas');
   await submit(coord,'Registrar o actualizar ruta',{origin_id:data.north,destination_id:data.valley,distance_km:30,travel_minutes:45,source_reference:'Supuesto académico de 30 km / 45 minutos'});
   await coord.goto(requestUrl);await submit(coord,'Buscar candidatos regionales',{});await capture(coord,'Compatibilidad_priorizacion');
   assert(!(await coord.locator('body').innerText()).includes('SECRETO-CLINICO'));
   await coord.setViewportSize({width:390,height:844});await overflow(coord);await capture(coord,'Solicitud_mobile');await coord.setViewportSize({width:1440,height:1000});
   await dest.goto(requestUrl);
   const choice=dest.locator('[name=candidate_id] option').filter({hasText:'BROWSER-UNIT'});
   await submit(dest,'Autorización médica y reserva',{candidate_id:await choice.getAttribute('value'),reason:'Revisión humana demostrativa confirmada',human_confirmation:true});
   const allocationUrl=dest.url();
   await coord.goto(allocationUrl);
   await submit(coord,'Asignar y programar traslado',{transport_id:data.transport,vehicle:'VEHICULO-BROWSER-DEMO',departure_at:new Date(Date.now()+60000).toISOString().slice(0,16),eta:new Date(Date.now()+3600000).toISOString().slice(0,16)});
   await capture(coord,'Asignacion_traslado');
   for(const [role,status] of [['operador','PREPARED'],['traslado','COLLECTED'],['traslado','IN_TRANSIT'],['traslado','DELIVERED'],['operador.valle','ACCEPTED']]){
      const p=await login(role);await p.goto(allocationUrl);
      const values={status,location_description:'Ubicación ficticia documentada',observation:'Evento DEMO '+status,evidence_reference:'ACTA-BROWSER-'+status};
      if(status==='ACCEPTED')values.location_id=data.valleyLocation;
      await submit(p,'Registrar evento de custodia',values);
   }
   await dest.goto(requestUrl);await submit(dest,'Cerrar o cancelar solicitud',{status:'CLOSED',observation:'Cantidad recibida y cierre confirmado'});
   await capture(dest,'Solicitud_cerrada');
   const auditor=await login('auditor');await auditor.goto(allocationUrl);await capture(auditor,'Cadena_custodia');
   assert(!(await auditor.locator('body').innerText()).includes('SECRETO-CLINICO'));
   assert.equal(await auditor.locator('main form').count(),0);
   await auditor.goto(base+'/auditoria');await capture(auditor,'Auditoria_regional');
   await coord.goto(base+'/sangre/panel-regional');await coord.locator('#overview-chart .highcharts-root').waitFor();assert.equal(await coord.locator('.highcharts-root').count(),3);await overflow(coord);await capture(coord,'Panel_regional');
   await coord.setViewportSize({width:390,height:844});await overflow(coord);await capture(coord,'Panel_regional_mobile');
   assert.deepEqual(failures,[]);assert.deepEqual(assets,[]);
   console.log(JSON.stringify({result:'PASS',flow:'donor-to-receipt-and-closure',roles:Object.keys(pages),javascriptErrors:failures,missingAssets:assets,screenshots:fs.readdirSync(output).filter(n=>n.endsWith('.png')).length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
