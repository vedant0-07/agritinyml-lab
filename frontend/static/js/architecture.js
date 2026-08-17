/**
 * Architecture Page — Dataset split chart
 */

const ArchPage = (() => {
  'use strict';

  let datasetChart = null;
  let initialized  = false;

  function buildDatasetChart() {
    const ctx = document.getElementById('dataset-chart');
    if (!ctx) return;
    if (datasetChart) datasetChart.destroy();
    datasetChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Train (350)', 'Validation (75)', 'Test (76)'],
        datasets: [{
          data: [350, 75, 76],
          backgroundColor: [
            'rgba(14,165,233,0.5)',
            'rgba(34,197,94,0.5)',
            'rgba(245,158,11,0.5)'
          ],
          borderColor: [
            'rgba(14,165,233,0.9)',
            'rgba(34,197,94,0.9)',
            'rgba(245,158,11,0.9)'
          ],
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, padding: 12 }
          }
        }
      }
    });
  }

  function init() {
    if (initialized) return;
    initialized = true;
    setTimeout(buildDatasetChart, 100);
  }

  return { init };
})();
