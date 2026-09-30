import {mkdirSync,copyFileSync} from 'node:fs';
// Only approved static assets are published. No spreadsheets, scripts, docs or local config.
mkdirSync('dist', {recursive:true});
for (const file of ['index.html','dados.js','boletins.js','metas.js']) copyFileSync(file, 'dist/'+file);
console.log('Static build: 4 public files.');
