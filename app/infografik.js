// Senaryo infografigi: A4, her senaryo bir sayfa + bir ozet sayfasi. node app/infografik.js  -> HEKIS_Senaryolar.pdf
const fs = require('fs');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const D = JSON.parse(fs.readFileSync(__dirname + '/scen_data.json'));
const nf = (v, d = 0) => v.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
const pc = (v, d = 0) => '%' + nf(v * 100, d);
const bn = (v, d = 1) => nf(v / 1e9, d);
const sg = (v, d) => (v > 0 ? '+' : v < 0 ? '−' : '') + nf(Math.abs(v), d);

const ORDER = ['baz', 'iyi', 'kotu', 'rf0', 'rf5', 'irl', 'huk', 'agir'];
const I = (id) => D.istanbul[id], A = (id) => D.anadolu[id];

const TXT = {
  baz: { flow: ['Reel fiyat düşüyor', 'Beklemek pahalı, havuz çekici', 'Hane yerleşir, bedel sübvansiyonu öder'], kat: 'Temel', story: 'Bugünkü verilerle sistem: boş konutu elde tutmak pahalı, havuza vermek çekici. Finansmanı lüks bedel taşır.',
    why: ['Reel konut fiyatı düşüyor (−%3,7): beklemenin getirisi yok, sahip havuza yönelir.', 'Katılım %20: havuza uygun boş stokun beşte biri gelir.', 'Lüks bedel (%5), toplam bedel gelirinin yaklaşık üçte ikisini sağlar. Sistem buna dayanır.'],
    watch: ['Lüks bedelin gerçek tahsilatı hiç ölçülmedi. İlk pilot önce bunu ölçer.', 'Reel faiz ve fiyat beklentisinin yönü.'] },
  iyi: { flow: ['Güçlü yaptırım, iyi tahsilat', 'Çok sahip havuza girer', 'Çok hane, daha ince marj'], kat: 'Olumlu', story: 'Yaptırım güçlü, tahsilat iyi: daha çok konut havuza girer, ama sübvansiyon da büyür.',
    why: ['Tahsilat %60 / %60 ve erozyon %10: bedel geliri yüksek.', 'Katılım tavanı %55 (gerçekleşen %44): çok daha fazla hane yerleşir.', 'Oran 1,72\'ye iner: yerleşen çoğaldıkça sübvansiyon büyür. Kapıdan yine de geçer.'],
    watch: ['Bu varsayımlar doğrulanmadı: %60 tahsilat için gözlem yok.', 'Yüksek yerleşme, idari kapasite ve tadilat ihtiyacını büyütür (modelde yok).'] },
  kotu: { flow: ['Katılım gönüllü, tahsilat zayıf', 'Katılım %6,5, kapı sınırı %15', 'Kapı geçilmez, sistem küçük kalır'], kat: 'Olumsuz', story: 'Katılım gönüllü ve tahsilat zayıf: sahip havuza gelmez. Sistem küçük kalır ama zarar etmez.',
    why: ['Katılım tavanı %8: gerçekleşen %6,5, kapının %15 alt sınırının altında.', 'Kapı geçilmez, sistem pilotta kalır.', 'Az hane yerleştiği için oran yüksek görünür (5,1), ama toplumsal etki yok.'],
    watch: ['Güvenli ama etkisiz: kayıp yok, kazanç da yok.', 'Katılımı artıracak tek araç bedeli yükseltmek; bunun kaçınma maliyeti var.'] },
  rf0: { flow: ['Reel faiz sıfır', 'Konutun değer saklama cazibesi döner', 'Katılım %14,8, kapı eşiğinin altında'], kat: 'Dış risk', story: 'Reel faiz sıfıra iner: mevduat cazibesini kaybeder, konut yeniden değer saklama aracı olur.',
    why: ['Faiz kanalı (2019-2025, n=7): reel faiz 0 iken beklenen reel konut artışı +%0,5.', 'Katılım %20,2\'den %14,8\'e düşer; kapının %15 sınırının hemen altı.', 'Kapı hiç geçilmezse sistem pilotta kalır.'],
    watch: ['Bugünkü ortam (reel faiz +%4) sistemin dışarıdan gelen avantajı.', 'Katılım alt sınırı (%15) benim kararım; sonuç buna duyarlı.'] },
  rf5: { flow: ['Reel faiz −%5', 'Beklemek kazançlı olur', 'Katılım %5, sistem çalışmaz'], kat: 'Dış risk', story: 'Reel faiz −%5: faiz konutu, dövizi ve altını cazip kılar. Katılım çöker.',
    why: ['Beklenen reel konut artışı ≈ +%7,2.', 'Sahip için havuza vermek yerine beklemek kazançlı: katılım %5\'e iner.', 'Sistem fiilen çalışmaz; kapı neredeyse hiç geçilmez.'],
    watch: ['Bu senaryo sistemi değil, makro ortamı sorgular.', 'Reel faiz negatifken konut dışı kaçış (döviz, altın) da artar.'] },
  irl: { flow: ['Tahsilat %10-15', 'Gelir sübvansiyonu karşılamaz', 'Kapı durdurur, pilotta kalınır'], kat: 'Uygulama riski', story: 'Bedel tahsil edilemez: lüks tahsilat %10, genel %15. İrlanda\'da işaretlenenin yalnız ~%6\'sı bedele tabi kaldı.',
    why: ['Lüks bedel sistemin gelirinin büyük kısmını taşır; tahsilat düşünce oran 0,78\'e iner.', 'Tam ölçekte sistem açık verir.', 'Kapı bunu görür ve büyümeyi durdurur: çoğu çekimde pilotta kalınır.'],
    watch: ['Pilotun asıl işi tam burada: büyük zarar oluşmadan durmak.', 'Tespit (elektrik tüketimi) ve yaptırım (tapuya şerh) kalitesi her şeyi belirler.'] },
  huk: { flow: ['Bedel 3. yılda iptal', 'Gelir biter, sübvansiyon sürer', 'Büyüme durur, yük ≈4 mr TL'], kat: 'Hukuki risk', story: 'Bedel 3. yılda tamamen iptal edilir (Anayasa md. 35 ve 73 itirazı). Yeni yerleştirme durur, yerleşmiş haneler korunur.',
    why: ['Gelir kaybolur, sübvansiyon sürer: net 10 yılda eksiye döner.', 'Kapı büyümeyi hemen durdurur; ölçek yaklaşık 2 bin haneyle sınırlı kalır.', 'Kademeli yürürlük kaybı yaklaşık 20 kat küçültür: 20 yıllık yük ≈4 mr TL, tam ölçekte ≈84 mr TL olurdu.'],
    watch: ['Lüks bedeli ayrı madde yapmak (ayrılabilirlik): yalnız lüks bedel iptali de neredeyse bu kadar zararlı.', 'Yerleşmiş hanelerin çıkarılamayacağı varsayıldı.'] },
  agir: { flow: ['Ralli + iptal + gelir erimesi', 'Katılım ve gelir birlikte çöker', 'Kapı durdurur, yük ≈1 mr TL'], kat: 'Birleşik şok', story: 'Fiyat rallisi, lüks bedelin iptali ve gelir erimesi birlikte gelir (3. yıldan itibaren).',
    why: ['Ralli katılımı çökertir; lüks bedel gelmez; hane geliri −%20.', 'Kapı büyümeyi durdurur, yük sınırlı kalır (20 yıl ≈1 mr TL).', 'Tek tek şoklardan farklı olarak üçü birleşince çekimlerin altıda biri zarar eder.'],
    watch: ['Kademeli kapı olmasaydı bu senaryo tam ölçekte yüz milyar TL mertebesinde yük bırakırdı.', 'Kur krizi ve sermaye çıkışı kurulmuş bir model değil, parametre vekili.'] },
};

