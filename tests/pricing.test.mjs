import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';
const context=vm.createContext({});
vm.runInContext(readFileSync('pricing.js','utf8'),context);
const assess=(value,meta)=>context.avaliarProposta(value,meta);
const data=JSON.parse(readFileSync('boletins.json','utf8'));
const third=data.metas.find(m=>m.filial==='Global School Cidade Alta'&&m.serie==='3º Ano');
test('ticket total includes material once and compares recovery, not base floor',()=>{
  // Real 30/09 reference; use stored target so changing the snapshot remains valid.
  const result=assess(third.ticket_alvo-1,third);
  assert.equal(result.situacao,'abaixo');
  assert.equal(result.diferencaCentavos,-100);
  assert.equal(result.mensalidadeCentavos+result.materialCentavos,result.totalCentavos);
});
test('exact boundary and one cent each side',()=>{
  assert.equal(assess(third.ticket_alvo,third).situacao,'dentro');
  assert.equal(assess(third.ticket_alvo+.01,third).diferencaCentavos,1);
  assert.equal(assess(third.ticket_alvo-.01,third).diferencaCentavos,-1);
});
test('empty, missing meta, negative, and below material are invalid',()=>{
  for(const value of ['',null,NaN,-1,0])assert.equal(assess(value,third).situacao,'invalida');
  assert.equal(assess(1500,null).situacao,'invalida');
});
test('all actual series accept their target, without relying on a full tuition price',()=>{
  for(const meta of data.metas)assert.equal(assess(meta.ticket_alvo,meta).situacao,'dentro',meta.id);
});
