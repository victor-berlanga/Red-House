'use strict';
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const root = path.resolve(__dirname, '../../../../..');
const output = path.join(root, '.local/artifacts/lineage-labels-20261116');
const { chromium } = require(path.join(root, '.local/gcp-public/browser/node_modules/playwright'));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1440, height: 900 } });
    await context.route(/^https?:/, route => route.abort());
    const page = await context.newPage();
    await page.goto(pathToFileURL(path.join(output, 'lineage.html')).href);
    assert.deepEqual(await page.locator('td[data-label="Producto"]').allTextContents(), ['Eritrocitos', 'Eritrocitos']);
    assert.deepEqual(await page.locator('td[data-label="Estado"]').allTextContents(), ['Disponible', 'Cuarentena']);
    assert.equal(await page.locator('time[data-local-time]').count(), 2);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(__dirname, 'linaje-etiquetas-sinteticas.png'), fullPage: true });
    fs.copyFileSync(path.join(output, 'render.json'), path.join(__dirname, 'render.json'));
    console.log('Captura aprobada; contenido sintético y navegador cerrado.');
  } finally { await browser.close(); }
})().catch(() => { console.error('Captura fallida; revisar artefacto local.'); process.exitCode = 1; });