function chart(rows, w = 360, h = 170) {
  const L = 34, R = 34, T = 10, B = 22, n = rows.length, bw = (w - L - R) / n;
  const small = Math.max(...rows.map(r => r.N)) < 3000, div = small ? 1 : 1000;
  const maxN = Math.max(1, ...rows.map(r => r.N)) / div;
  const nice = (v) => { const p = Math.pow(10, Math.floor(Math.log10(v))); const m = v / p; return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p; };
  const yN = nice(maxN);
  const cmin = Math.min(0, ...rows.map(r => r.cum / 1e9)), cmax = Math.max(0.2, ...rows.map(r => r.cum / 1e9));
  const sy = (v) => T + (h - T - B) * (1 - v / yN);
  const cy = (v) => T + (h - T - B) * (1 - (v - cmin) / (cmax - cmin));
  let s = `<svg viewBox="0 0 ${w} ${h}" width="100%">`;
  for (let i = 0; i <= 4; i++) { const v = yN * i / 4, y = sy(v); s += `<line x1="${L}" x2="${w - R}" y1="${y}" y2="${y}" stroke="#d5dedb" stroke-width=".7"/><text x="${L - 4}" y="${y + 3}" text-anchor="end">${nf(v, v < 10 && !small ? 1 : 0)}</text>`; }
  rows.forEach((r, i) => {
    const x = L + i * bw + bw * .18, ww = bw * .64, y = sy(r.N / div);
    s += `<rect x="${x}" y="${y}" width="${ww}" height="${Math.max(0, h - B - y)}" fill="${r.gecti ? '#0e6b62' : '#c4861c'}" rx="1.5"/><text x="${x + ww / 2}" y="${h - 8}" text-anchor="middle">${r.yil}</text>`;
  });
  s += `<polyline points="${rows.map((r, i) => `${L + i * bw + bw / 2},${cy(r.cum / 1e9)}`).join(' ')}" fill="none" stroke="#17302d" stroke-width="1.6"/>`;
  const z = cy(0); s += `<line x1="${L}" x2="${w - R}" y1="${z}" y2="${z}" stroke="#17302d" stroke-width=".5" stroke-dasharray="3 2"/>`;
  s += `<text x="${w - R + 3}" y="${cy(rows[n - 1].cum / 1e9) + 3}">${nf(rows[n - 1].cum / 1e9, 1)}</text><text x="${L}" y="7">${small ? 'hane' : 'bin hane'}</text><text x="${w - R}" y="7" text-anchor="end">mr TL</text></svg>`;
  return s;
}
function probBar(mc, label) {
  const mid = Math.max(0, 1 - mc.full - mc.stuck);
  return `<div class="pb"><div class="pl">${label}</div><div class="bar"><span style="width:${mc.full * 100}%;background:#0e6b62">${mc.full >= .1 ? pc(mc.full) : ''}</span><span style="width:${mid * 100}%;background:#9fb9b4;color:#17302d">${mid >= .1 ? pc(mid) : ''}</span><span style="width:${mc.stuck * 100}%;background:#c4861c">${mc.stuck >= .1 ? pc(mc.stuck) : ''}</span></div></div>`;
}
const tile = (k, v, s, c = '') => `<div class="tile ${c}"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`;

