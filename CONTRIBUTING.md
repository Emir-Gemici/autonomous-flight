# Katkı rehberi

Kanonik kaynak kodu `autonomous_flight_Py/` klasöründedir. Repo kökündeki eski `autonomous_flight/` kopyası yerel arşivdir ve Git tarafından yok sayılır.

## Çalışma ortamı

Python 3.11–3.13 ile sanal ortam oluşturup `requirements.txt` bağımlılıklarını kurun. GStreamer ile çalışacaksanız README'deki ayrı görev ortamı açıklamasını izleyin.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Değişiklik hazırlama

1. Amacı belli bir dal açın: `git switch -c fix/kisa-aciklama`.
2. İlgili kaynak ve açıklamaları birlikte güncelleyin.
3. Algoritma veya görev davranışı değişiyorsa donanım kullanmayan anlamlı bir test ekleyin.
4. Aşağıdaki kontrolleri çalıştırın.
5. Pull request açıklamasında değişen davranışı ve gerçekten doğruladığınız ortamı belirtin.

```bash
python -m compileall -q autonomous_flight_Py examples tests
python -m unittest discover -s tests -v
git diff --check
```

## Proje kuralları

- Python dosyalarında UTF-8, dört boşluk ve açıklayıcı isimler kullanın.
- Birim testlerinde araç bağlantısı, kamera, gerçek süreç veya ağ başlatmayın. Sentetik görüntüler ve sahte bağımlılıklar kullanın.
- Renk eşikleri, koordinat çerçeveleri ve rota değişikliklerinde birimleri ve varsayımları açıklayın.
- Uçuş doğrulaması ile birim testi sonuçlarını ayrı belirtin. CI'nin geçmesi görevin uçuşta doğrulandığı anlamına gelmez.
- `.venv/`, `Monitor_logs/`, videolar, kimlik bilgileri ve IDE ayarlarını commit etmeyin.
- Kişisel kayıt ve görüntüleri hata raporuna eklemeden önce paylaşım kapsamını kontrol edin.

## Hata raporu

Python ve işletim sistemi sürümünü, çalıştırılan komutu, hata çıktısını ve beklenen davranışı ekleyin. Video sorunlarında OpenCV sürümü ile `GStreamer: YES/NO` bilgisini de belirtin. Sorun yalnızca SITL veya belirli bir donanımda oluşuyorsa bunu açıkça yazın.

## Lisans

Depo sahibi henüz bir açık kaynak lisansı seçmemiştir. Bu hazırlık sırasında kullanım veya dağıtım hakkı tanımlayan bir lisans eklenmemiştir.
