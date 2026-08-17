/**
 * Playground Page — Model Inference UI
 * Handles form validation and calling /api/predict/irrigation
 */

const PlaygroundPage = (() => {
  'use strict';

  function showError(msg) {
    const box = document.getElementById('playground-error');
    const txt = document.getElementById('playground-error-text');
    if (box && txt) { txt.textContent = msg; box.style.display = 'flex'; }
  }
  function hideError() {
    const box = document.getElementById('playground-error');
    if (box) box.style.display = 'none';
  }

  function setFieldError(id, show) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('visible', show);
  }

  function validate() {
    let valid = true;
    const cropType    = document.getElementById('input-crop-type').value;
    const cropDays    = document.getElementById('input-crop-days').value;
    const soilMoist   = document.getElementById('input-soil-moisture').value;
    const temperature = document.getElementById('input-temperature').value;
    const humidity    = document.getElementById('input-humidity').value;

    setFieldError('err-crop-type',    !cropType);
    setFieldError('err-crop-days',    !cropDays    || isNaN(parseFloat(cropDays))   || parseFloat(cropDays) < 0);
    setFieldError('err-soil-moisture',!soilMoist   || isNaN(parseFloat(soilMoist)));
    setFieldError('err-temperature',  !temperature || isNaN(parseFloat(temperature)));
    setFieldError('err-humidity',     !humidity    || isNaN(parseFloat(humidity)) || parseFloat(humidity) < 0 || parseFloat(humidity) > 100);

    if (!cropType || !cropDays || !soilMoist || !temperature || !humidity) valid = false;
    if (isNaN(parseFloat(cropDays)) || parseFloat(cropDays) < 0)   valid = false;
    if (isNaN(parseFloat(soilMoist)))                               valid = false;
    if (isNaN(parseFloat(temperature)))                             valid = false;
    if (isNaN(parseFloat(humidity)) || parseFloat(humidity) < 0 || parseFloat(humidity) > 100) valid = false;

    return valid;
  }

  function setLoading(loading) {
    const btn     = document.getElementById('run-predict-btn');
    const spinner = document.getElementById('run-predict-spinner');
    if (btn)     btn.disabled = loading;
    if (spinner) spinner.style.display = loading ? 'inline-block' : 'none';
    if (btn && !loading) btn.textContent = '';
    if (btn && !loading) {
      spinner.style.display = 'none';
      btn.innerHTML = '<span id="run-predict-spinner" class="spinner" style="display:none;"></span>▷ RUN INT8 PREDICTION';
    }
    if (loading) {
      if (btn) btn.innerHTML = '<span id="run-predict-spinner" class="spinner"></span> RUNNING INFERENCE…';
    }
  }

  function renderResult(data) {
    const isIrrigation = data.prediction === 1;

    // Result card
    const card = document.getElementById('result-card');
    card.className = `result-card ${isIrrigation ? 'positive' : 'negative'}`;

    document.getElementById('result-empty').style.display = 'none';
    document.getElementById('result-content').style.display = 'block';

    document.getElementById('result-icon').textContent  = isIrrigation ? '🌱' : '✓';
    document.getElementById('result-label').className   = `result-label ${isIrrigation ? 'positive' : 'negative'}`;
    document.getElementById('result-label').textContent = data.label;
    document.getElementById('result-prob').textContent  = `Confidence: ${(data.probability_pct).toFixed(2)}%`;

    document.getElementById('rm-prediction').textContent = `${data.prediction} (${data.label})`;
    document.getElementById('rm-probability').textContent = `${(data.probability * 100).toFixed(4)}%`;
    document.getElementById('rm-model').textContent     = data.model;
    document.getElementById('rm-engine').textContent    = data.inference_engine;
    document.getElementById('rm-execution').textContent = data.execution;
    document.getElementById('rm-time').textContent      = data.inference_time_ms != null ? `${data.inference_time_ms} ms` : 'N/A';
    document.getElementById('rm-fpga').textContent      = data.fpga_status;
    document.getElementById('rm-backend').textContent   = data.backend || 'tflite';

    // Probability bars
    const prob   = parseFloat(data.probability);
    const pctIrr = (prob * 100).toFixed(1);
    const pctNo  = ((1 - prob) * 100).toFixed(1);

    document.getElementById('prob-bar-card').style.display = 'block';
    document.getElementById('prob-bar-irrigation').style.width    = `${pctIrr}%`;
    document.getElementById('prob-val-irrigation').textContent    = `${pctIrr}%`;
    document.getElementById('prob-bar-no-irrigation').style.width = `${pctNo}%`;
    document.getElementById('prob-val-no-irrigation').textContent = `${pctNo}%`;
  }

  async function runPrediction(e) {
    e.preventDefault();
    hideError();

    if (!validate()) {
      showError('Please fill in all fields with valid agricultural parameters.');
      return;
    }

    const cropType    = document.getElementById('input-crop-type').value;
    const cropDays    = parseFloat(document.getElementById('input-crop-days').value);
    const soilMoist   = parseFloat(document.getElementById('input-soil-moisture').value);
    const temperature = parseFloat(document.getElementById('input-temperature').value);
    const humidity    = parseFloat(document.getElementById('input-humidity').value);

    setLoading(true);

    try {
      const res = await fetch('/api/predict/irrigation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop_type:     cropType,
          crop_days:     cropDays,
          soil_moisture: soilMoist,
          temperature:   temperature,
          humidity:      humidity
        })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        showError(data.error || 'Inference failed. Please check the backend server.');
        return;
      }

      renderResult(data);

    } catch (err) {
      showError('Unable to connect to inference server. Make sure the backend is running at http://127.0.0.1:5000');
    } finally {
      setLoading(false);
    }
  }

  function init() {
    const form = document.getElementById('playground-form');
    if (form && !form._bound) {
      form.addEventListener('submit', runPrediction);
      form._bound = true;
    }
  }

  // Auto-init when DOM is ready
  document.addEventListener('DOMContentLoaded', init);

  return { init, runPrediction };
})();