function page(i, id) {
  const a = I(id), b = A(id), t = TXT[id];
  const s = a.s;
  const assum = [['Katılım tavanı', pc(s.cap / 100)], ['Beklenen reel artış', sg(s.ge, 1) + '%'], ['Tahsilat genel / lüks', `${s.coll}% / ${s.lcoll}%`], ['Erozyon', `${s.eros}%`], ['Şok', s.shock === 'yok' ? 'yok' : 'var (3. yıl)']];
  const ratioCls = a.full.ratio >= 1.25 ? 'ok' : a.full.ratio >= 1 ? 'warn' : 'bad';
  const dens = a.soc.N10 > 5000;
  return `<section class="page">
  <div class="top"><span class="num">${i + 1}</span><div><div class="kat">${t.kat}</div><h1>${a.ad}</h1></div></div>
  <p class="story">${t.story}</p>
  <div class="flow">${t.flow.map((x, j) => `<div class="fb f${j}"><small>${['TETİKLEYİCİ', 'MEKANİZMA', 'SONUÇ'][j]}</small>${x}</div>`).join('<span class="ar">▶</span>')}</div>
  <div class="assum">${assum.map(x => `<div><b>${x[0]}</b>${x[1]}</div>`).join('')}</div>
  <div class="tiles">
    ${tile('Katılım (tam ölçek)', pc(a.full.p, 1), (s.shock === 'yok' ? '' : 'şoksuz; ') + (a.full.p >= .15 ? 'kapı eşiği %15 üstünde' : 'kapı eşiği %15 altında'), a.full.p >= .15 ? 'ok' : 'bad')}
    ${tile('Tam ölçekte hane', nf(a.full.N), `${s.shock === 'yok' ? '' : 'şoksuz; '}Anadolu: ${nf(b.full.N)}`)}
    ${tile('Bedel / sübvansiyon', nf(a.full.ratio, 2), (s.shock === 'yok' ? '' : 'şoksuz; ') + (a.full.ratio >= 1.25 ? 'eşik 1,25 üstünde' : a.full.ratio >= 1 ? 'sınırda' : 'sistem açık veriyor'), ratioCls)}
    ${tile('10 yıl net, medyan', bn(a.mc.net) + ' mr TL', `P10 ${bn(a.mc.p10)} / P90 ${bn(a.mc.p90)}`)}
  </div>
  <div class="row2">
    <div class="box"><h3>10 yıllık yol (kusursuz ölçüm)</h3>${chart(a.rows, 380, 235)}<div class="lg"><i style="background:#0e6b62"></i>kapı geçti <i style="background:#c4861c"></i>kapı durdurdu <i style="background:#17302d;height:2px;vertical-align:3px"></i>kümülatif net</div></div>
    <div class="box"><h3>Belirsizlik: 300 rastgele çekim</h3>
      ${probBar(a.mc, 'İstanbul')}${probBar(b.mc, 'Anadolu')}
      <div class="lg"><i style="background:#0e6b62"></i>10. yılda tam ölçek <i style="background:#9fb9b4"></i>arada <i style="background:#c4861c"></i>pilotta takılır</div>
      <div class="mini"><b>Zarar eden çekim:</b> İstanbul ${pc(a.mc.deficit)}, Anadolu ${pc(b.mc.deficit)}</div></div>
  </div>
  <div class="row3">
    <div class="box"><h3>Neden böyle?</h3><ul>${t.why.map(x => `<li>${x}</li>`).join('')}</ul></div>
    <div class="box"><h3>Yaşamda ne değişir? (10. yıl)</h3>
      ${dens ? `<ul><li>${nf(a.soc.N10)} hane yerleşir, hane başına ayda ${nf(a.soc.B / 12)} TL fayda.</li><li>Gini ${sg(a.soc.dGini, 4)}, yoksulluk ${sg(a.soc.dPov, 2)} puan.</li><li>İstanbul kirası ${sg(a.soc.rent * 100, 1)}%, yerel TÜFE ${sg(a.soc.cpi, 2)} puan, ulusal ${sg(a.soc.cpiNat, 3)} puan.</li></ul>`
        : `<ul><li>Yalnızca ${nf(a.soc.N10)} hane yerleşir.</li><li>Gini ve yoksulluk fiilen değişmez; kira ve TÜFE etkisi ihmal edilebilir (TÜFE ${sg(a.soc.cpi, 3)} puan).</li><li>Sistem varlığını sürdürür ama toplumsal etkisi yoktur.</li></ul>`}</div>
    <div class="box"><h3>Ne izlenmeli?</h3><ul>${t.watch.map(x => `<li>${x}</li>`).join('')}</ul></div>
  </div>
  <div class="foot">HEKİS modeli, İstanbul (kalın) ve Anadolu 7 büyükşehir; kişisel modelleme, doğrulanmış kamu maliyesi modeli değil. Sayılar varsayımlara bağlı.  Sayfa ${i + 2}</div>
</section>`;
}

