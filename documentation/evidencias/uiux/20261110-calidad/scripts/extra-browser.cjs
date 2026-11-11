const {chromium}=require(process.cwd()+'/.local/gcp-public/browser/node_modules/playwright'),fs=require('fs'),assert=require('assert');
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true}),p=await b.newPage(),out='documentation/evidencias/uiux/20261110-calidad',r={fixtures:true,checks:[]};try{
for(const family of ['conservation','lineage','evaluation','form','upload','detail','empty','error'])for(const width of [1440,768,320]){
await p.setViewportSize({width,height:1000});let res=await p.goto('http://127.0.0.1:15053/after/custom-'+family+'.html');assert.equal(res.status(),200);
r.checks.push({family,width,overflow:await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)});
await p.screenshot({path:`${out}/custom-${family}-${width}.png`,fullPage:true});}
await p.goto('http://127.0.0.1:15053/after/custom-conservation.html');const eye=p.locator('[data-row-preview]').first();await eye.click();await p.locator('#record-dialog[open]').waitFor();await p.keyboard.press('Escape');assert(await eye.evaluate(e=>e===document.activeElement));r.historyPreviewFocus=true;
for(const family of ['alerts','documents','login','operations']){
await p.setViewportSize({width:1024,height:1000});await p.goto('http://127.0.0.1:15053/after/DONOR-'+family+'.html');
await p.evaluate(()=>{const nodes=[...document.querySelectorAll('h1,h2,h3,p,a,button,label,small,span,td,th,input,select,summary')];const sizes=nodes.map(n=>parseFloat(getComputedStyle(n).fontSize));nodes.forEach((n,i)=>n.style.fontSize=(sizes[i]*2)+'px')});
r.checks.push({family,width:1024,textScale:'200% CSS text-only simulation',overflow:await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)});await p.screenshot({path:`${out}/text200-${family}.png`,fullPage:true});}
r.result=r.checks.some(x=>x.overflow)?'needs-review':'passed';
}catch(e){r.error=e.stack;r.result='failed'}finally{fs.writeFileSync(out+'/extra-browser.json',JSON.stringify(r,null,2));console.log(JSON.stringify(r));await b.close()}})();
