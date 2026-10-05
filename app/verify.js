// JS modelini Python ciktisiyla karsilastirir. Kullanim: python3 -m hekis.verify_app > app/expected.json && node app/verify.js
const fs = require('fs');
const K = JSON.parse(fs.readFileSync(__dirname + '/constants.json'));
const X = JSON.parse(fs.readFileSync(__dirname + '/expected.json'));
const M = require('./model.js').make(K);
let worst = 0, n = 0;
for (const t of X.zone) {
  const sys = K.sistem[t.sistem];
  const z = M.runSystem(sys, t.st, t.size);
  for (const k of ['N', 'sub', 'rev', 'ratio']) {
    const e = Math.abs(z[k] - t[k]) / Math.max(Math.abs(t[k]), 1e-9);
    if (e > worst) worst = e; n++;
    if (e > 0.01) console.log('FARK', t.sistem, k, z[k], t[k], JSON.stringify(t.st));
  }
}
console.log('zone: ' + X.zone.length + ' nokta, en buyuk goreli hata ' + (worst * 100).toFixed(3) + '%');
let w2 = 0;
for (const t of X.path) {
  const sys = K.sistem[t.sistem];
  const rows = M.onePath(sys, {}, null, t.shock ? require('./model.js').SHOCKS[t.shock] : null, { years: 10 });
  rows.forEach((r, i) => { const e = Math.abs(r.N - t.rows[i].N) / Math.max(t.rows[i].N, 1); if (e > w2) w2 = e; if (e > 0.01) console.log('YOL FARK', t.sistem, t.shock, i + 1, r.N, t.rows[i].N); });
}
console.log('yol: ' + X.path.length + ' yol, en buyuk goreli hata ' + (w2 * 100).toFixed(3) + '%');
const g = M.giniBenefit(X.gini.N, X.gini.B, X.gini.households);
console.log('gini js', g.g0.toFixed(4), g.g1.toFixed(4), 'py', X.gini.g0.toFixed(4), X.gini.g1.toFixed(4), '| yoksulluk js', g.p0.toFixed(4), g.p1.toFixed(4), 'py', X.gini.p0.toFixed(4), X.gini.p1.toFixed(4));
process.exit(worst < 0.01 && w2 < 0.01 ? 0 : 1);
