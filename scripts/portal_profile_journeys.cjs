'use strict';
// Extensión de los recorridos: usa formularios reales del mismo navegador.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
module.exports=async function(h){
 const {login,goto,fill,save,confirm,api,check,id,input}=h;
 const stamp=crypto.randomUUID().slice(0,8);
 const local=(minutes=0)=>new Date(Date.now()+minutes*60000-6*3600000).toISOString().slice(0,16);
 async function timezone(zone){const page=h.page();await page.locator('details.timezone-menu').evaluate(e=>e.open=true);const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/preferencias/horario'&&r.request().method()==='POST');await page.locator('#display-timezone').selectOption(zone);assert.equal((await response).status(),200);await page.waitForFunction(zone=>document.querySelector('main form input[name="_timezone"]')?.value===zone,zone);}
 await login('admin');await goto('/configuracion/institucion');
 await fill({published:true,description:'Institución ficticia publicada '+stamp,latitude:'25.6866',longitude:'-100.3161',coordinate_source:'Coordenadas sintéticas de aceptación',coordinate_recorded_at:local(-5),synthetic:true});await confirm();await save(/\/configuracion$/);
 let p=h.page();const published=await p.request.get(input.base+'/');assert.ok((await published.text()).includes('Institución ficticia publicada '+stamp));assert.ok(!(await published.text()).includes('Coordenadas sintéticas de aceptación'));
 check('Publicación institucional explícita, sin coordenadas privadas en sitio público','admin');
 await goto('/administracion/dispositivos/nuevo');await fill({user_id:input.seedAccounts.transport1.id,source:'SIMULATOR',label:'Emisor ficticio '+stamp,expires_at:local(1440)});await save(/\/administracion\/dispositivos\/[a-f0-9-]+$/);const device=id();
 await goto('/administracion/dispositivos/'+device+'/credencial');await confirm();await save(new RegExp('/administracion/dispositivos/'+device+'/credencial$'));assert.ok((await h.page().locator('#device-credential').inputValue()).length>20);
 await goto('/administracion/dispositivos/'+device+'/revocar');await confirm();await save(new RegExp('/administracion/dispositivos/'+device+'$'));check('Administrador registra emisor, rota credencial y revoca dispositivo','admin');
 const site=await api('identidad_acceso','POST','/api/v1/catalogues/sites',{name:'Sede ficticia '+stamp,municipality:'Monterrey',address:'Dirección ficticia de prueba'},'admin1');
 await login('donor');await goto('/donantes/donor/nuevo');await fill({folio:'DON-'+stamp,display_name:'Donante ficticio de aceptación',blood_group:'O+',consent:true});await save(/\/donantes\/donor\/[a-f0-9-]+$/);const donor=id();
 await goto('/donantes/donor/'+donor+'/consentimientos/nuevo');await fill({policy_version:'SYNTHETIC-1',reference:'Consentimiento ficticio',effective_at:local(-2),granted:true});await confirm();await save(/\/consentimientos$/);await h.page().reload();check('Donante registra expediente y consentimiento versionado persistente','donor1');
 assert.equal((await h.page().goto(input.base+'/inventario/'+input.unit.id)).status(),403);check('Donante rechazado por URL de inventario ajeno','donor1');
 await login('operator1');await goto('/campanas/nueva');const campaignStart=local(5);await fill({title:'Campaña ficticia '+stamp,starts_at:campaignStart,ends_at:local(240),capacity:'10'});await timezone('UTC');assert.equal(await h.page().locator('#starts_at').inputValue(),new Date(campaignStart+'-06:00').toISOString().slice(0,16));await save(/\/campanas$/);
 const campaigns=await api('donantes','GET','/api/v1/campaigns?q='+encodeURIComponent('Campaña ficticia '+stamp),undefined,'operator1');const campaign=campaigns.items.find(r=>r.title.endsWith(stamp));assert.ok(campaign);
 assert.equal(Date.parse(campaign.starts_at),Date.parse(campaignStart+'-06:00'));check('Cambio Monterrey/UTC conserva instante capturado y almacenamiento UTC','operator1');
 await goto('/campanas/'+campaign.id+'/publicacion');await timezone('America/Monterrey');await fill({published:true,venue:'Sede pública de prueba',information:'Actividad ficticia, sin criterios médicos'});await confirm();await save(new RegExp('/campanas/'+campaign.id+'$'));
 for(const minute of [20,50,80]){await goto('/campanas/'+campaign.id+'/horarios/nuevo');await fill({site_id:site.id,starts_at:local(minute),ends_at:local(minute+15),capacity:'1'});await save(new RegExp('/campanas/'+campaign.id+'/horarios$'));}
 const slots=(await api('donantes','GET','/api/v1/campaign-slots?campaign_id='+campaign.id,undefined,'operator1')).items;
 await login('donor');await goto('/citas/nueva?campaign_id='+campaign.id+'&slot_id='+slots[0].id);await fill({donor_id:donor,campaign_id:campaign.id,slot_id:slots[0].id});await save(/\/citas\/[a-f0-9-]+$/);const appointment=id();
 await goto('/citas/'+appointment+'/horario');await fill({action:'CONFIRM'});await confirm();await save(new RegExp('/citas/'+appointment+'$'));
 await goto('/citas/'+appointment+'/horario');await fill({action:'RESCHEDULE',slot_id:slots[1].id});await confirm();await save(new RegExp('/citas/'+appointment+'$'));
 await goto('/citas/'+appointment+'/horario');await fill({action:'CANCEL'});await confirm();await save(new RegExp('/citas/'+appointment+'$'));await h.page().reload();check('Agenda con sede/horario: reservar, confirmar, reprogramar y cancelar','donor1');
 if(input.accounts.donor_race){
  await login('donor_race');await goto('/donantes/donor/nuevo');await fill({folio:'RACE-'+stamp,display_name:'Segundo donante ficticio',blood_group:'O+',consent:true});await save(/\/donantes\/donor\/[a-f0-9-]+$/);const secondDonor=id();
  const contenders=[];
  for(const [alias,person] of [['donor',donor],['donor_race',secondDonor]]){await login(alias);await goto('/citas/nueva?campaign_id='+campaign.id+'&slot_id='+slots[2].id);await fill({donor_id:person,campaign_id:campaign.id,slot_id:slots[2].id});contenders.push(h.page());}
  const results=await Promise.all(contenders.map(async page=>{const pending=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/citas/nueva');await page.locator('main form button[type=submit]').last().click();return (await pending).status();}));assert.deepEqual(results.slice().sort(),[302,409]);
  const loser=contenders[results.indexOf(409)];assert.equal(await loser.locator('#slot_id').inputValue(),slots[2].id);assert.ok(await loser.locator('#form-error').isVisible());
  const saved=(await api('donantes','GET','/api/v1/campaign-slots/'+slots[2].id,undefined,'operator1'));assert.equal(saved.occupied,1);assert.equal(saved.available,0);check('Dos cuentas compiten en navegador por último cupo: una reserva; rechazo conserva valores','donor');
 }
 await login('origin');await goto('/donantes/evaluacion/'+donor);await fill({decision:'ELIGIBLE'});await confirm();await save(new RegExp('/donantes/donor/'+donor+'$'));
 await goto('/donaciones/nueva');await fill({donor_id:donor,kind:'BLOOD',component:'RBC',collected_at:local(-1)});await confirm();await save(/\/donaciones\/[a-f0-9-]+$/);const donation=id();
 await login('operator1');await goto('/donaciones/'+donation+'/procesar');await fill({state:'PROCESSED'});await confirm();await save(new RegExp('/donaciones/'+donation+'$'));
 await goto('/inventario/nuevo');await fill({folio:'SRC-'+stamp,component:'RBC',blood_group:'O+',expires_at:local(1440),donation_id:donation});await save(/\/inventario\/[a-f0-9-]+$/);const resource=id();
 await goto('/inventario/'+resource+'/componentes');await fill({folio_1:'RBC-'+stamp,component_1:'RBC',expires_at_1:local(1200)});await confirm();await save(new RegExp('/inventario/'+resource+'/linaje$'));assert.ok((await h.page().locator('main').innerText()).includes('RBC-'+stamp));
 await goto('/inventario/'+resource+'/etiqueta');assert.ok(await h.page().locator('img').count());check('Donación, evaluación médica, procesamiento, fraccionamiento, linaje y etiqueta','operator1');
 await goto('/conservacion/equipos/nuevo');await fill({label:'Equipo ficticio '+stamp,location:'Sede de ensayo',calibration_reference:'Referencia sintética'});await save(/\/conservacion\/equipos$/);check('Equipo de conservación registrado mediante formulario','operator1');
 const equipment=(await api('inventario','GET','/api/v1/cold/equipment?q='+encodeURIComponent('Equipo ficticio '+stamp),undefined,'operator1')).items.find(r=>r.label.endsWith(stamp));
 const child=(await api('inventario','GET','/api/v1/resources?q=RBC-'+stamp,undefined,'operator1')).items.find(r=>r.folio==='RBC-'+stamp);
 await login('origin');await goto('/conservacion/perfiles/nuevo');await fill({kind:'BLOOD',component:'RBC',minimum_c:'1',maximum_c:'5',max_gap_seconds:'3600',source:'Límites ficticios para ensayo, sin validación clínica '+stamp});await save(/\/conservacion\/perfiles$/);
 const thermal=(await api('inventario','GET','/api/v1/cold/profiles',undefined,'medical1')).items.find(r=>r.source.endsWith(stamp));
 await goto('/inventario/'+child.id+'/controles');await fill({lab_profile_id:input.profile.id,cold_equipment_id:equipment.id,cold_profile_id:thermal.id});await confirm();await save(new RegExp('/inventario/'+child.id+'/conservacion$'));
 await login('operator1');await goto('/inventario/'+child.id+'/lectura');await fill({temperature_c:'9',source:'Lectura sintética fuera del intervalo de prueba',calibration_reference:'Calibración ficticia'});await save(new RegExp('/inventario/'+child.id+'/conservacion$'));
 await login('origin');await goto('/inventario/'+child.id+'/revision-calidad');await confirm();await save(new RegExp('/inventario/'+child.id+'/conservacion$'));await h.page().reload();check('Perfil térmico sintético, controles, excursión y revisión documentada por médico','origin');
 await login('donor');await goto('/donantes/donor/'+donor+'/consentimientos/nuevo');await fill({policy_version:'SYNTHETIC-1',reference:'Retirada ficticia',effective_at:local(),granted:false});await confirm();await save(/\/consentimientos$/);check('Retirada de consentimiento conserva historial','donor1');
 const donorPage=h.page();await donorPage.locator('form[action="/logout"] button:visible').first().click();await donorPage.waitForURL(/\/login/);
 await goto('/recuperar-acceso');await fill({username:input.accounts.donor.username});
 const sent=donorPage.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/recuperar-acceso');await donorPage.locator('main button[type=submit]').click();assert.equal((await sent).status(),200);
 await login('admin');const delivered=await h.page().request.post(input.base+'/test/mailbox');const {token}=await delivered.json();assert.ok(token,'SMTP local entregó el token');
 await login('donor');await goto('/recuperar-acceso/confirmar');const password=input.password+'Changed!';await fill({token,password,confirmation:password});
 let response=donorPage.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/recuperar-acceso/confirmar');await donorPage.locator('main button[type=submit]').click();assert.equal((await response).status(),200);
 await goto('/recuperar-acceso/confirmar');await fill({token,password,confirmation:password});response=donorPage.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/recuperar-acceso/confirmar');await donorPage.locator('main button[type=submit]').click();assert.equal((await response).status(),401);
 await goto('/login');await donorPage.locator('#login_email').fill(input.accounts.donor.username);await donorPage.locator('#password').fill(password);await Promise.all([donorPage.waitForURL('**/panel'),donorPage.locator('button[type=submit]').click()]);check('Recuperación por SMTP real local, token de un uso y nuevo login','donor');
 await login('origin');
 return {donor,donation,resource,appointment,campaign:campaign.id};
};
