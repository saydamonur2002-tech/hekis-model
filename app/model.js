// HEKIS modeli, JS portu. hekis/zones.py run_three_zone ilk yil hesabi + hekis/horizon.py kademe/kapi/sok + social etkisi.
// Sabitler constants.json'dan (hekis/export_app.py). Dogrulama: node app/verify.js
(function (root) {
  const LIKELY = { g_e: -0.037, cap: 0.25, coll: 0.30, lux_coll: 0.40 };
  const SPACE = { g_e: [-0.15, 0.15], cap: [0.10, 0.60], coll: [0.15, 0.90], lux_coll: [0.30, 0.90] };
  const START = 3800, YEARS_DEFAULT = 10, SHOCK_YEAR = 3, SAFETY = 1.25, P_RANGE = [0.15, 0.38], TENANT_MIN = 0.80, INCOME_MIN = 0.85;
  const SHOCKS = {
    'yok': {},
    'Fiyat rallisi (beklenen reel artis +10 puan)': { g_e_add: 0.10 },
    'Luks tahsilat cokusu (x0,4)': { lux_mult: 0.4 },
    'Genel tahsilat cokusu (x0,5)': { coll_mult: 0.5 },
    'Enflasyon sokunu (+10 puan)': { infl: 0.10 },
    'Hane geliri -%30': { inc_mult: 0.7 },
    'Bedel iptali (hukuki, tum bedel)': { lux_mult: 0, coll_mult: 0 },
    'Kismi iptal (yalniz luks bedel)': { lux_mult: 0 },
    'Gelir erimesi (hane -%20, kiraci tahsilat x0,8)': { inc_mult: 0.8, alpha_mult: 0.8 },
    'Kur krizi + sermaye cikisi': { cost_mult: 1.3, g_e_add: 0.10, lux_mult: 0.7 },
    'Agir kriz (ralli + luks iptali + gelir erimesi)': { g_e_add: 0.10, lux_mult: 0, inc_mult: 0.8, alpha_mult: 0.8 },
  };

  function make(K) {
    const S = K.sabit;
    const luxResp = (fee, cap = S.lux_cap) => cap * (1 - Math.exp(-fee * 100 / S.lux_fs));
    const effColl = (fee, coll) => Math.max(0, coll - S.avoid_slope * Math.max(0, fee * 100 - S.avoid_start * 100));
    const pos = (grid, x) => {
      if (x <= grid[0]) return [0, 0];
      if (x >= grid[grid.length - 1]) return [grid.length - 2, 1];
      let i = 0; while (grid[i + 1] < x) i++;
      return [i, (x - grid[i]) / (grid[i + 1] - grid[i])];
    };
    function interpB(B, inc, alpha, cost) {
      const [i, ti] = pos(K.inc, inc), [j, tj] = pos(K.alpha, alpha), [k, tk] = pos(K.cost, cost);
      let v = 0;
      for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) for (let c = 0; c < 2; c++)
        v += (a ? ti : 1 - ti) * (b ? tj : 1 - tj) * (c ? tk : 1 - tk) * B[i + a][j + b][k + c];
      return v;
    }
    // st: {g_e, cap, coll, lux_coll, fee, lux_fee, inc, alpha, cost}; size: sistem toplam bos stok olcegi
    function runSystem(sys, st, size) {
      const sc = size / sys.full;
      let N = 0, sub = 0, rev = 0, Sh = 0, Sb = 0, Sl = 0, freed = 0;
      const respB = luxResp(st.fee), respL = luxResp(st.lux_fee);
      for (const c of sys.sehirler) {
        const stok = c.stok * sc;
        const g = c.g_base + (st.g_e - LIKELY.g_e);
        const hold = c.hold[0] + (c.hold[1] - c.hold[0]) * Math.min(1, Math.max(0, (st.cost - 1) / 0.3));
        const p = st.cap / (1 + Math.exp(-S.slope * (hold + st.fee - g)));
        const sh = stok * c.fS[0], sb = stok * c.fS[1], sl = stok * c.fS[2];
        const n = sh * p;
        const rPool = sh * (1 - p) * c.V[0] * st.fee * st.coll;
        const rBuf = sb * (1 - respB) * c.V[1] * st.fee * effColl(st.fee, st.coll);
        const rLux = sl * (1 - respL) * c.V[2] * st.lux_fee * effColl(st.lux_fee, st.lux_coll);
        N += n; rev += rPool + rBuf + rLux; Sh += sh; Sb += sb; Sl += sl;
        sub += n * interpB(c.B, st.inc, st.alpha, st.cost);
        freed += sb * respB + sl * respL;
      }
      return { N, sub, rev, ratio: sub > 0 ? rev / sub : 0, p: Sh > 0 ? N / Sh : 0, S: [Sh, Sb, Sl], freed, coverage: N / sys.eligible };
    }
    // ---- sosyal etki
    function invNorm(p) { // Acklam
      const a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00];
      const b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01];
      const c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00];
      const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
      const pl = 0.02425;
      if (p < pl) { const q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
      if (p > 1 - pl) { const q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
      const q = p - 0.5, r = q * q;
      return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    const hhMonthly = (q) => Math.exp(S.mu + S.sigma * invNorm(q)) * S.eq / 12 * S.uplift;
    function giniBenefit(N, B, households, grid = 2000) {
      const phi = Math.min(1, N / (0.4 * households));
      const base = [], after = [];
      for (let i = 0; i < grid; i++) {
        const q = (i + 0.5) / grid, inc = hhMonthly(q) * 12, w = 1 / grid;
        base.push([inc, w]);
        if (q < 0.4) { after.push([inc + B, w * phi]); after.push([inc, w * (1 - phi)]); } else after.push([inc, w]);
      }
      const line = 0.5 * hhMonthly(0.5) * 12;
      const gini = (cells) => {
        cells = cells.slice().sort((x, y) => x[0] - y[0]);
        let tw = 0, ty = 0; for (const [i, w] of cells) { tw += w; ty += i * w; }
        let cy = 0, area = 0;
        for (const [i, w] of cells) { const y = i * w; area += (cy + y / 2) * w; cy += y; }
        return 1 - 2 * area / (tw * ty);
      };
      const pov = (cells) => cells.reduce((a, [i, w]) => a + (i < line ? w : 0), 0) / cells.reduce((a, [, w]) => a + w, 0);
      return { g0: gini(base), g1: gini(after), p0: pov(base), p1: pov(after) };
    }
    function costOfLiving(sys, N, freed, elasticity) {
      const tenants = sys.households * S.tenant_share;
      const demand = N / tenants, both = (N + S.rented * freed) / tenants;
      const nat = sys.households / S.national_hh;
      const cpi = [S.w_kira * -demand / elasticity * 100, S.w_kira * -both / elasticity * 100];
      return { demand, both, rent: [-demand / elasticity, -both / elasticity], cpi, cpiNat: cpi.map(x => x * nat), natShare: nat };
    }
    // ---- kademeli yol
    function mulberry(seed) { let a = seed >>> 0; return () => { a += 0x6D2B79F5; let t = a; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    function gauss(rng) { let u = 0, v = 0; while (!u) u = rng(); while (!v) v = rng(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
    const tri = (rng, lo, hi, mode) => { const u = rng(), c = (mode - lo) / (hi - lo); return u < c ? lo + Math.sqrt(u * (hi - lo) * (mode - lo)) : hi - Math.sqrt((1 - u) * (hi - lo) * (hi - mode)); };
    const binom = (rng, p, n) => Math.min(1, Math.max(0, p + gauss(rng) * Math.sqrt(Math.max(p * (1 - p), 1e-6) / Math.max(n, 1))));
    function applyShock(P, sh) {
      const o = { ...P };
      o.g_e = P.g_e + (sh.g_e_add || 0);
      o.lux_coll = P.lux_coll * (sh.lux_mult ?? 1);
      o.coll = P.coll * (sh.coll_mult ?? 1);
      if (sh.cost_mult) o.cost = sh.cost_mult;
      if (sh.alpha_mult) o.alpha = sh.alpha_mult;
      if (sh.inc_mult) o.inc = sh.inc_mult;
      return o;
    }
    function onePath(sys, P0, rng, shock, opt = {}) {
      const erosion = opt.erosion ?? 0.25, growth = opt.growth ?? 2.5, years = opt.years ?? YEARS_DEFAULT;
      const tariff = opt.tariff || sys.tarife;
      const P = { ...LIKELY, ...P0 };
      const rows = []; let size = START;
      for (let y = 1; y <= years; y++) {
        let Pt = { ...P, fee: tariff[0], lux_fee: tariff[1], inc: P.inc ?? 1, alpha: P.alpha ?? 1, cost: P.cost ?? 1 };
        if (shock && y >= SHOCK_YEAR) Pt = applyShock(Pt, shock);
        const f = 1 - erosion * Math.log(Math.max(size, START) / START) / Math.log(sys.full / START);
        Pt.coll *= f; Pt.lux_coll *= f;
        const z = runSystem(sys, Pt, size);
        const nLux = z.S[2] * (1 - luxResp(Pt.lux_fee));
        const nGen = z.S[0] * (1 - z.p) + z.S[1] * (1 - luxResp(Pt.fee));
        rows.push({ yil: y, stok: size, N: z.N, sub: z.sub, rev: z.rev, ratio: z.ratio, p: z.p, freed: z.freed, coverage: z.coverage });
        const nHh = Math.max(z.N, 1), cTrue = Math.min(1, Pt.alpha), incTrue = Pt.inc;
        let oG, oL, oP, oC, oI;
        if (!rng) { oG = Pt.coll; oL = Pt.lux_coll; oP = z.p; oC = cTrue; oI = incTrue; }
        else {
          oG = binom(rng, Pt.coll, nGen); oL = binom(rng, Pt.lux_coll, nLux); oP = binom(rng, z.p, z.S[0]);
          oC = binom(rng, cTrue, nHh); oI = incTrue * Math.exp(gauss(rng) * 0.803 / Math.sqrt(nHh));
        }
        const zo = runSystem(sys, { ...Pt, coll: oG, lux_coll: oL, alpha: oC, inc: oI }, size);
        const passed = zo.ratio >= SAFETY && oP >= P_RANGE[0] && oP <= P_RANGE[1] && oC >= TENANT_MIN && oI >= INCOME_MIN;
        rows[rows.length - 1].gecti = passed;
        if (passed) size = Math.min(sys.full, size * growth);
      }
      return rows;
    }
    function draw(rng) { const o = {}; for (const k of Object.keys(SPACE)) o[k] = tri(rng, SPACE[k][0], SPACE[k][1], LIKELY[k]); return o; }
    function monteCarlo(sys, n, seed, shock, opt) {
      const rng = mulberry(seed || 11); const out = [];
      for (let i = 0; i < n; i++) out.push(onePath(sys, draw(rng), rng, shock, opt));
      return out;
    }
    const med = (a) => { const s = a.slice().sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
    const pct = (a, q) => { const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(q * s.length))]; };
    function summarize(paths, sys) {
      const n = paths.length, T = paths[0].length;
      const net = paths.map(p => p.reduce((a, r) => a + r.rev - r.sub, 0));
      const yearly = [];
      for (let t = 0; t < T; t++) yearly.push({ yil: t + 1, N: med(paths.map(p => p[t].N)), full: paths.filter(p => p[t].stok >= sys.full).length / n, stuck: paths.filter(p => p[t].stok <= START).length / n });
      return { net: med(net), p10: pct(net, 0.1), p90: pct(net, 0.9), deficit: net.filter(x => x < 0).length / n, yearly, stuck: yearly[T - 1].stuck, full: yearly[T - 1].full };
    }
    return { runSystem, giniBenefit, costOfLiving, onePath, monteCarlo, summarize, draw, mulberry, luxResp, effColl, LIKELY, SHOCKS, START };
  }
  const api = { make, LIKELY, SHOCKS, START };
  if (typeof module !== 'undefined') module.exports = api; else root.HEKIS = api;
})(typeof window !== 'undefined' ? window : globalThis);
