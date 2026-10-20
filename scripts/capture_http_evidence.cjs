'use strict';
// Captures of the recorded HTTP exchange viewer. No credentials are injected.
const fs = require('fs'), path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require('playwright');
const root = path.resolve(process.argv[2] || 'documentation/evidencias/segundo-parcial/http');
(async () => {
  const coverage = JSON.parse(fs.readFileSync(path.join(root, 'coverage.json')));
  fs.mkdirSync(path.join(root, 'captures'), {recursive:true});
  const browser = await chromium.launch({channel:'chrome', headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
    for (const entry of coverage.endpoints) {
      if (!entry.http_records) continue;
      await page.goto(pathToFileURL(path.join(root, entry.page)).href);
      await page.screenshot({path:path.join(root, entry.screenshot)});
    }
    await page.goto(pathToFileURL(path.join(root, 'index.html')).href);
    await page.screenshot({path:path.join(root, 'captures/inventory.png')});
  } finally { await browser.close(); }
  console.log(JSON.stringify({captures:coverage.endpoints.filter(x=>x.http_records).length}));
})().catch(error => {console.error(error);process.exitCode=1;});
