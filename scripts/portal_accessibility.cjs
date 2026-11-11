'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
module.exports=async function(page,input,report,role){
 await page.waitForFunction(()=>[...document.querySelectorAll('[data-chart-values]')].every(e=>!JSON.parse(e.dataset.chartValues).length||e.querySelector('.highcharts-root')));
 const charts=await page.evaluate(()=>[...document.querySelectorAll('[data-chart-values]')].map(e=>({expected:JSON.parse(e.dataset.chartValues),actual:window.Highcharts?.charts.find(c=>c?.renderTo===e)?.series[0].data.map(p=>p.y),rendered:!!e.querySelector('.highcharts-root'),table:!!e.closest('section').querySelector('table')})));
 for(const chart of charts){assert.ok(chart.table);if(chart.expected.length){assert.ok(chart.rendered);assert.deepEqual(chart.actual,chart.expected.map(r=>r.value));}}
 (report.charts ||= []).push({role,charts});
 for(const width of [390,768,1440]){
  await page.setViewportSize({width,height:1000});await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth);
  await page.evaluate(()=>document.activeElement?.blur());await page.keyboard.press('Tab');
  const focus=await page.evaluate(()=>{const e=document.activeElement,r=e.getBoundingClientRect();return {tag:e.tagName,visible:r.width>0&&r.height>0,label:e.textContent.trim().slice(0,100),outline:getComputedStyle(e).outlineStyle};});
  assert.ok(focus.visible&&focus.tag!=='BODY');
  if(input.axe){await page.evaluate(fs.readFileSync(input.axe,'utf8'));const violations=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target)}));});(report.accessibility ||= []).push({role,page:new URL(page.url()).pathname,width,focus,violations});assert.deepEqual(violations,[],`Accesibilidad ${role} ${width}`);}
 }
};
