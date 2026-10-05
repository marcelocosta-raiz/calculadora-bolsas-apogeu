/* Metas agregadas: nenhuma informação individual de alunos. */
function normalizarMeta(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
}
function buscarMeta(dado) {
  if (!dado || typeof BOLETINS === 'undefined') return null;
  return BOLETINS.metas.find(meta => normalizarMeta(meta.filial) === normalizarMeta(dado.unidade)
    && meta.segmento === dado.segmento && normalizarMeta(meta.serie) === normalizarMeta(dado.serie)) || null;
}
function textoSeguro(value) {
  return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
}
function moedaMeta(value) {
  return value == null ? 'Sem alunos elegíveis' : Number(value).toLocaleString('pt-BR', {style:'currency', currency:'BRL'});
}
function atualizarFiltrosMetas() {
  const select = document.getElementById('metas-serie');
  const segment = document.getElementById('metas-segmento').value;
  const previous = select.value;
  select.replaceChildren(new Option('Todas as séries', ''));
  BOLETINS.metas.filter(m => m.filial === getUnidade() && (!segment || m.segmento === segment)).forEach(m => {
    select.add(new Option(m.serie, m.id));
  });
  if ([...select.options].some(o => o.value === previous)) select.value = previous;
  renderMetas();
}
function renderMetas() {
  const segment = document.getElementById('metas-segmento').value;
  const series = document.getElementById('metas-serie').value;
  const rows = BOLETINS.metas.filter(m => m.filial === getUnidade()
    && (!segment || m.segmento === segment) && (!series || m.id === series));
  document.getElementById('metas-data').textContent = 'Ficha financeira de ' + BOLETINS.data_ficha.split('-').reverse().join('/')
    + ' · Matriculados e pré-matriculados de captação';
  document.getElementById('metas-resumo').textContent = rows.length + ' séries · '
    + rows.reduce((sum, m) => sum + m.alunos, 0) + ' alunos considerados';
  document.getElementById('metas-body').innerHTML = rows.map(m => {
    const delta = m.ticket_realizado == null ? null : Math.round(m.ticket_realizado*100)-Math.round(m.ticket_minimo*100);
    const label = delta == null ? 'Sem matrículas válidas' : delta === 0 ? 'Na meta' : delta > 0 ? 'Acima da meta' : 'Abaixo da meta';
    const cls = delta == null ? 'neutro' : delta < 0 ? 'revisar' : '';
    return `<tr><td>${textoSeguro(m.segmento)} · ${textoSeguro(m.serie)}</td>
      <td>${m.alunos} / ${m.meta_alunos}</td><td class="money">${moedaMeta(m.ticket_minimo)}</td>
      <td>${m.ticket_realizado == null ? '—' : moedaMeta(m.ticket_realizado)}</td>
      <td class="money">${moedaMeta(m.ticket_alvo)}</td>
      <td><span class="meta-status ${cls}">${label}</span></td></tr>`;
  }).join('') || '<tr><td colspan="6">Nenhuma série com os filtros selecionados.</td></tr>';
}
