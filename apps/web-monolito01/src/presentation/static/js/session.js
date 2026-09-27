/* Solo comparte avisos entre pestañas; nunca credenciales ni capturas. */
(() => {
  'use strict';
  const dialog=document.getElementById('session-dialog');
  if(!dialog)return;
  const text=dialog.querySelector('[data-session-message]'), renew=dialog.querySelector('[data-session-renew]');
  const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('red-house-session'):null;
  let deadline=0,busy=false,expired=false,focused,epoch=0;
  async function request(url,options={}){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);try{return await fetch(url,{...options,signal:controller.signal});}finally{clearTimeout(timer);}}
  const show=()=>{if(!dialog.open){focused=document.activeElement;dialog.showModal();}};
  const close=()=>{if(dialog.open){dialog.close();focused?.focus();}};
  const end=()=>{if(expired)return;expired=true;epoch++;window.dispatchEvent(new Event('session-ended'));window.location.replace('/login');};
  function apply(state){deadline=Date.now()+(state.expires_at-state.server_time)*1000;expired=false;if(state.csrf_token)document.querySelectorAll('[name=csrf_token]').forEach(e=>e.value=state.csrf_token);if(deadline-Date.now()>300000)close();tick();}
  async function sync(){
    if(busy)return;
    const seen=epoch;
    try{const res=await request('/sesion/estado',{cache:'no-store'});if(seen!==epoch)return;if(res.status===401){end();return;}if(!res.ok)throw Error();apply(await res.json());}
    catch{if(dialog.open)text.textContent='No se pudo comprobar la conexión. Reintenta continuar antes de que termine la sesión.';}
  }
  function tick(){
    if(!deadline||expired||busy)return;
    const seconds=Math.ceil((deadline-Date.now())/1000);
    if(seconds<=0){end();return;}
    if(seconds<=300){show();const message='Tu sesión está por finalizar. ¿Quieres continuar? Al renovar, conservarás los datos que estás capturando.';if(text.textContent!==message)text.textContent=message;}
  }
  renew.addEventListener('click',async()=>{
    if(busy)return;busy=true;epoch++;renew.disabled=true;
    try{
      const res=await request('/sesion/continuar',{method:'POST',headers:{'X-CSRFToken':dialog.querySelector('[name=csrf_token]').value}});
      if(res.status===401){end();return;}
      if(!res.ok)throw Error();
      apply(await res.json());channel?.postMessage('renewed');close();
    }catch{text.textContent='No se pudo continuar la sesión. Comprueba la conexión y reintenta; si venció, vuelve a iniciar sesión.';}
    finally{busy=false;renew.disabled=false;}
  });
  dialog.addEventListener('cancel',e=>e.preventDefault());
  document.querySelectorAll('form[action="/logout"]').forEach(f=>f.addEventListener('submit',()=>channel?.postMessage('logout')));
  if(channel)channel.onmessage=e=>{if(e.data==='logout')end();else if(e.data==='renewed'){epoch++;sync();}};
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)sync();});
  window.addEventListener('pageshow',sync);
  setInterval(tick,1000);setInterval(sync,60000);sync();
})();
