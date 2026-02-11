const runBtn = document.getElementById('runBtn');
const statusEl = document.getElementById('status');
const tbody = document.querySelector('#resultTable tbody');

function setStatus(msg) {
  statusEl.textContent = msg;
}

function clearRows() {
  tbody.innerHTML = '';
}

function addRow(row) {
  const tr = document.createElement('tr');
  [row.ico, row.name, row.executive, row.phone, row.source, row.operator_check].forEach(v => {
    const td = document.createElement('td');
    td.textContent = v || '-';
    tr.appendChild(td);
  });
  tbody.appendChild(tr);
}

async function runSearch() {
  const city = document.getElementById('city').value.trim();
  const limit = Number(document.getElementById('limit').value || 20);
  const maxSourcePages = Number(document.getElementById('maxPages').value || 4);
  const strict = document.getElementById('strict').checked;
  const demo = document.getElementById('demo').checked;

  if (!city) {
    setStatus('Vyplň město.');
    return;
  }

  clearRows();
  setStatus('Načítám data, čekej...');
  runBtn.disabled = true;

  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, limit, max_source_pages: maxSourcePages, strict, demo })
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      setStatus(data.error || 'Nastala chyba.');
      return;
    }

    if (!data.rows.length) {
      setStatus('Hotovo: nic nenalezeno pro zadaný filtr.');
      return;
    }

    data.rows.forEach(addRow);
    setStatus(`Hotovo: nalezeno ${data.rows.length} záznamů.`);
  } catch (err) {
    setStatus(`Chyba: ${err.message}`);
  } finally {
    runBtn.disabled = false;
  }
}

runBtn.addEventListener('click', runSearch);
