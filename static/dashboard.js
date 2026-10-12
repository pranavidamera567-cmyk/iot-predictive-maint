const get = u => fetch(u).then(r => r.json());
const charts = {};

function draw(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), config);
}

async function showAsset(id) {
  const d = await get(`/api/timeseries/${id}?hours=336`);
  document.getElementById('tsTitle').textContent = `${id}: temperature & vibration`;
  draw('ts', { type: 'line', data: { labels: d.timestamp, datasets: [
    { label: 'Temperature °C', data: d.temperature, borderColor: '#e67e22', pointRadius: 0, yAxisID: 'y' },
    { label: 'Vibration', data: d.vibration, borderColor: '#2980b9', pointRadius: 0, yAxisID: 'y1' }]},
    options: { scales: { y: {}, y1: { position: 'right', grid: { drawOnChartArea: false } } } } });
  draw('risk', { type: 'line', data: { labels: d.timestamp, datasets: [
    { label: 'Failure risk', data: d.risk, borderColor: '#c0392b', fill: true, backgroundColor: '#c0392b22', pointRadius: 0 }]},
    options: { scales: { y: { min: 0, max: 1 } } } });
}

async function init() {
  const [assets, alerts, maint, m] = await Promise.all(
    ['/api/assets', '/api/alerts', '/api/maintenance', '/api/metrics'].map(get));
  document.getElementById('metrics').textContent =
    `Model holdout: recall ${(m.recall * 100).toFixed(0)}% · precision ${(m.precision * 100).toFixed(0)}%` +
    (m.roc_auc ? ` · AUC ${m.roc_auc.toFixed(2)}` : '');
  const tbody = document.querySelector('#assets tbody');
  assets.forEach(a => {
    const tr = document.createElement('tr');
    tr.className = 'row';
    tr.innerHTML = `<td>${a.asset_id}</td><td>${a.temperature}</td><td>${a.vibration}</td>
      <td>${(a.risk * 100).toFixed(0)}%</td><td class="${a.status}">${a.status}</td>`;
    tr.onclick = () => showAsset(a.asset_id);
    tbody.appendChild(tr);
  });
  document.getElementById('alerts').innerHTML = alerts.length
    ? alerts.map(a => `<li><b>${a.asset_id}</b> risk ${(a.risk * 100).toFixed(0)}% at ${a.timestamp}</li>`).join('')
    : '<li>No alerts</li>';
  draw('mMonth', { type: 'bar', data: { labels: maint.by_month.map(r => r.month), datasets: [
    { label: 'Events', data: maint.by_month.map(r => r.events), backgroundColor: '#2980b9' },
    { label: 'Downtime h', data: maint.by_month.map(r => r.downtime), backgroundColor: '#e67e22' }]}});
  draw('mType', { type: 'doughnut', data: { labels: maint.by_type.map(r => r.type), datasets: [
    { data: maint.by_type.map(r => r.cost), backgroundColor: ['#2980b9', '#e67e22', '#27ae60', '#8e44ad'] }]}});
  showAsset(assets[0].asset_id);
}
init();
