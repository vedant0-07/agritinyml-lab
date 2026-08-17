/**
 * Comparison Page — Float32 vs INT8 charts
 */

const ComparisonPage = (() => {
  'use strict';

  let sizeChart    = null;
  let accuracyChart = null;
  let initialized  = false;

  const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } } }
    },
    scales: {
      x: { ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }, grid: { color: 'rgba(30,58,95,0.3)' } },
      y: { ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }, grid: { color: 'rgba(30,58,95,0.3)' } }
    }
  };

  function buildSizeChart() {
    const ctx = document.getElementById('size-chart');
    if (!ctx) return;
    if (sizeChart) sizeChart.destroy();
    sizeChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Float32', 'INT8'],
        datasets: [{
          label: 'Model Size (KB)',
          data: [6.90, 5.50],
          backgroundColor: ['rgba(14,165,233,0.3)', 'rgba(34,197,94,0.3)'],
          borderColor:     ['rgba(14,165,233,0.8)', 'rgba(34,197,94,0.8)'],
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false } },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, beginAtZero: true, title: { display: true, text: 'Size (KB)', color: '#64748b', font: { size: 10 } } }
        }
      }
    });
  }

  function buildAccuracyChart() {
    const ctx = document.getElementById('accuracy-chart');
    if (!ctx) return;
    if (accuracyChart) accuracyChart.destroy();
    accuracyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Accuracy', 'Precision', 'Recall', 'F1 Score'],
        datasets: [
          {
            label: 'Float32',
            data: [96.05, 96.55, 93.33, 94.92],
            backgroundColor: 'rgba(14,165,233,0.3)',
            borderColor:     'rgba(14,165,233,0.8)',
            borderWidth: 2, borderRadius: 4,
          },
          {
            label: 'INT8',
            data: [96.05, 96.55, 93.33, 94.92],
            backgroundColor: 'rgba(34,197,94,0.3)',
            borderColor:     'rgba(34,197,94,0.8)',
            borderWidth: 2, borderRadius: 4,
          }
        ]
      },
      options: {
        ...CHART_DEFAULTS,
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, min: 90, max: 100, title: { display: true, text: 'Score (%)', color: '#64748b', font: { size: 10 } } }
        }
      }
    });
  }

  function init() {
    if (initialized) return;
    initialized = true;
    setTimeout(() => {
      buildSizeChart();
      buildAccuracyChart();
    }, 100);
  }

  return { init };
})();
