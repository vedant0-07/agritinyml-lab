/**
 * Experiments Page — History table with search, filter, and export
 */

const ExperimentsPage = (() => {
  'use strict';

  let allRows = [];
  let initialized = false;

  function formatTimestamp(ts) {
    try {
      const d = new Date(ts);
      return d.toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'medium' });
    } catch { return ts; }
  }

  function renderTable(rows) {
    const tbody = document.getElementById('history-tbody');
    const table = document.getElementById('history-table');
    const empty = document.getElementById('history-empty');
    const load  = document.getElementById('history-loading');
    const count = document.getElementById('history-count');

    if (load) load.style.display = 'none';

    if (!rows || rows.length === 0) {
      if (table) table.style.display = 'none';
      if (empty) empty.style.display = 'flex';
      if (count) count.textContent = '0 records';
      return;
    }

    if (empty) empty.style.display = 'none';
    if (table) table.style.display = 'table';
    if (count) count.textContent = `${rows.length} record${rows.length !== 1 ? 's' : ''}`;

    if (!tbody) return;
    tbody.innerHTML = rows.map((r, i) => {
      const isIrr = r.prediction === 1;
      const predColor = isIrr ? 'var(--accent-green)' : 'var(--accent-cyan)';
      return `<tr>
        <td>${r.id ?? (i + 1)}</td>
        <td>${formatTimestamp(r.timestamp)}</td>
        <td>${r.model_id}</td>
        <td>${r.crop_type}</td>
        <td>${r.crop_days ?? '—'}</td>
        <td>${r.soil_moisture ?? '—'}</td>
        <td>${r.temperature ?? '—'}${r.temperature != null ? '°C' : ''}</td>
        <td>${r.humidity ?? '—'}${r.humidity != null ? '%' : ''}</td>
        <td style="color:${predColor}; font-weight:600;">${r.label || (isIrr ? 'Irrigation Required' : 'No Irrigation')}</td>
        <td>${r.probability != null ? (r.probability * 100).toFixed(2) + '%' : '—'}</td>
        <td>${r.inference_engine || 'TFLite'}</td>
        <td>${r.inference_time_ms != null ? r.inference_time_ms + ' ms' : '—'}</td>
      </tr>`;
    }).join('');
  }

  function filterRows() {
    const search = (document.getElementById('history-search')?.value || '').toLowerCase();
    const pred   = document.getElementById('history-filter-pred')?.value;
    let rows = [...allRows];
    if (search) {
      rows = rows.filter(r =>
        (r.crop_type || '').toLowerCase().includes(search) ||
        (r.label || '').toLowerCase().includes(search) ||
        (r.model_id || '').toLowerCase().includes(search)
      );
    }
    if (pred !== '' && pred != null) {
      rows = rows.filter(r => String(r.prediction) === pred);
    }
    renderTable(rows);
  }

  async function loadHistory() {
    const load = document.getElementById('history-loading');
    if (load) load.style.display = 'flex';
    try {
      const res  = await fetch('/api/history');
      const data = await res.json();
      allRows = data.history || [];
      filterRows();
    } catch {
      allRows = [];
      renderTable([]);
    }
  }

  async function clearHistory() {
    if (!confirm('Clear all experiment history? This cannot be undone.')) return;
    try {
      await fetch('/api/history/clear', { method: 'POST' });
      allRows = [];
      renderTable([]);
    } catch {
      alert('Failed to clear history.');
    }
  }

  function exportCSV() {
    window.location.href = '/api/history/export';
  }

  function init() {
    if (initialized) return;
    initialized = true;

    document.getElementById('refresh-history-btn')?.addEventListener('click', loadHistory);
    document.getElementById('clear-history-btn')?.addEventListener('click', clearHistory);
    document.getElementById('export-history-btn')?.addEventListener('click', exportCSV);
    document.getElementById('history-search')?.addEventListener('input', filterRows);
    document.getElementById('history-filter-pred')?.addEventListener('change', filterRows);

    loadHistory();
  }

  return { init };
})();
