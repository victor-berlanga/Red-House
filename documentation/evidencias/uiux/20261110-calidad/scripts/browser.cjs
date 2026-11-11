const {chromium}=require(process.cwd()+'/.local/gcp-public/browser/node_modules/playwright');
const fs=require('fs'),assert=require('assert');
const out='documentation/evidencias/uiux/20261110-calidad',root='http://127.0.0.1:15053';
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});let report={origin:'synthetic Jinja fixtures; no authenticated route',checks:[],comparisons:[]};try{
for(const phase of ['before','after']) for(const family of ['campaigns','alerts','documents','login','operations']) {
 await page.goto(`${root}/${phase}/DONOR-${family}.html`,{waitUntil:'networkidle'});
 await page.screenshot({path:`${out}/${phase}-${family}-1440.png`,fullPage:false});
 if(['campaigns','alerts'].includes(family))report.comparisons.push({phase,family,viewport:[1440,1000],...await page.evaluate(()=>({visibleRows:[...document.querySelectorAll('tbody>tr')].filter(x=>{const r=x.getBoundingClientRect();return r.top>=0 && r.bottom<=innerHeight}).length,rowHeight:document.querySelector('tbody>tr')?.getBoundingClientRect().height}))});
}
for(const role of ['DONOR','OPERATOR','MEDICAL','COORDINATOR','TRANSPORT','ADMIN','AUDITOR'])for(const width of [1440,1024,768,390,320])for(const family of ['campaigns','alerts','documents','login','operations','workspace','label','decision']){
 await page.setViewportSize({width,height:1000});await page.goto(`${root}/after/${role}-${family}.html`,{waitUntil:'domcontentloaded'});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
 report.checks.push({role,width,family,overflow});
 if(role==='DONOR' && [320,390,768].includes(width) && ['alerts','documents','login','operations'].includes(family))await page.screenshot({path:`${out}/after-${family}-${width}.png`,fullPage:true});
}
await page.setViewportSize({width:1440,height:1000});await page.goto(`${root}/after/OPERATOR-operations.html`);
const trigger=page.locator('.row-action-menu summary').first();await trigger.focus();await page.locator('[role=tooltip]').waitFor();await page.keyboard.press('Enter');await page.locator('.row-action-menu[open]').waitFor();await page.keyboard.press('Escape');assert(await trigger.evaluate(x=>x===document.activeElement));assert.equal(await page.locator('.row-action-menu[open]').count(),0);report.keyboardMenu=true;
const eye=page.locator('[data-record-view]').first();await eye.focus();assert((await page.locator('[role=tooltip]').textContent()).includes('Vista rápida'));await eye.click();await page.locator('#record-dialog[open]').waitFor();await page.keyboard.press('Escape');assert(await eye.evaluate(x=>x===document.activeElement));report.dialogFocus=true;
await page.goto(`${root}/after/DONOR-alerts.html`);assert.equal(await page.locator('a:has-text("Abrir expediente")').count(),0);assert.equal(await page.locator('.record-link').count(),20);assert.equal(await page.locator('form.inline-action[method=post] input[name=csrf_token]').count(),20);assert.equal(await page.locator('form.inline-action input[name=idempotency_key]').count(),20);report.postPreserved=true;
await page.goto(`${root}/after/DONOR-login.html`);report.brokenAria=await page.evaluate(()=>[...document.querySelectorAll('[aria-describedby]')].flatMap(x=>x.getAttribute('aria-describedby').split(/\s+/).filter(id=>!document.getElementById(id))));assert.equal(report.brokenAria.length,0);
report.overflow=report.checks.filter(x=>x.overflow);report.result=report.overflow.length?'needs-review':'passed';
} catch(e){report.error=e.stack;report.result='failed';}finally{fs.writeFileSync(out+'/chrome.json',JSON.stringify(report,null,2));console.log(JSON.stringify({result:report.result,error:report.error,comparisons:report.comparisons,overflow:report.overflow}));await browser.close();}})();
