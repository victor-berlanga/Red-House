/* NODE_PATH debe proporcionar playwright y mermaid. Solo sirve recursos temporales en localhost. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../report-assets/diagrams');
const dist=path.dirname(require.resolve('mermaid'));
(async()=>{
 const server=http.createServer((req,res)=>{
   const rel=decodeURIComponent(req.url.split('?')[0]).replace(/^\//,'');
   if(!rel){res.setHeader('Content-Type','text/html');res.end('<!doctype html><html><body></body></html>');return;}
   const file=path.resolve(dist,rel);
   if(!file.startsWith(dist+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
   res.setHeader('Content-Type',file.endsWith('.mjs')||file.endsWith('.js')?'text/javascript':'application/octet-stream');
   res.setHeader('Access-Control-Allow-Origin','*');res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try{
   browser=await chromium.launch({channel:'chrome',headless:true});
   const page=await browser.newPage({viewport:{width:1600,height:1200},deviceScaleFactor:2});
   const url=`http://127.0.0.1:${server.address().port}/mermaid.esm.min.mjs`;
   await page.goto(`http://127.0.0.1:${server.address().port}/`);
   await page.evaluate(async url=>{window.mermaid=(await import(url)).default;window.mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',themeVariables:{fontFamily:'Arial',fontSize:'20px',primaryColor:'#f1f5f9',primaryTextColor:'#0f172a',primaryBorderColor:'#64748b',lineColor:'#64748b'},flowchart:{useMaxWidth:false},sequence:{useMaxWidth:false}});},url);
   let index=0;
   for(const name of fs.readdirSync(root).filter(n=>n.endsWith('.mmd')).sort()){
     const code=fs.readFileSync(path.join(root,name),'utf8');
     const svg=await page.evaluate(async({code,index})=>(await window.mermaid.render('d'+index,code)).svg,{code,index:++index});
     fs.writeFileSync(path.join(root,name.replace('.mmd','.svg')),svg);
     await page.evaluate(svg=>{document.body.style='margin:0;background:white';document.body.innerHTML='<div id="figure" style="display:inline-block;padding:24px;background:white">'+svg+'</div>';},svg);
     await page.locator('#figure').screenshot({path:path.join(root,name.replace('.mmd','.png'))});
   }
   console.log(JSON.stringify({result:'PASS',diagrams:index,formats:['mmd','svg','png']}));
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exit(1);});
