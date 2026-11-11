const {chromium}=require(process.cwd()+'/.local/gcp-public/browser/node_modules/playwright');
const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const base='https://34.18.186.116',out='documentation/evidencias/gcp/uiux-quality-20261110';
const phase=process.argv.includes('--before')?'before':'after';
const manifest=JSON.parse(fs.readFileSync('.local/deploy-uiux-quality-20261110/manifest.json'));
const state=JSON.parse(fs.readFileSync('.local/compose/state.json'));
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const report={phase,origin:base,date:new Date().toISOString(),checks:[],pages:[],errors:[],businessWrites:false};
 try {
  const p=await browser.newPage({viewport:{width:1440,height:1000}});
  const r=await p.goto(base+'/login',{waitUntil:'networkidle'});assert.equal(r.status(),200);
  report.tls=await r.securityDetails();await p.screenshot({path:`${out}/${phase}-login.png`});
  if(phase==='after'){
   for(const [name,sha] of Object.entries(manifest).filter(([n])=>n.includes('/static/'))){
    const url=base+'/static/'+name.split('/static/')[1];const a=await p.request.get(url);
    assert.equal(a.status(),200);assert.equal(crypto.createHash('sha256').update(await a.body()).digest('hex'),sha,name);
    report.checks.push({asset:name,sha256Matches:true,cacheControl:a.headers()['cache-control']});
   }
   assert.equal(await p.locator('#login_email[aria-describedby]').count(),0);
  }
  await p.close();
  for(const user of ['donor1','operator1']){
   const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();
   let authenticated=false;
   page.on('pageerror',e=>report.errors.push(e.message));
   try{
    await page.goto(base+'/login');await page.locator('#login_email').fill(user);await page.locator('#password').fill(state.password);
    await Promise.all([page.waitForURL('**/panel',{timeout:45000}),page.locator('button[type=submit]').click()]);authenticated=true;
    report.checks.push({user,login:true});
    const routes=user==='donor1'?['/campanas','/notificaciones','/documentos','/citas']:['/inventario','/traslados','/conservacion'];
    for(const route of routes){
     for(const width of (phase==='before'?[1440]:[1440,320])){
      await page.setViewportSize({width,height:1000});const response=await page.goto(base+route,{waitUntil:'networkidle'});assert.equal(response.status(),200,route);
      const measured=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,visibleRows:[...document.querySelectorAll('tbody>tr')].filter(n=>{const r=n.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight}).length,rowHeight:document.querySelector('tbody>tr')?.getBoundingClientRect().height,rows:document.querySelectorAll('tbody>tr').length}));
      assert(!measured.overflow,user+' '+route+' '+width+' overflow');
      const filename=`${phase}-${user}-${route.slice(1)}-${width}.png`;await page.screenshot({path:out+'/'+filename});
      report.pages.push({user,route,width,status:response.status(),capture:filename,...measured});
      if(phase==='after'&&width===1440&&['/campanas','/notificaciones','/inventario'].includes(route)){
       assert.equal(await page.locator('.record-actions a:has-text("Abrir expediente")').count(),0);
       const eye=page.locator('.record-actions [data-record-view]').first();
       if(await eye.count()){
        await eye.focus();await page.locator('[role=tooltip]').waitFor();await eye.click();await page.locator('#record-dialog[open]').waitFor();await page.keyboard.press('Escape');assert(await eye.evaluate(n=>document.activeElement===n));
        report.checks.push({user,route,quickViewAndFocus:true});
       }
       if(route==='/notificaciones'){
        const forms=page.locator('.record-actions form.inline-action');
        const count=await forms.count();assert(count>0);
        assert.equal(await forms.locator('input[name=csrf_token]').count(),count);assert.equal(await forms.locator('input[name=idempotency_key]').count(),count);
        report.checks.push({user,route,readActionPostPreserved:true,forms:count,submitted:false});
       }
       const link=page.locator('.record-link').first();
       if(await link.count()){
        const href=await link.getAttribute('href');const detail=await page.goto(new URL(href,base).href,{waitUntil:'networkidle'});assert.equal(detail.status(),200);assert.notEqual(new URL(page.url()).pathname,route);
        report.checks.push({user,route,directDetail:true});
       }
      }
      if(phase==='after'&&route==='/documentos'){
       const min=await page.locator('main select').evaluateAll(nodes=>Math.min(...nodes.map(n=>n.getBoundingClientRect().height)));
       assert(min>=43.9);report.checks.push({user,route,width,minimumSelectHeight:min});
      }
     }
    }
   }finally{
    if(authenticated){
     await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/panel');
     await page.locator('.sidebar-footer button[aria-label="Cerrar sesión"]').click();await page.waitForURL('**/login');
     report.checks.push({user,logout:true});
    }
    await context.close();
   }
  }
  assert.equal(report.errors.length,0);report.result='passed';
 }catch(error){report.result='failed';report.failure=error.message;process.exitCode=1;}
 finally{fs.writeFileSync(out+`/browser-${phase}.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({phase,result:report.result,failure:report.failure,pages:report.pages.length,errors:report.errors}));await browser.close();}
})();
