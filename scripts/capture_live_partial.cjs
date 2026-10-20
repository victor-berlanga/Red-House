'use strict';
// Browser evidence with fictitious Compose accounts. Never writes credentials.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {chromium} = require('playwright');
const state = JSON.parse(fs.readFileSync('.local/compose/state.json'));
const output = 'documentation/evidencias/segundo-parcial/browser';
fs.mkdirSync(output,{recursive:true});
const base='http://127.0.0.1:6050';
const filesOnly=process.argv.includes('--files-only');
const report=filesOnly?JSON.parse(fs.readFileSync(path.join(output,'browser-results.json'))):{date:new Date().toISOString(),pages:[],errors:[],checks:[]};
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try {
  async function login(user,width=1440){
   const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
   const page=await context.newPage(); page.on('pageerror',e=>report.errors.push(e.message));
   await page.goto(base+'/login');
   if(user==='operator1')await page.screenshot({path:path.join(output,'login.png')});
   await page.locator('#login_email').fill(user);await page.locator('#password').fill(state.password);
   await Promise.all([page.waitForURL('**/panel'),page.locator('button[type=submit]').click()]);
   return {context,page};
  }
  async function checkCharts(page,user){
   const result=await page.evaluate(()=>({loaded:Boolean(window.Highcharts),charts:
    [...document.querySelectorAll('[data-chart-values]')].map(node=>{
     const expected=JSON.parse(node.dataset.chartValues),chart=window.Highcharts?.charts[Number(node.dataset.highchartsChart)];
     return {title:node.dataset.chartTitle,expected,values:chart?.series[0].data.map(point=>point.y)||[],labels:chart?.xAxis[0].categories||[]};
    })}));
   assert.ok(result.loaded);
   for(const chart of result.charts){
    assert.deepEqual(chart.values,chart.expected.map(item=>item.value));
    assert.deepEqual(chart.labels,chart.expected.map(item=>item.label));
   }
   report.checks.push({user,highcharts:true,charts:result.charts,date:new Date().toISOString()});
  }
  if(!filesOnly){
  const pages={admin1:['/panel','/administracion/users','/catalogos/sites'],operator1:['/panel','/inventario','/donaciones'],
   medical2:['/panel','/solicitudes','/donantes/recipient'],coordinator1:['/panel','/disponibilidad','/traslados','/rutas'],
   transport1:['/panel','/traslados'],auditor1:['/panel','/auditoria'],donor1:['/panel','/campanas','/citas']};
  for(const [user,routes] of Object.entries(pages)){
   const {context,page}=await login(user);
   for(const route of routes){
    const response=await page.goto(base+route,{waitUntil:'networkidle'});
    assert.equal(response.status(),200,`${user} ${route}`);
    const file=user+route.replaceAll('/','-')+'.png';await page.screenshot({path:path.join(output,file)});
    report.pages.push({user,route,status:response.status(),capture:file});
    if(route==='/panel')await checkCharts(page,user);
   }
   await context.close();
  }
  const mobile=await login('operator1',390);
  await mobile.page.goto(base+'/inventario',{waitUntil:'networkidle'});
  assert.ok(await mobile.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await mobile.page.screenshot({path:path.join(output,'inventory-mobile.png')});
  report.checks.push({responsive_width:390,horizontal_overflow:false});await mobile.context.close();
  }

  const shipment=execFileSync('docker',['compose','exec','-T','postgres','psql','-U','rh_bootstrap','-d','red_house','-qAt','-c',
   "SELECT id FROM access_transporte.shipments WHERE origin_id='"+state.tenants[0]+"' AND status NOT IN ('ACCEPTED','CANCELLED','REJECTED') AND NOT inventory_pending ORDER BY id LIMIT 1"],{encoding:'utf8'}).trim();
  assert.match(shipment,/^[0-9a-f-]{36}$/, 'Ejecuta primero deployment/prepare_browser_demo.py para disponer de un traslado abierto.');
  const files=await login('operator1');
  if(filesOnly)await checkCharts(files.page,'operator1');
  const fileResponse=await files.page.goto(base+'/traslados/'+shipment+'/archivos');
  assert.equal(fileResponse.status(),200);
  await files.page.locator('input[type=file]').setInputFiles({name:'evidence.png',mimeType:'image/png',
   buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEklEQVR4nGP8z4AdMOEQH6QSAM1BAQ/oQeJvAAAAAElFTkSuQmCC','base64')});
  await Promise.all([files.page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/archivos')),
    files.page.getByRole('button',{name:'Cargar y verificar',exact:true}).click()]);
  await files.page.getByText('Verificado',{exact:false}).first().waitFor();
  await files.page.screenshot({path:path.join(output,'gcs-web-verified.png')});
  report.checks.push({web_gcs_upload:'VERIFIED',shipment,date:new Date().toISOString()});await files.context.close();

  const context=await browser.newContext();const page=await context.newPage();
  const loginResponse=await context.request.post('http://127.0.0.1:6101/api/v1/auth/login',{data:{username:'operator1',password:state.password}});
  assert.equal(loginResponse.status(),200);const token=(await loginResponse.json()).data.access_token;
  await page.goto('http://127.0.0.1:6104/docs/');
  const security=Object.keys(JSON.parse(fs.readFileSync('apps/services/ms_inventario/contracts/openapi.json')).components.securitySchemes)[0];
  await page.waitForFunction(()=>Boolean(window.ui));await page.evaluate(([scheme,value])=>window.ui.preauthorizeApiKey(scheme,value),[security,token]);
  const operation=page.locator('.opblock-get').filter({has:page.locator('.opblock-summary-path').getByText('/api/v1/resources',{exact:true})});
  await operation.locator('.opblock-summary').click();await operation.getByRole('button',{name:'Try it out',exact:true}).click();
  const responsePromise=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/resources');
  await operation.getByRole('button',{name:'Execute',exact:true}).click();const response=await responsePromise;
  assert.equal(response.status(),200);
  const headers=await response.request().allHeaders();if(headers.authorization)headers.authorization='[REDACTED]';
  report.swagger={url:response.url(),method:response.request().method(),headers,status:response.status(),body:await response.json()};
  await operation.locator('.responses-wrapper').waitFor();
  await page.evaluate(()=>{const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(walker.nextNode())walker.currentNode.textContent=walker.currentNode.textContent.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g,'[REDACTED JWT]');});
  await operation.screenshot({path:path.join(output,'swagger-executed.png')});await context.close();
  assert.deepEqual(report.errors,[]);report.status="passed";delete report.failure;report.completed_at=new Date().toISOString();
 } catch(error) {report.status="failed";report.failure=error.message;throw error;
 } finally {await browser.close();fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify(report,null,2)+'\n');}
 console.log(JSON.stringify({pages:report.pages.length,checks:report.checks.length,errors:report.errors.length}));
})().catch(error=>{console.error(error.message);process.exitCode=1;});
