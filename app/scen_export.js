// Senaryo sayfalari icin veri: her sistem x senaryo (kusursuz yol, 300 cekim MC, 10. yil sosyal etki)
const fs = require('fs');
const K = JSON.parse(fs.readFileSync(__dirname + '/constants.json'));
const H = require('./model.js'); const M = H.make(K);
const DEF = (s) => ({ fee: s.tarife[0] * 100, lux: s.tarife[1] * 100, growth: 2.5, cap: 25, ge: -3.7, coll: 30, lcoll: 40, eros: 25, elas: 0.6, shock: 'yok' });
const SCEN = [
  { id: 'baz', ad: 'En olası', o: {} },
  { id: 'iyi', ad: 'İyimser', o: { cap: 55, coll: 60, lcoll: 60, eros: 10 } },
  { id: 'kotu', ad: 'Kötümser', o: { cap: 8, coll: 15, lcoll: 30, eros: 40 } },
  { id: 'rf0', ad: 'Reel faiz sıfıra iner', o: { ge: 0.5 } },
  { id: 'rf5', ad: 'Reel faiz −%5', o: { ge: 7.2 } },
  { id: 'irl', ad: 'Tahsilat İrlanda gibi', o: { coll: 15, lcoll: 10 } },
  { id: 'huk', ad: 'Hukuki iptal', o: { shock: 'Bedel iptali (hukuki, tum bedel)' } },
  { id: 'agir', ad: 'Ağır kriz', o: { shock: 'Agir kriz (ralli + luks iptali + gelir erimesi)' } },
];
const out = {};
for (const key of ['istanbul', 'anadolu']) {
  const sys = K.sistem[key]; out[key] = {};
  for (const sc of SCEN) {
    const s = { ...DEF(sys), ...sc.o };
    const st = { g_e: s.ge / 100, cap: s.cap / 100, coll: s.coll / 100, lux_coll: s.lcoll / 100, fee: s.fee / 100, lux_fee: s.lux / 100, inc: 1, alpha: 1, cost: 1 };
    const full = M.runSystem(sys, st, sys.full);
    const shock = H.SHOCKS[s.shock]; const sk = Object.keys(shock).length ? shock : null;
    const opt = { erosion: s.eros / 100, growth: s.growth, years: 10, tariff: [st.fee, st.lux_fee] };
    const P0 = { g_e: st.g_e, cap: st.cap, coll: st.coll, lux_coll: st.lux_coll };
    const rows = M.onePath(sys, P0, null, sk, opt); let cum = 0; rows.forEach(r => { cum += r.rev - r.sub; r.cum = cum; });
    const sm = M.summarize(M.monteCarlo(sys, 300, 11, sk, opt, P0), sys);
    const r10 = rows[9], B = r10.N > 0 ? r10.sub / r10.N : 0;
    const g = M.giniBenefit(r10.N, B, sys.households, 2000);
    const c = M.costOfLiving(sys, r10.N, r10.freed, 0.6);
    out[key][sc.id] = { ad: sc.ad, s, full: { N: full.N, ratio: full.ratio, sub: full.sub, rev: full.rev, p: full.p, coverage: full.coverage }, rows: rows.map(r => ({ yil: r.yil, stok: r.stok, N: r.N, cum: r.cum, gecti: r.gecti, ratio: r.ratio })),
      mc: { full: sm.full, stuck: sm.stuck, net: sm.net, p10: sm.p10, p90: sm.p90, deficit: sm.deficit }, soc: { dGini: g.g1 - g.g0, dPov: (g.p1 - g.p0) * 100, B, rent: c.rent[0], cpi: c.cpi[0], cpiNat: c.cpiNat[0], N10: r10.N, cov10: r10.coverage } };
  }
}
fs.writeFileSync(__dirname + '/scen_data.json', JSON.stringify(out));
console.log('ok', Object.keys(out.istanbul).length, 'senaryo');
