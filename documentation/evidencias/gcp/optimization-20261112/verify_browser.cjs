const {chromium}=require(process.cwd()+'/.local/gcp-public/browser/node_modules/playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const base='https://34.18.186.116',out='.local/deploy-optimization-20261112';
const password=JSON.parse(fs.readFileSync('.local/password-maintenance-20261111/remote-input.json')).password;
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const report={at:new Date().toISOString(),origin:base,pages:[],errors:[],businessWrites:false};
 try{
  for(const user of ['auditor1','donor1','operator1']){
   const context=await browser.newContext({viewport:{width:1440,height:1000}});
   const page=await context.newPage();let authenticated=false;
   page.on('pageerror',e=>report.errors.push({user,message:e.message}));
   try{
    const login=await page.goto(base+'/login');assert.equal(login.status(),200);
    report.tls=await login.securityDetails();
    await page.locator('#login_email').fill(user);await page.locator('#password').fill(password);
    await Promise.all([page.waitForURL('**/panel',{timeout:45000}),page.locator('button[type=submit]').click()]);
    authenticated=true;
    for(const route of user==='auditor1'?['/monitoreo']:['/panel']){
     for(const width of [1440,390]){
      await page.setViewportSize({width,height:1000});
      const start=Date.now();const response=await page.goto(base+route,{waitUntil:'networkidle'});
      assert.equal(response.status(),200,user+' '+route);
      const details=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,
       chartScripts:[...document.scripts].map(s=>s.src).filter(s=>/highcharts|charts\.js/.test(s)),
       chartRequests:performance.getEntriesByType('resource').filter(s=>/highcharts|charts\.js/.test(s.name)).length,
       charts:document.querySelectorAll('.highcharts-container').length}));
      assert(!details.overflow,user+' '+route+' overflow');
      if(user==='donor1'){assert.equal(details.chartScripts.length,0);assert.equal(details.chartRequests,0);}
      if(user==='operator1'){assert(details.chartScripts.length>0);assert(details.charts>0);}
      report.pages.push({user,route,width,status:response.status(),navigationMs:Date.now()-start,...details});
     }
    }
   }finally{
    if(authenticated){
     await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/panel');
     await page.locator('.sidebar-footer button[aria-label="Cerrar sesión"]').click();await page.waitForURL('**/login');
     const status=await context.request.get(base+'/sesion/estado');assert.equal(status.status(),401);
     report.pages.push({user,logout:true,sessionHttp:status.status()});
    }
    await context.close();
   }
  }
  assert.equal(report.errors.length,0);report.result='passed';
 }catch(error){report.result='failed';report.failure=error.message;process.exitCode=1;}
 finally{
  fs.writeFileSync(out+'/browser-after.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({result:report.result,failure:report.failure,pages:report.pages.length,errors:report.errors.length}));
  await browser.close();
 }
})();
