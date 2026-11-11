'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(path.resolve('.local/gcp-public/browser/node_modules/playwright'));
const input=JSON.parse(fs.readFileSync(0,'utf8'));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});const result=[];const out='documentation/evidencias/gcp/portal03-20261106/layout';fs.mkdirSync(out,{recursive:true});try{
 await page.goto(input.base+'/login');await page.locator('#login_email').fill('operator1');await page.locator('#password').fill(input.password);await Promise.all([page.waitForURL('**/panel'),page.locator('main form button[type=submit]').click()]);
 const response=await page.goto(input.base+'/campanas/1d626159-b312-4e54-b935-89fbad1ef455/horarios');assert.equal(response.status(),200);
 for(const width of [390,768,1440]){await page.setViewportSize({width,height:1000});const instant=await page.evaluate(()=>({inner:innerWidth,scroll:document.documentElement.scrollWidth}));await page.waitForTimeout(600);
  const settled=await page.evaluate(()=>({inner:innerWidth,scroll:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>innerWidth+1||r.left < -1);}).slice(0,20).map(e=>({tag:e.tagName,className:e.className,right:Math.round(e.getBoundingClientRect().right),width:Math.round(e.getBoundingClientRect().width)}))}));
  result.push({width,instant,settled,passed:settled.scroll<=settled.inner+1});await page.screenshot({path:path.join(out,width+'.png'),fullPage:true});
 }
 fs.writeFileSync(path.join(out,'layout.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));if(result.some(r=>!r.passed))process.exitCode=1;
 }finally{await browser.close();}})();