function summary() {
  const rows = ORDER.map(id => { const a = I(id), b = A(id); return `<tr><td><b>${a.ad}</b></td><td>${pc(a.full.p, 1)}</td><td>${nf(a.full.N)}</td><td>${nf(a.full.ratio, 2)}</td><td>${pc(a.mc.full)}</td><td>${pc(a.mc.stuck)}</td><td>${bn(a.mc.net)}</td><td>${pc(b.mc.full)}</td><td>${pc(b.mc.stuck)}</td></tr>`; }).join('');
  return `<section class="page">
  <div class="top"><span class="num" style="background:#17302d">★</span><div><div class="kat">Özet</div><h1>HEKİS senaryo haritası</h1></div></div>
  <p class="story">Sistem tek bir sonuç vermez; iki şeye bağlıdır: <b>sahibin havuza verme isteği (katılım)</b> ve <b>bedelin gerçekten tahsil edilmesi</b>. Aşağıdaki sekiz senaryo bu iki ayağı ve dış şokları sırayla sınar.</p>
  <div class="tw"><table><tr><th>Senaryo</th><th>Katılım</th><th>Tam ölçek hane</th><th>Bedel/sübv.</th><th>İst. tam ölçek</th><th>İst. takılma</th><th>İst. 10y net (mr)</th><th>Anad. tam ölçek</th><th>Anad. takılma</th></tr>${rows}</table></div>
  <div class="box"><h3>10. yılda tam ölçeğe ulaşma olasılığı</h3><div class="sbar">${ORDER.map(id => `<div>${I(id).ad}</div><div><div class="sb"><i style="width:${I(id).mc.full * 100}%;background:#0e6b62"></i><em>İstanbul ${pc(I(id).mc.full)}</em></div><div class="sb"><i style="width:${A(id).mc.full * 100}%;background:#7fa9a2"></i><em>Anadolu ${pc(A(id).mc.full)}</em></div></div>`).join('')}</div></div>
  <div class="row2" style="margin-top:0;flex:none">
    <div class="box"><h3>Nasıl okunur?</h3><ul>
      <li><b>Katılım:</b> havuza uygun boş stokun gerçekleşen payı. Kapı için en az %15.</li>
      <li><b>Bedel/sübvansiyon:</b> 1,25 üstü yeterli, 1-1,25 sınırda, 1 altı açık.</li>
      <li><b>Tam ölçek / takılma:</b> 10. yılda tüm şehre ulaşan / pilotta kalan çekimlerin payı.</li>
      <li>Her yıl bir kapı: eşikler tutmazsa kapsam büyümez.</li></ul></div>
    <div class="box"><h3>Üç ana çıkarım</h3><ul>
      <li>Sistem finansal olarak şokta ayakta kalır, çünkü kademeli kapı büyümeyi durdurur. Ama durunca küçük kalır.</li>
      <li>Zayıf halka lüks bedelin tahsilatı ve hukuki dayanağı; ikisi de ölçülmedi.</li>
      <li>Katılım bugünkü ortama bağlı: reel faiz sıfıra ya da fiyat beklentisi yukarı dönerse sistem boşalır.</li></ul></div>
  </div>
  <div class="foot">HEKİS modeli; kişisel modelleme. İstanbul %1/%5, Anadolu %0,5/%3 bedel tarifesi. 300 rastgele çekim, ±3 puan örnekleme hatası.  Sayfa 1</div>
</section>`;
}

