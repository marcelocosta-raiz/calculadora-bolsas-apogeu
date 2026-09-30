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
  const onlyAlerts = document.getElementById('metas-alertas').checked;
  const rows = BOLETINS.metas.filter(m => m.filial === getUnidade()
    && (!segment || m.segmento === segment) && (!series || m.id === series) && (!onlyAlerts || m.revisao));
  document.getElementById('metas-data').textContent = 'Ficha financeira de ' + BOLETINS.data_ficha.split('-').reverse().join('/')
    + ' · Matriculados e pré-matriculados de captação · Atualização por carga validada';
  document.getElementById('metas-resumo').textContent = rows.length + ' séries · '
    + rows.reduce((sum, m) => sum + m.alunos, 0) + ' alunos elegíveis · '
    + rows.filter(m => m.revisao).length + ' sinalizações de revisão';
  document.getElementById('metas-body').innerHTML = rows.map(m => {
    const exclusions = Object.values(m.excluidos).reduce((a,b) => a+b, 0);
    return `<tr><td>${textoSeguro(m.segmento)} · ${textoSeguro(m.serie)}</td>
      <td>${m.alunos} / ${m.meta_alunos}</td><td>${moedaMeta(m.ticket_meta)}</td>
      <td>${moedaMeta(m.ticket_realizado)}</td><td>${m.horizonte || 'Revisar'}</td>
      <td class="money">${moedaMeta(m.ticket_alvo)}</td><td>${moedaMeta(m.limite_revisao)}</td>
      <td><span class="meta-status ${m.revisao ? 'revisar' : ''}">${m.revisao ? 'Revisão necessária' : 'Dentro do limite'}</span>
      ${!m.alunos ? '<br>Sem alunos elegíveis; piso preservado' : ''}
      ${m.sem_horizonte ? '<br>Meta de quantidade zero; revisar horizonte' : ''}
      ${exclusions ? '<br>' + exclusions + ' excluído(s) ou pendente(s)' : ''}</td></tr>`;
  }).join('') || '<tr><td colspan="8">Nenhuma série com os filtros selecionados.</td></tr>';
}
