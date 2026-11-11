'use strict';
const assert=require('node:assert/strict');
module.exports=async function(h,resource){
 const {login,goto,fill,save,confirm,id,input,check}=h;
 await login('auditor1');await goto('/hallazgos/nuevo');await fill({description:'Comprobación ficticia de documentación del destino',priority:'MEDIUM',assignee_id:input.accounts.coordinator.id,resource_id:resource,evidence:'Referencia sintética del ensayo'});await save(/\/hallazgos\/[a-f0-9-]+$/);const finding=id();
 await login('coordinator');await goto('/hallazgos/'+finding+'/atender/IN_PROGRESS');await fill({corrective_action:'Contraste de documentos ficticios'});await confirm();await save(new RegExp('/hallazgos/'+finding+'$'));
 await goto('/hallazgos/'+finding+'/atender/PENDING_VERIFICATION');await fill({corrective_action:'Revisión ficticia terminada',evidence:'Identificadores del ensayo conservados'});await confirm();await save(new RegExp('/hallazgos/'+finding+'$'));
 assert.equal((await h.page().request.get(input.base+'/hallazgos/'+finding+'/atender/CLOSED')).status(),403);
 await login('auditor1');await goto('/hallazgos/'+finding+'/atender/CLOSED');await fill({evidence:'Verificación independiente ficticia'});await confirm();await save(new RegExp('/hallazgos/'+finding+'$'));await h.page().reload();assert.ok((await h.page().locator('main').innerText()).includes('Cerrado'));
 check('Hallazgo atendido por coordinador y cerrado por auditor distinto; responsable no puede verificar','auditor1');return finding;
};
