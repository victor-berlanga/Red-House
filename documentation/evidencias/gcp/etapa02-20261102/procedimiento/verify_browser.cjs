'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require(path.resolve('.local/gcp-public/browser/node_modules/playwright'));
const input=JSON.parse(fs.readFileSync(0,'utf8'));
assert.equal(input.base,'https://34.18.186.116');
const report={passed:false,checks:[],consoleErrors:[],networkErrors:[],screenshots:false,video:false};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function otp(secret){let bits='';for(const c of secret.replace(/=/g,''))bits+='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5,'0');const bytes=[];for(let i=0;i+8<=bits.length;i+=8)bytes.push(parseInt(bits.slice(i,i+8),2));const count=Buffer.alloc(8);count.writeBigUInt64BE(BigInt(Math.floor(Date.now()/30000)));const h=crypto.createHmac('sha1',Buffer.from(bytes)).update(count).digest();return ((h.readUInt32BE(h[19]&15)&0x7fffffff)%1000000).toString().padStart(6,'0');}
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();page.setDefaultTimeout(90000);page.on('pageerror',e=>report.consoleErrors.push(e.message));page.on('response',r=>{if(r.status()>=400)report.networkErrors.push({path:new URL(r.url()).pathname,status:r.status()});});
 await page.goto(input.base+'/login');await pause(30500-Date.now()%30000);await page.locator('#login_email').fill('medical1');await page.locator('#password').fill(input.password);await page.locator('#otp').fill(otp(input.accounts.origin.secret));await Promise.all([page.waitForURL('**/panel'),page.locator('main form button[type=submit]').click()]);assert.ok((await context.cookies()).every(c=>c.secure));report.checks.push('HTTPS válido, MFA y cookie Secure');
 for(const [url,expected] of [
 ['/apoyo-decisiones','cuatro niveles'],
 ['/apoyo-decisiones/fuentes','3.66.0'],
 ['/laboratorio/resultados/'+input.stage02.result,'HLA00001'],
 ['/laboratorio/muestras/'+input.stage02.sample+'/completitud','Completitud'],
 ['/apoyo-decisiones/'+input.stage02.run,'REGIONAL-OSM-DIJKSTRA-3.0'],
 ['/laboratorio/perfiles','Comprobación académica GCP'],
 ['/apoyo-decisiones/importar-rutas','Nuevo León']]){
  const response=await page.goto(input.base+url);assert.equal(response.status(),200,url);assert.ok((await page.locator('main').innerText()).includes(expected),url+' expected '+expected);assert.equal((await page.reload()).status(),200);report.checks.push(url);
 }
 assert.equal(report.consoleErrors.length,0);assert.equal(report.networkErrors.length,0);report.passed=true;
 }catch(e){report.failure=e.message;}finally{await browser.close();fs.writeFileSync(path.join(input.output,'browser-final.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,failure:report.failure}));if(!report.passed)process.exitCode=1;}})();
