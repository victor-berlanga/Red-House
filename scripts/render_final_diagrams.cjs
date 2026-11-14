'use strict';
// Reutiliza el flujo Playwright/Mermaid del generador histórico, sin instalar CLI ni navegador.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const { chromium } = require(path.join(root, '.local/gcp-public/browser/node_modules/playwright'));
const directory = path.resolve(process.argv[2] || path.join(root, 'documentation/entrega-final/modelos/diagramas'));
const selectedSources = new Set(process.argv.slice(3));
const allowed = path.join(root, 'documentation/entrega-final') + path.sep;
if (!directory.startsWith(allowed)) throw new Error('Solo se renderizan destinos de entrega-final');
const bundle = process.env.REDHOUSE_MERMAID_BUNDLE || path.join(root, '.local/tools/clamav-1.5.4/package/clamav-1.5.4.macos.universal-documentation.pkg/Payload/usr/local/clamav/share/doc/ClamAV/html/mermaid-eefea253.min.js');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const bitmapNames = new Set(['componentes', 'despliegue', 'archivos', 'secuencia', 'datos', 'archivos-resumen', 'secuencia-resumen']);

(async () => {
  const library = fs.readFileSync(bundle);
  const server = http.createServer((request, response) => {
    if (request.url === '/') {
      response.setHeader('Content-Type', 'text/html');
      response.end('<!doctype html><html lang="es"><head><meta charset="utf-8"></head><body></body></html>');
    } else if (request.url === '/mermaid.js') {
      response.setHeader('Content-Type', 'text/javascript');
      response.end(library);
    } else {
      response.writeHead(404); response.end();
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  let browser;
  const report = { status: 'STARTED', bundle_sha256: digest(library), files: [], visual_review: false };
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const page = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1 });
    await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    await page.goto(origin);
    await page.addScriptTag({ url: origin + '/mermaid.js' });
    await page.evaluate(() => window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', maxTextSize: 500000, theme: 'base', themeVariables: { fontFamily: 'Arial', primaryColor: '#f1f5f9', primaryTextColor: '#0f172a', primaryBorderColor: '#64748b', lineColor: '#64748b' }, flowchart: { useMaxWidth: false }, sequence: { useMaxWidth: false } }));
    const names = fs.readdirSync(directory).filter(name => name.endsWith('.mmd') && (!selectedSources.size || selectedSources.has(name))).sort();
    if (!names.length) throw new Error('No hay fuentes Mermaid seleccionadas');
    for (const [index, name] of names.entries()) {
      const code = fs.readFileSync(path.join(directory, name), 'utf8');
      const svg = await page.evaluate(async ({ code, index }) => {
        await window.mermaid.parse(code);
        return (await window.mermaid.render('finalDiagram' + index, code)).svg;
      }, { code, index });
      fs.writeFileSync(path.join(directory, name.replace(/\.mmd$/, '.svg')), svg);
      const item = { source: name, source_sha256: digest(code), svg_sha256: digest(svg), png: false };
      if (bitmapNames.has(name.replace(/\.mmd$/, ''))) {
        await page.evaluate(svg => { document.body.style = 'margin:0;background:white'; document.body.innerHTML = '<div id="figure" style="display:inline-block;padding:24px;background:white">' + svg + '</div>'; }, svg);
        const figure = page.locator('#figure');
        const bounds = await figure.boundingBox();
        if (bounds && bounds.width * bounds.height <= 25000000) {
          await figure.screenshot({ path: path.join(directory, name.replace(/\.mmd$/, '.png')) });
          item.png = true;
        }
      }
      report.files.push(item);
    }
    report.status = 'GENERATED';
    console.log(JSON.stringify({ status: report.status, diagrams: report.files.length, visual_review: false }));
  } finally {
    if (report.status === 'STARTED') report.status = 'FAILED';
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    fs.writeFileSync(path.join(directory, '_render.json'), JSON.stringify(report, null, 2) + '\n');
  }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
