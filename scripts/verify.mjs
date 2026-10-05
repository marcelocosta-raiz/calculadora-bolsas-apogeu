import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const html = readFileSync('index.html', 'utf8');
const context = vm.createContext({});
for (const file of ['dados.js', 'boletins.js', 'metas.js', 'pricing.js', 'calculadora.js']) {
  vm.runInContext(readFileSync(file, 'utf8'), context, {filename: file});
}
for (const [,code] of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) new vm.Script(code);
const report = vm.runInContext(`({
  metas: BOLETINS.metas.length,
  included: BOLETINS.metas.reduce((s,m)=>s+m.alunos,0),
  prices: DADOS.length,
  mapped: DADOS.filter(d=>buscarMeta(d)).length,
  noMeta: buscarMeta({unidade:'Zona Norte',segmento:'EI',serie:'Infantil 1'}),
  courses: DADOS.filter(d=>d.segmento==='CL'&&buscarMeta(d)).length,
  missingComparisons: BOLETINS.metas.filter(m=>m.ticket_alvo<m.ticket_minimo).length
})`, context);
assert.equal(report.metas, 70);
assert.equal(report.noMeta, null);
assert.ok(report.courses > 0);
assert.equal(report.missingComparisons, 0);
const data = JSON.parse(readFileSync('boletins.json','utf8'));
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(BOLETINS)',context)),data);
assert.equal(report.included, Object.values(data.status_alunos).reduce((sum,n)=>sum+n,0));
assert.match(data.data_ficha, /^\d{4}-\d{2}-\d{2}$/);
assert.equal(data.email_ativo, false);
const forbidden = /"(?:RA|ALUNO|CPF|CODPESSOAALUNO|destinatario|arquivo)"\s*:/i;
assert.equal(forbidden.test(JSON.stringify(data)), false);
assert.ok(html.includes('painel-metas'));
assert.doesNotMatch(html, /bolsoes|bolsao|renderBolsoes/i);
assert.equal(vm.runInContext('typeof PORTAS', context), 'undefined');
assert.ok(html.includes('Ticket projetado para recuperar a meta'));
assert.ok(html.includes('cm-total'));
assert.ok(html.includes('calculadora.html'));
assert.ok(html.includes('tickets.html'));
console.log('Checks passed:', JSON.stringify(report));
