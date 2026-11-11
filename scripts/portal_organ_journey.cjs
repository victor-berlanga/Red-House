'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
module.exports=async function(h){
 const {login,goto,fill,save,confirm,proof,reject,check,id,input}=h;
 const {unit,result}=input.organ;
 await login('origin');await goto('/inventario/'+unit.id+'/liberar');await confirm();await proof('origin');await reject(409);
 check('Órgano incompleto no se libera antes de revisión HLA','origin');
 await goto('/laboratorio/resultados/'+result.id+'/revisar');await fill({decision:'AUTHORIZED'});await confirm();await proof('origin');await save(new RegExp('/laboratorio/resultados/'+result.id+'$'));
 await goto('/inventario/'+unit.id+'/liberar');await confirm();await proof('origin');await save(new RegExp('/inventario/'+unit.id+'$'));
 await login('destination');await goto('/donantes/recipient/nuevo');await fill({folio:'ORG-P-'+crypto.randomUUID().slice(0,8),display_name:'Receptor ficticio de órgano',blood_group:'O+',kind:'ORGAN',organ_type:'KIDNEY',studies:'Ensayo técnico con referencias documentales de etapa 02; sin validez clínica'});await save(/\/donantes\/recipient\/[a-f0-9-]+$/);const recipient=id();
 await goto('/solicitudes/nueva');await fill({recipient_id:recipient,component:'KIDNEY',quantity:1,urgency:2});await save(/\/solicitudes\/[a-f0-9-]+$/);const request=id();
 await goto('/solicitudes/'+request+'/evaluar');await save(/\/evaluaciones\/[a-f0-9-]+$/);const evaluation=id();
 await goto(`/evaluaciones/${evaluation}/dictamen/${unit.id}`);await fill({decision:'FAVORABLE'});await confirm();await save(new RegExp('/evaluaciones/'+evaluation+'$'));
 await goto(`/evaluaciones/${evaluation}/reservar/${unit.id}`);await confirm();await proof('destination');await reject(409);check('Órgano sin constancia externa vigente no se reserva','destination');
 await goto('/solicitudes/'+request+'/constancias/nueva');await fill({authority:'Autoridad ficticia de ensayo',reference:'SYNTHETIC-'+request,decision:'RECORDED'});await confirm();await save(new RegExp('/solicitudes/'+request+'/constancias$'));
 await goto(`/evaluaciones/${evaluation}/reservar/${unit.id}`);await confirm();await proof('destination');await save(/\/operaciones\/[a-f0-9-]+$/);
 const link=await h.page().getByText('Ver reserva',{exact:true}).getAttribute('href');const reservation=new URL(link,input.base).pathname.split('/').pop();
 await login('coordinator');await goto('/traslados/nuevo?reservation_id='+reservation);await fill({transport_user_id:input.seedAccounts.transport1.id});await confirm();await save(/\/traslados\/[a-f0-9-]+$/);const shipment=id();
 for(const [state,user] of [['PREPARED','operator1'],['COLLECTED','transport1'],['IN_TRANSIT','transport1'],['DELIVERED','transport1'],['ACCEPTED','operator2']]){
  await login(user);await goto(`/traslados/${shipment}/paso/${state}`);await confirm();
  if(['COLLECTED','DELIVERED','ACCEPTED'].includes(state))await fill({scanned_resource_id:unit.id,seal:'SELLO-ORGANO-FICTICIO',reported_handover_user_id:input.seedAccounts[state==='COLLECTED'?'operator1':state==='DELIVERED'?'operator2':'transport1'].id,electronic_acceptance:true});
  await save(new RegExp('/traslados/'+shipment+'$'));
 }
 const workers=await h.page().request.post(input.base+'/test/run-workers',{timeout:120000});assert.equal(workers.status(),200);
 await login('destination');await goto('/inventario/'+unit.id+'/destino');await fill({destination:'TRANSPLANTED',reference:'Trasplante ficticio, aceptación técnica sin autorización clínica real'});await confirm();await proof('destination');await save(new RegExp('/inventario/'+unit.id+'$'));await h.page().reload();
 check('Órgano: HLA revisado, constancia sintética, reserva, custodia, recepción y destino persistente','destination');
 return {resource:unit.id,recipient,request,evaluation,shipment};
};
