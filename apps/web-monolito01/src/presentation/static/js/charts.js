"use strict";
const chartContainer = document.getElementById("overview-chart");
if (chartContainer && window.Highcharts) {
  const values = JSON.parse(chartContainer.dataset.chartValues);
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  window.Highcharts.chart(chartContainer, {
    chart: {type: "column", backgroundColor: "transparent", height: 245,
      style: {fontFamily: "Inter, sans-serif"}, animation: !reducedMotion},
    title: {text: null},
    accessibility: {description: chartContainer.dataset.chartTitle},
    xAxis: {categories: values.map(item => item.label), lineColor: "#e2e8f0", tickLength: 0,
      labels: {style: {color: "#64748b", fontSize: "12px"}}},
    yAxis: {title: {text: null}, allowDecimals: false, gridLineColor: "#eef2f6", min: 0},
    legend: {enabled: false},
    tooltip: {pointFormat: "<b>{point.y}</b> registros", useHTML: false},
    plotOptions: {series: {animation: !reducedMotion, borderWidth: 0}, column: {borderRadius: 4, maxPointWidth: 42}},
    series: [{name: "Registros", color: "#1e3a5f", data: values.map(item => item.value)}],
    credits: {enabled: true},
  });
}
