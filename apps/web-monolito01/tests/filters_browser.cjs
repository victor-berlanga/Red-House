const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const base = process.env.BASE_URL, output = process.env.BROWSER_ARTIFACTS;
  fs.mkdirSync(output,{recursive:true});
  const errors=[], pages={};
  async function login(role, options={}) {
    const context = await browser.newContext({viewport:{width:1440,height:1000},...options});
    const p = await context.newPage();
    p.on('pageerror',e=>errors.push(e.message));
    await p.goto(base+'/login');
    await p.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');
    await p.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);
    await p.getByRole('button',{name:'Iniciar sesión'}).click();
    await p.waitForURL(url=>url.pathname!=='/login');
    pages[role]=p;
    return p;
  }
  async function ready(p,route) {
    await p.goto(base+route);
    await p.locator('form.live-filters-enabled').waitFor();
    await p.evaluate(()=>window.filterDocumentMarker='preserved');
  }
  async function applied(p,key,value) {
    await p.waitForFunction(({key,value})=>
      (new URL(location.href).searchParams.get(key)||'')===value &&
      document.querySelector('[data-filter-results]').getAttribute('aria-busy')==='false' &&
      /^\d+ resultados?$/.test(document.querySelector('.filter-feedback [role=status]').textContent),{key,value});
    assert.equal(await p.evaluate(()=>window.filterDocumentMarker),'preserved','No recarga de documento');
  }
  async function count(p) {return Number(await p.locator('[data-filter-results]').getAttribute('data-result-count'));}
  async function clear(p) {
    await p.locator('form[data-live-filter] [data-filter-clear]').click();
    await applied(p,'q','');
    assert.equal(new URL(p.url()).search,'');
  }
  async function screenshot(p,name) {await p.screenshot({path:path.join(output,name+'.png'),fullPage:true});}

  try {
    const op=await login('operador');
    await ready(op,'/inventario');
    assert(await op.getByRole('button',{name:'Filtrar',exact:true}).isHidden());
    const requests=[];
    op.on('request',r=>{if(r.resourceType()==='fetch')requests.push(new URL(r.url()));});
    const initialCount=await count(op);
    assert(initialCount>12);
    await op.locator('[data-filter-results] .pagination').getByRole('link',{name:'Siguiente'}).click();
    await applied(op,'page','2');
    const before=requests.length;
    await op.locator('#q').pressSequentially('UNIT-01',{delay:20});
    await applied(op,'q','UNIT-01');
    assert.equal(requests.length-before,1,'Una consulta tras terminar de escribir');
    assert.equal(new URL(op.url()).searchParams.has('page'),false,'Filtros reinician página');
    assert.equal(await count(op),1);
    assert.equal(await op.locator('[data-filter-summary] strong').first().innerText(),'1');
    assert(await op.locator('#q').evaluate(el=>el===document.activeElement));
    await op.locator('#recorded_group_code').selectOption('A+');
    await applied(op,'recorded_group_code','A+');
    assert.equal(await count(op),0,'Combinación de filtros y estado vacío');
    await screenshot(op,'Inventario_sin_coincidencias');
    await op.goBack();
    await applied(op,'recorded_group_code','');
    assert.equal(await count(op),1);
    assert.equal(await op.locator('#recorded_group_code').inputValue(),'');
    await clear(op);
    assert.equal(await count(op),initialCount);

    // Una respuesta lenta no debe reemplazar el criterio más reciente.
    let release, started;
    const held=new Promise(resolve=>{release=resolve;});
    const intercepted=new Promise(resolve=>{started=resolve;});
    const slow=async route=>{
      const response=await route.fetch();started();await held;
      try {await route.fulfill({response});} catch {} // El navegador puede cancelar el transporte.
    };
    await op.route('**/inventario?q=UNIT-01',slow);
    await op.locator('#q').fill('UNIT-01');await intercepted;
    await op.locator('#q').fill('SIN-RESULTADOS');
    await applied(op,'q','SIN-RESULTADOS');release();
    await op.unroute('**/inventario?q=UNIT-01',slow);
    assert.equal(await count(op),0);
    await clear(op);

    const fail=route=>route.abort('failed');
    await op.route('**/inventario?q=UNIT-01',fail);
    await op.locator('#q').fill('UNIT-01');
    await op.getByRole('button',{name:'Reintentar'}).waitFor();
    assert.equal(await count(op),initialCount,'Error conserva resultados anteriores');
    assert((await op.locator('.filter-feedback').innerText()).includes('resultados anteriores'));
    await screenshot(op,'Error_y_reintento');
    await op.unroute('**/inventario?q=UNIT-01',fail);
    await op.getByRole('button',{name:'Reintentar'}).click();
    await applied(op,'q','UNIT-01');assert.equal(await count(op),1);
    await screenshot(op,'Inventario_filtrado');

    await ready(op,'/sangre/personas/donor');
    await op.locator('form[method=post] [name=display_name]').fill('Borrador sin guardar');
    await op.locator('#search-q').fill('SIN-RESULTADOS');await applied(op,'q','SIN-RESULTADOS');
    assert.equal(await count(op),0);
    assert.equal(await op.locator('form[method=post] [name=display_name]').inputValue(),'Borrador sin guardar');
    await clear(op);assert.equal(await count(op),1);
    await op.setViewportSize({width:390,height:844});
    await op.locator('#search-q').fill('DON-01');await applied(op,'q','DON-01');
    assert(await op.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await screenshot(op,'Donantes_mobile');

    const med=await login('medico.valle');
    for(const [route,term] of [['/sangre/personas/recipient','REC-01'],['/sangre/solicitudes','SOL-01']]) {
      await ready(med,route);
      await med.locator('#search-q').fill('SIN-RESULTADOS');await applied(med,'q','SIN-RESULTADOS');
      assert.equal(await count(med),0);
      await med.locator('#search-q').fill(term);await applied(med,'q',term);
      assert.equal(await count(med),1);
    }
    const admin=await login('admin');
    for(const entity of ['institutions','sites','locations','components','users']) {
      await ready(admin,'/administracion/'+entity);
      assert(await count(admin)>0);
      await admin.locator('#q').fill('SIN-RESULTADOS');await applied(admin,'q','SIN-RESULTADOS');
      assert.equal(await count(admin),0);
      await clear(admin);assert(await count(admin)>0);
      await admin.locator('#state').selectOption('INACTIVE');await applied(admin,'state','INACTIVE');
      assert.equal(await count(admin),0);
    }
    await screenshot(admin,'Usuarios_filtrados');
    const auditor=await login('auditor');
    await ready(auditor,'/auditoria');
    await auditor.locator('#q').fill('SENSITIVE_READ');await applied(auditor,'q','SENSITIVE_READ');
    await auditor.locator('#outcome').selectOption('SUCCESS');await applied(auditor,'outcome','SUCCESS');
    await auditor.locator('#date').fill('2000-01-01');await applied(auditor,'date','2000-01-01');
    assert.equal(await count(auditor),0);
    await screenshot(auditor,'Auditoria_filtrada');

    // Sesión vencida: navegar al acceso, sin insertar la página de login como tabla.
    await ready(med,'/sangre/personas/recipient');
    await med.context().clearCookies();
    await med.locator('#search-q').fill('REC');await med.waitForURL('**/login');
    assert.equal(await med.locator('[data-filter-results]').count(),0);

    const basic=await login('operador',{javaScriptEnabled:false});
    await basic.goto(base+'/inventario');
    await basic.locator('#q').fill('UNIT-01');
    await basic.getByRole('button',{name:'Filtrar',exact:true}).click();
    await basic.waitForURL(url=>url.searchParams.get('q')==='UNIT-01');
    assert.equal(await count(basic),1,'GET convencional sin JavaScript');
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'Browser_results.json'),JSON.stringify({result:'PASS',sections:10,
      debounce:true,pagination:true,counters:true,history:true,staleResponse:true,networkRetry:true,
      unsavedFormPreserved:true,mobile:true,sessionExpired:true,noJavascript:true,errors},null,2)+'\n');
    console.log('PASS: filtros automáticos en diez secciones y escenarios de recuperación.');
  } catch(error) {
    for(const [role,p] of Object.entries(pages)) {
      await p.screenshot({path:path.join(output,role+'-failure.png'),fullPage:true,animations:'disabled'});
      const state=await p.evaluate(()=>({width:innerWidth,scroll:scrollY,documentWidth:document.documentElement.scrollWidth,clear:Array.from(document.querySelectorAll('[data-filter-clear]')).map(e=>({rect:e.getBoundingClientRect().toJSON(),hidden:e.hidden,inert:!!e.closest('[inert]'),display:getComputedStyle(e).display})),bodyClass:document.body.className}));
      console.error(role,JSON.stringify(state));
    }
    throw error;
  } finally {
    // Cerrar cada contexto antes del proceso evita dejar páginas/interceptores pendientes.
    await Promise.all(browser.contexts().map(context=>context.close()));
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exit(1);});
