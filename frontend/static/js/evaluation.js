/**
 * Evaluation Page
 * Runs actual test set evaluation via /api/evaluate/irrigation
 */

const EvaluationPage = (() => {
  'use strict';

  let initialized = false;
  let evalData = null;

  function setLoading(loading) {
    const btn     = document.getElementById('run-eval-btn');
    const spinner = document.getElementById('eval-spinner');
    if (btn)     btn.disabled = loading;
    if (spinner) spinner.style.display = loading ? 'inline-block' : 'none';
    if (loading && btn) {
      btn.innerHTML = '<span id="eval-spinner" class="spinner"></span> RUNNING 76 SAMPLES…';
    } else if (btn) {
      btn.innerHTML = '<span id="eval-spinner" class="spinner" style="display:none;"></span>◎ RUN COMPLETE TEST SET';
    }
  }

  function updateConfusionMatrix(cm) {
    const ids = ['TN', 'FP', 'FN', 'TP'];
    ids.forEach(id => {
      const el = document.getElementById(`live-cm-${id}`);
      if (el) el.querySelector('div:first-child').textContent = cm[id];
    });
  }

  function renderLiveMetrics(metrics) {
    const container = document.getElementById('live-metrics');
    if (!container) return;
    const m = [
      ['Accuracy',  metrics.accuracy  + '%'],
      ['Precision', metrics.precision + '%'],
      ['Recall',    metrics.recall    + '%'],
      ['F1 Score',  metrics.f1_score  + '%'],
    ];
    container.innerHTML = m.map(([label, val]) => `
      <div class="metric-bar-row">
        <div class="metric-bar-label">${label}</div>
        <div class="metric-bar-track"><div class="metric-bar-fill" style="width:${parseFloat(val)}%"></div></div>
        <div class="metric-bar-value">${val}</div>
      </div>`).join('');
  }

  function renderSampleTable(samples) {
    const tbody = document.getElementById('eval-samples-tbody');
    if (!tbody) return;
    tbody.innerHTML = samples.map((s, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${s.true_label} <span style="font-size:9px; color:var(--text-muted);">(${s.true_label_name})</span></td>
        <td style="color:${s.correct ? 'var(--accent-green)' : 'var(--accent-red)'};">${s.predicted} (${s.predicted_name})</td>
        <td>${(s.probability * 100).toFixed(2)}%</td>
        <td style="font-size:13px;">${s.correct ? '<span style="color:var(--accent-green);">✓</span>' : '<span style="color:var(--accent-red);">✗</span>'}</td>
      </tr>`).join('');
  }

  async function runEvaluation() {
    setLoading(true);
    try {
      const res = await fetch('/api/evaluate/irrigation', { method: 'POST' });
      const data = await res.json();

      if (!res.ok || !data.success) {
        alert(data.error || 'Evaluation failed. Ensure backend is running.');
        return;
      }

      evalData = data;
      const metrics = data.metrics;
      const cm      = metrics.confusion_matrix;

      // Update summary cards
      document.getElementById('eval-summary').style.display = 'grid';
      document.getElementById('ev-samples').textContent   = data.test_samples;
      document.getElementById('ev-accuracy').textContent  = metrics.accuracy + '%';
      document.getElementById('ev-correct').textContent   = metrics.correct;
      document.getElementById('ev-incorrect').textContent = metrics.incorrect;

      // Show charts and update
      document.getElementById('eval-charts').style.display = 'grid';
      updateConfusionMatrix(cm);
      renderLiveMetrics(metrics);

      // Show sample table
      document.getElementById('eval-samples-section').style.display = 'block';
      document.getElementById('eval-correct-badge').textContent   = `✓ ${metrics.correct} Correct`;
      document.getElementById('eval-incorrect-badge').textContent = `✗ ${metrics.incorrect} Incorrect`;
      renderSampleTable(data.samples);

      // Show export button
      document.getElementById('export-eval-btn').style.display = 'inline-flex';

    } catch (err) {
      alert('Unable to connect to inference server. Please ensure the Flask backend is running.');
    } finally {
      setLoading(false);
    }
  }

  function exportResults() {
    if (!evalData) return;
    const m = evalData.metrics;
    const cm = m.confusion_matrix;
    let csv  = 'Metric,Value\n';
    csv += `Test Samples,${evalData.test_samples}\n`;
    csv += `Accuracy,${m.accuracy}%\n`;
    csv += `Precision,${m.precision}%\n`;
    csv += `Recall,${m.recall}%\n`;
    csv += `F1 Score,${m.f1_score}%\n`;
    csv += `Correct,${m.correct}\n`;
    csv += `Incorrect,${m.incorrect}\n`;
    csv += `TP,${cm.TP}\nTN,${cm.TN}\nFP,${cm.FP}\nFN,${cm.FN}\n`;
    csv += '\n#,True Label,Predicted,Probability,Correct\n';
    evalData.samples.forEach((s, i) => {
      csv += `${i+1},${s.true_label_name},${s.predicted_name},${s.probability},${s.correct}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'evaluation_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  function init() {
    if (initialized) return;
    initialized = true;

    const runBtn = document.getElementById('run-eval-btn');
    if (runBtn) runBtn.addEventListener('click', runEvaluation);

    const expBtn = document.getElementById('export-eval-btn');
    if (expBtn) expBtn.addEventListener('click', exportResults);
  }

  return { init };
})();