const CSS = `
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Liberation Sans', 'DejaVu Sans', Arial, sans-serif; color: #17302d; font-size: 12px; line-height: 1.4; }
.page { width: 210mm; height: 297mm; padding: 13mm 14mm 14mm; page-break-after: always; position: relative; background: #f6f8f7; overflow: hidden; display: flex; flex-direction: column; gap: 9px; }
.page:last-child { page-break-after: auto; }
.top { display: flex; align-items: center; gap: 12px; border-bottom: 2.5px solid #0e6b62; padding-bottom: 9px; }
.num { width: 46px; height: 46px; border-radius: 50%; background: #0e6b62; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 23px; font-weight: 700; flex: none; }
.kat { font-size: 10px; text-transform: uppercase; letter-spacing: .12em; color: #5a6f6b; }
h1 { margin: 0; font-size: 29px; line-height: 1.1; font-family: 'Liberation Serif', 'DejaVu Serif', serif; }
.story { font-size: 14.2px; margin: 2px 0 0; max-width: 180mm; }
.flow { display: flex; align-items: stretch; gap: 5px; }
.fb { flex: 1; background: #fff; border: 1px solid #d5dedb; border-radius: 6px; padding: 7px 9px; font-size: 11.6px; font-weight: 600; }
.fb small { display: block; font-size: 8.6px; letter-spacing: .1em; color: #5a6f6b; font-weight: 600; margin-bottom: 2px; }
.fb.f0 { border-left: 4px solid #b87613; } .fb.f1 { border-left: 4px solid #5a6f6b; } .fb.f2 { border-left: 4px solid #0e6b62; }
.ar { align-self: center; color: #0e6b62; font-size: 11px; }
.assum { display: flex; gap: 6px; }
.assum div { flex: 1; background: #e3eeec; border-radius: 4px; padding: 4px 8px; font-size: 10.6px; }
.assum b { display: block; font-weight: 600; color: #5a6f6b; font-size: 8.8px; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.tile { background: #fff; border: 1px solid #d5dedb; border-radius: 6px; padding: 8px 10px; border-top: 4px solid #0e6b62; }
.tile.ok { border-top-color: #2b7a4b; } .tile.warn { border-top-color: #b87613; } .tile.bad { border-top-color: #ae3a32; }
.tile .k { font-size: 10px; color: #5a6f6b; } .tile .v { font-size: 25px; font-weight: 700; font-family: 'DejaVu Sans Mono', monospace; letter-spacing: -.03em; } .tile .s { font-size: 9.6px; color: #5a6f6b; }
.row2 { display: grid; grid-template-columns: 1.2fr 1fr; gap: 8px; flex: 1.25; }
.row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; flex: 1; }
.box { background: #fff; border: 1px solid #d5dedb; border-radius: 6px; padding: 9px 11px; }
.box h3 { margin: 0 0 6px; font-size: 11.4px; text-transform: uppercase; letter-spacing: .06em; color: #0e6b62; }
.box ul { margin: 0; padding-left: 14px; } .box li { margin-bottom: 4px; font-size: 11.4px; }
svg text { font-size: 8.4px; fill: #5a6f6b; font-family: 'DejaVu Sans Mono', monospace; }
.lg { font-size: 9.2px; color: #5a6f6b; margin-top: 4px; } .lg i { display: inline-block; width: 9px; height: 9px; border-radius: 2px; margin: 0 4px 0 8px; } .lg i:first-child { margin-left: 0; }
.pb { margin-bottom: 11px; } .pl { font-size: 10.6px; font-weight: 600; margin-bottom: 3px; }
.bar { display: flex; height: 26px; border-radius: 5px; overflow: hidden; background: #e3eeec; }
.bar span { color: #fff; font-size: 11.4px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.mini { margin-top: 10px; font-size: 11px; }
.foot { margin-top: auto; font-size: 8.8px; color: #5a6f6b; border-top: 1px solid #d5dedb; padding-top: 5px; }
table { border-collapse: collapse; width: 100%; font-size: 10.6px; } th, td { padding: 7px 6px; border-bottom: 1px solid #d5dedb; text-align: right; } th:first-child, td:first-child { text-align: left; } th { font-size: 9px; color: #5a6f6b; background: #e3eeec; }
td { font-family: 'DejaVu Sans Mono', monospace; } td:first-child { font-family: inherit; }
.sbar { display: grid; grid-template-columns: 130px 1fr; gap: 6px 10px; align-items: center; font-size: 11px; }
.sb { height: 13px; background: #e3eeec; border-radius: 3px; position: relative; margin: 2px 0; } .sb i { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; }
.sb em { position: absolute; right: 4px; top: -1px; font-size: 9.6px; font-style: normal; font-weight: 700; }
`;
(async () => {
  const html = `<!doctype html><html lang="tr"><head><meta charset="utf-8"><style>${CSS}</style></head><body>${summary()}${ORDER.map((id, i) => page(i, id)).join('')}</body></html>`;
  fs.writeFileSync(__dirname + '/senaryolar.html', html);
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const p = await b.newPage();
  await p.setContent(html, { waitUntil: 'load' });
  await p.pdf({ path: __dirname + '/../HEKIS_Senaryolar.pdf', format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await b.close();
  console.log('PDF yazildi');
})();
