'use strict';
const assert=require('node:assert/strict');
module.exports=async function(h,shipment){
 const {login,goto,api,check,input,contexts}=h;
 const waitEnded=page=>page.waitForFunction(()=>location.pathname==='/login'||document.querySelector('#tracking-coordinate')?.textContent==='Acceso terminado',{},{timeout:20000});
 // El cambio del responsable se inyecta en el fixture; el rechazo es del backend real.
 await login('transport1');await goto('/traslados/'+shipment+'/mapa');let page=h.page();await page.waitForFunction(()=>document.querySelector('#tracking-source').textContent.includes('SIMULADO'));
 assert.equal((await page.request.post(input.base+'/test/tracking-assignment/'+shipment+'/change')).status(),200);await waitEnded(page);
 assert.equal((await page.request.get(input.base+'/traslados/'+shipment+'/mapa')).status(),403);
 assert.equal((await page.request.post(input.base+'/test/tracking-assignment/'+shipment+'/restore')).status(),200);check('Mapa abierto cesa entrega y borra posición al cambiar responsable en fixture','transport1');
 for(const mode of ['expire','revoke','logout','role']){
  await login('map_viewer');await goto('/traslados/'+shipment+'/mapa');page=h.page();await page.waitForFunction(()=>document.querySelector('#tracking-source').textContent.includes('SIMULADO'));
  if(mode==='logout'){
   const other=await contexts.map_viewer.context.newPage();await other.goto(input.base+'/panel');await other.locator('form[action="/logout"] button:visible').first().click();await other.waitForURL(/\/login/);await other.close();
  }else if(mode==='role'){
   const users=await api('identidad_acceso','GET','/api/v1/users?q='+encodeURIComponent(input.accounts.map_viewer.username),undefined,'admin1');const user=users.items.find(row=>row.id===input.accounts.map_viewer.id);assert.ok(user);await api('identidad_acceso','POST','/api/v1/users/'+user.id+'/role',{version:user.version,role:'DONOR',human_confirmation:true,reason:'Ensayo de autorización continua'},'admin1');
  }else assert.equal((await page.request.post(input.base+'/test/tracking-session/'+mode)).status(),200);
  await waitEnded(page);assert.equal(await page.locator('#tracking-history tr').count(),0);check('Mapa abierto: '+mode+' retira acceso y datos sin recarga manual ('+(new URL(page.url()).pathname==='/login'?'redirige a login':'acceso terminado')+')','map_viewer');
  await contexts.map_viewer.context.close();delete contexts.map_viewer;
 }
 await login('transport1');
};
