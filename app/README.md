# HEKİS Simülatörü (app)

Tek dosya, bağımlılıksız web uygulaması: `app/index.html` (tarayıcıda aç; telefonda da çalışır).

- Model: `app/model.js` (Python modelinin ilk yıl hesabı + kademeli yol + kapı + şok + sosyal etki), sabitler `app/constants.json`.
- Yeniden üret: `python -m hekis.export_app && python app/build.py`
- Doğrula: `python -m hekis.verify_app && node app/verify.js` (80 rastgele nokta, en büyük fark %0,7; kusursuz yollar birebir).
- Sınır: iç tutarlılık modeli; lüks tahsilat ve boş stok varsayımdır.
