/* Playwright es una herramienta de pruebas externa, no una dependencia de la aplicación. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({channel:'chrome', headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const page = await context.newPage();
  const root = process.env.BASE_URL;
  const output = process.env.BROWSER_ARTIFACTS;
  fs.mkdirSync(output,{recursive:true});
  const failures = [];
  const badAssets = [];
  page.on('pageerror',error => failures.push(error.message));
  page.on('response',response => { if(response.url().includes('/static/') && response.status() >= 400) badAssets.push(response.url()); });
  async function capture(name) { await page.screenshot({path:path.join(output,name+'.png'),fullPage:true,animations:'disabled'}); }
  async function login(role) {
    await page.goto(root+'/login');
    await page.getByLabel('Correo electrónico',{exact:true}).fill(role+'@red-house.test');
    await page.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);
    await page.getByRole('button',{name:'Iniciar sesión'}).click();
    await page.waitForURL('**/panel');
  }
  async function noOverflow(label) {
    const dimensions=await page.evaluate(()=>({viewport:innerWidth,content:document.documentElement.scrollWidth}));
    if (dimensions.content > dimensions.viewport+1) {
      await capture('overflow-debug');
      console.log(await page.evaluate(()=>[...document.querySelectorAll('body *')].map(el=>({tag:el.tagName,classes:el.className,width:el.getBoundingClientRect().width,right:el.getBoundingClientRect().right,position:getComputedStyle(el).position})).filter(item=>item.right>innerWidth+1).slice(0,12)));
    }
    assert(dimensions.content <= dimensions.viewport+1, label+': horizontal page overflow '+JSON.stringify(dimensions));
  }
  try {
    await page.goto(root+'/'); await capture('public-desktop'); await noOverflow('public desktop');
    await page.goto(root+'/login'); await capture('login-desktop');
    await login('operador');
    await page.locator('.highcharts-root').waitFor();
    const chartLoaded = await page.locator('.highcharts-root').count() > 0;
    assert(chartLoaded, 'Highcharts must render with the local assets');
    assert(await page.getByRole('table',{name:'Datos de la gráfica'}).isVisible());
    await capture('dashboard-desktop');
    await page.goto(root+'/inventario'); await capture('inventory-desktop');
    await page.getByRole('link',{name:'Registrar unidad',exact:true}).click();
    await page.getByLabel('Folio de trazabilidad DEMO').fill('RH-BROWSER-001');
    await page.getByLabel('Componente sanguíneo').selectOption({index:1});
    await page.getByLabel('Ubicación institucional').selectOption({index:1});
    await page.getByLabel('Grupo registrado (dato ficticio)').selectOption('A+');
    await page.getByLabel('Referencia ficticia del grupo').fill('SOURCE-BROWSER-DEMO');
    await page.getByLabel('Estado inicial DEMO').selectOption('AVAILABLE');
    const time = Date.now();
    await page.getByLabel('Recolección (UTC)').fill(new Date(time-3600000).toISOString().slice(0,16));
    await page.getByLabel('Caducidad (UTC)').fill(new Date(time+86400000).toISOString().slice(0,16));
    await page.getByLabel('Motivo del registro').fill('Alta ficticia desde navegador');
    await page.getByRole('button',{name:'Guardar unidad',exact:true}).click();
    await page.getByRole('heading',{name:'RH-BROWSER-001',exact:true}).waitFor();
    await page.getByLabel('Estado DEMO',{exact:false}).selectOption('QUARANTINED');
    await page.getByLabel('Motivo *',{exact:true}).fill('Cambio ficticio de estado desde navegador');
    await page.getByRole('button',{name:'Guardar movimiento'}).click();
    await page.getByText('Movimiento guardado con trazabilidad y auditoría.').waitFor();
    await capture('unit-detail-desktop');
    await page.reload();
    assert(await page.getByText('Cambio ficticio de estado desde navegador').isVisible());
    await page.goto(root+'/proximamente/compatibilidad'); await capture('future-desktop');
    assert(await page.getByRole('button',{name:'Evaluar candidatos',exact:true}).isDisabled());
    await page.setViewportSize({width:390,height:844});
    for(const route of ['/panel','/inventario','/proximamente/compatibilidad']) {
      await page.goto(root+route); await noOverflow(route+' mobile');
    }
    await capture('future-mobile');
    await page.goto(root+'/inventario');
    await page.getByRole('button',{name:'Abrir menú'}).click();
    assert(await page.getByRole('link',{name:'Panel principal',exact:true}).isVisible());
    await capture('navigation-mobile');
    await page.keyboard.press('Escape');
    assert.equal(await page.getByRole('button',{name:'Abrir menú'}).getAttribute('aria-expanded'),'false');
    await capture('inventory-mobile');
    await page.setViewportSize({width:1440,height:1000});
    await page.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
    await login('admin');
    await page.goto(root+'/administracion/institutions'); await capture('institutions-desktop');
    await page.getByRole('link',{name:'Nuevo registro'}).click();
    await page.getByLabel('Código institucional').fill('BROWSER-INST');
    await page.getByLabel('Nombre de la institución').fill('Institución navegador DEMO');
    await page.getByLabel('Tipo',{exact:false}).selectOption('HOSPITAL');
    await page.getByLabel('Participación').selectOption('ACTIVE');
    await page.getByLabel('Ciudad',{exact:false}).fill('Ciudad sintética');
    await page.getByLabel('Dirección',{exact:false}).fill('Calle ficticia 10');
    await page.getByRole('button',{name:'Guardar cambios'}).click();
    await page.getByRole('heading',{name:'Institución navegador DEMO',exact:true}).waitFor();
    await page.goto(root+'/administracion/configuracion/parametros'); await capture('settings-desktop');
    await page.setViewportSize({width:390,height:844});
    await page.goto(root+'/administracion/users/nuevo'); await noOverflow('admin form mobile'); await capture('admin-form-mobile');
    await page.setViewportSize({width:1440,height:1000});
    await page.getByRole('button',{name:'Cerrar sesión',exact:true}).click();
    await login('auditor');
    await page.goto(root+'/auditoria'); await capture('audit-desktop');
    await page.getByLabel('Buscar evento').fill('MOVE');
    await page.getByRole('button',{name:'Filtrar'}).click();
    assert(await page.getByText('MOVE',{exact:true}).count() > 0);
    await page.setViewportSize({width:390,height:844}); await noOverflow('audit mobile');
    await page.goto(root+'/login'); await noOverflow('login mobile'); await capture('login-mobile');
    await page.goto(root+'/'); await noOverflow('public mobile'); await capture('public-mobile');
    assert.deepEqual(failures,[], 'Browser exceptions');
    assert.deepEqual(badAssets,[], 'Missing local assets');
    console.log(JSON.stringify({result:'PASS', chartLoaded, screenshots:output, browserErrors:failures.length, missingAssets:badAssets.length}));
  } finally { await browser.close(); }
})().catch(error=>{ console.error(error); process.exit(1); });
