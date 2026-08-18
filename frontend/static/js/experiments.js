/**
 * Experiments Page — History table with search, filter, and export
 * Uses /api/experiments (Supabase PostgreSQL backend)
 */

const ExperimentsPage = (() => {
  'use strict';

  let allRows    = [];
  let initialized = false;

  function formatTimestamp(ts) {
    if (!ts) return '—';
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
      if (count) count.textContent   = '0 records';
      return;
    }

    if (empty) empty.style.display = 'none';
    if (table) table.style.display = 'table';
    if (count) count.textContent = `${rows.length} record${rows.length !== 1 ? 's' : ''}`;

    if (!tbody) return;

    tbody.innerHTML = rows.map((r, i) => {
      // prediction is now a label string e.g. "Irrigation Required"
      const isIrr     = (r.prediction || '').toLowerCase().includes('irrigation required') &&
                        !(r.prediction || '').toLowerCase().includes('no irrigation');
      const predColor = isIrr ? 'var(--accent-green)' : 'var(--accent-cyan)';

      // inputs may be a parsed JSONB object
      const inp = r.inputs || {};

      return `<tr>
        <td>${r.id ?? (i + 1)}</td>
        <td>${formatTimestamp(r.timestamp)}</td>
        <td>${r.model_name || r.model_id || '—'}</td>
        <td>${inp.crop_type ?? r.crop_type ?? '—'}</td>
        <td>${inp.crop_days  ?? r.crop_days  ?? '—'}</td>
        <td>${inp.soil_moisture ?? r.soil_moisture ?? '—'}</td>
        <td>${inp.temperature != null ? inp.temperature + '°C' : (r.temperature != null ? r.temperature + '°C' : '—')}</td>
        <td>${inp.humidity != null ? inp.humidity + '%' : (r.humidity != null ? r.humidity + '%' : '—')}</td>
        <td style="color:${predColor}; font-weight:600;">${r.prediction || '—'}</td>
        <td>${r.probability != null ? (r.probability * 100).toFixed(2) + '%' : '—'}</td>
        <td>${r.engine || 'TFLite'}</td>
        <td>${r.inference_time_ms != null ? r.inference_time_ms + ' ms' : '—'}</td>
      </tr>`;
    }).join('');
  }

  function filterRows() {
    const search = (document.getElementById('history-search')?.value || '').toLowerCase();
    const pred   = (document.getElementById('history-filter-pred')?.value || '');

    let rows = [...allRows];

    if (search) {
      rows = rows.filter(r => {
        const inp = r.inputs || {};
        return (
          (inp.crop_type || r.crop_type || '').toLowerCase().includes(search) ||
          (r.prediction  || '').toLowerCase().includes(search) ||
          (r.model_name  || '').toLowerCase().includes(search)
        );
      });
    }

    if (pred) {
      // pred is '1' (irrigation required) or '0' (no irrigation)
      rows = rows.filter(r => {
        const isIrr = (r.prediction || '').toLowerCase().includes('irrigation required') &&
                      !(r.prediction || '').toLowerCase().includes('no irrigation');
        return pred === '1' ? isIrr : !isIrr;
      });
    }

    renderTable(rows);
  }

  async function loadHistory() {
    const load  = document.getElementById('history-loading');
    const empty = document.getElementById('history-empty');
    const table = document.getElementById('history-table');
    const count = document.getElementById('history-count');

    if (load)  load.style.display  = 'flex';
    if (empty) empty.style.display = 'none';
    if (table) table.style.display = 'none';

    try {
      const res  = await fetch('/api/experiments');
      const data = await res.json();

      if (data.success === false) {
        // DB unavailable — show error in the empty state
        if (load)  load.style.display  = 'none';
        if (empty) {
          empty.style.display = 'flex';
          const msg = empty.querySelector('.empty-msg') || empty;
          msg.innerHTML = `<div style="color:var(--accent-amber); font-size:13px;">
            ⚠ Database unavailable<br>
            <span style="color:var(--text-muted); font-size:11px; margin-top:6px; display:block;">
              ${data.error || 'DATABASE_URL is not configured.'}
            </span>
          </div>`;
        }
        if (count) count.textContent = '0 records';
        allRows = [];
        return;
      }

      allRows = data.experiments || [];
      filterRows();

    } catch (err) {
      console.error('Experiments fetch error:', err);
      if (load)  load.style.display  = 'none';
      if (empty) empty.style.display = 'flex';
      if (count) count.textContent   = '0 records';
      allRows = [];
      renderTable([]);
    }
  }

  async function clearHistory() {
    if (!confirm('Clear all experiment history? This cannot be undone.')) return;
    try {
      await fetch('/api/experiments', { method: 'DELETE' });
      allRows = [];
      renderTable([]);
    } catch {
      alert('Failed to clear history.');
    }
  }

  function exportCSV() {
    window.location.href = '/api/experiments/export';
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
