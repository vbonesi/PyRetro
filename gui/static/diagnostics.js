'use strict';
const refresh = document.getElementById('refresh');
const download = document.getElementById('download');
const status = document.getElementById('status');
const checks = document.getElementById('checks');
let report = null;
const labels = {roms:'Pasta de ROMs', saves:'Pasta de saves', states:'Pasta de estados', backups:'Pasta de backups', rclone:'rclone', 'bonisarch-emulator':'Lançador de emuladores'};
const states = {present:'Encontrado', missing:'Não encontrado', unavailable:'Indisponível'};
refresh.addEventListener('click', async () => {
  refresh.disabled = true; download.disabled = true; report = null;
  checks.replaceChildren(); status.textContent = 'Verificando…';
  try {
    const response = await fetch('/api/diagnostics', {cache:'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (data.schema !== 1 || !Array.isArray(data.checks)) throw new Error('invalid');
    report = data;
    data.checks.forEach(check => {
      const item = document.createElement('li');
      item.textContent = `${labels[check.id] || 'Componente'}: ${states[check.status] || 'Desconhecido'}. ${check.action || ''}`;
      checks.append(item);
    });
    status.textContent = 'Verificação concluída. O relatório está pronto para baixar.';
    download.disabled = false;
  } catch (_) {
    status.textContent = 'Não foi possível obter o relatório. Confira se o PyRetro está ativo e tente novamente.';
  } finally { refresh.disabled = false; }
});
download.addEventListener('click', () => {
  if (!report) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = 'pyretro-diagnostico.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
