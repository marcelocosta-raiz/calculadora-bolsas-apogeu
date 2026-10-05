function populateCalcSeries() {
  const select=document.getElementById('cm-serie');
  select.replaceChildren(new Option('— selecione —',''));
  for(const segment of SEG_ORDER){
    const metas=BOLETINS.metas.filter(m=>m.filial===getUnidade()&&m.segmento===segment);
    if(!metas.length)continue;
    const group=document.createElement('optgroup');group.label=segment;
    for(const meta of metas)group.appendChild(new Option(meta.serie,meta.id));
    select.appendChild(group);
  }
  document.getElementById('cm-total').value='';
  document.getElementById('calc-data').textContent='Ficha financeira de '+BOLETINS.data_ficha.split('-').reverse().join('/');
  calcMens();
}
function onSerieChange(){ document.getElementById('cm-total').value='';calcMens(); }
function calcMens(){
  const meta=BOLETINS.metas.find(m=>m.id===document.getElementById('cm-serie').value);
  const result=document.getElementById('cm-result');
  const input=document.getElementById('cm-total');
  input.disabled=!meta;
  if(!meta){result.innerHTML='<p>Selecione uma série para calcular.</p>';return;}
  const assessment=avaliarProposta(input.value,meta);
  const valid=assessment.situacao!=='invalida';
  input.setAttribute('aria-invalid',String(!valid&&input.value!==''));
  const delta=assessment.diferencaCentavos;
  let title,detail,cls;
  if(!valid){
    title=input.value===''?'Informe o ticket total':'Confira o valor da proposta';
    detail=input.value===''?'Inclua mensalidade e material didático.':'O total deve cobrir o material didático mensal de '+moedaMeta(meta.md_anual/12)+'.';
    cls='neutro';
  }else{
    title=delta>=0?'Dentro da meta':'Fora da meta';cls=delta>=0?'acima':'abaixo';
    detail=delta===0?'A proposta atinge exatamente o ticket projetado.':delta<0
      ? 'Faltam '+moedaMeta(-delta/100)+' por mês para atingir o ticket projetado.'
      : 'A proposta está '+moedaMeta(delta/100)+' por mês acima do ticket projetado.';
  }
  result.innerHTML=`<h3>Resultado da proposta</h3>
    <div class="res-linha"><span>Mensalidade com bolsa</span><b>${valid?moedaMeta(assessment.mensalidadeCentavos/100):'—'}</b></div>
    <div class="res-linha"><span>Material didático incluído</span><b>${moedaMeta(meta.md_anual/12)}</b></div>
    <div class="res-linha"><strong>Ticket total proposto</strong><b>${valid?moedaMeta(assessment.totalCentavos/100):'—'}</b></div>
    <div class="res-linha"><span>Ticket meta da série</span><b>${moedaMeta(meta.ticket_minimo)}</b></div>
    <div class="meta-box ${cls}" role="status" aria-live="polite"><div class="status">${title}</div><p>${detail}</p></div>
    <div class="res-linha"><span>Ticket total para atingir a meta a partir dos tickets realizados até hoje</span><b>${moedaMeta(meta.ticket_alvo)}</b></div>
    <p class="hint">Valores mensais com material didático. Referência calculada com a ficha indicada nesta página.</p>`;
}
