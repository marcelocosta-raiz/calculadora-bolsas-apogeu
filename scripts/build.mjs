import {mkdirSync,copyFileSync} from 'node:fs';
// Only approved static assets are published. No spreadsheets, scripts, docs or local config.
mkdirSync('dist', {recursive:true});
for (const file of ['index.html','dados.js','boletins.js','metas.js','pricing.js','calculadora.js']) copyFileSync(file, 'dist/'+file);
for(const page of ['calculadora.html','tickets.html']) copyFileSync('index.html','dist/'+page);
console.log('Static build: 8 public files.');
