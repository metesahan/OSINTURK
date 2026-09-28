# ◇ OSINTURK

**Pasif Bilgi Toplama Konsolu** — Subfinder, Httpx, Censys ve Nikto araçlarını
tek Türkçe arayüzde toplayan, macOS Apple Silicon (ARM64) uyumlu masaüstü uygulaması.

> _Mete Şahan Tarafından Geliştirilmiştir. · 2026_

---

## ⚠️ Sorumluluk Reddi

OSINTURK yalnızca **yasal yetkiye sahip olduğunuz** sistemlerde güvenlik
değerlendirmesi ve pasif bilgi toplama için tasarlanmıştır. İzinsiz tarama çoğu
ülkede (Türkiye'de TCK 243–244 dâhil) suçtur. Geliştirici, aracın kötüye
kullanımından sorumlu değildir. Uygulama her taramadan önce yetki onayı ister.

---

## Kurulum (macOS ARM64 / Linux / Windows)

```bash
cd OSINTURK
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

`PyQt6` ve `aiohttp`, Apple Silicon dâhil tüm platformlar için hazır “wheel”
paketleriyle gelir — derleme/harici bağımlılık hatası oluşmaz.

---

## Nasıl Çalışır?

| Modül | Uygulama İçi Davranış |
|-------|------------------------|
| **Subfinder** | Sistemde gerçek `subfinder` binary'si varsa onu kullanır; yoksa **saf Python** ile Sertifika Şeffaflığı (`crt.sh`) üzerinden **pasif** subdomain keşfi yapar. |
| **Httpx** | `aiohttp` ile asenkron olarak her hedefe ve bulunan subdomain'lere geniş Türkçe/İngilizce wordlist uygular; HTTP durum kodlarını (200/301/403/404/500…) tespit eder. |
| **Kritik Bulgular** | `.env`, `.git`, `wp-config`, `phpmyadmin`, admin panelleri vb. hassas yollar **200 OK** dönerse ayrı bir sekmede öne çıkarılır. |
| **Censys** | API ID + Secret girilirse Censys Search v2 API'sini sorgular (IP / açık servisler). |
| **Nikto** | Sistemde `nikto` kurulu ise çalıştırır ve çıktısını canlı akıtır; kurulu değilse adımı atlar. |

Tüm ağ işlemleri **ayrı bir thread'deki asyncio döngüsünde** yürütülür; arayüz
donmaz ve ilerleme sözel olarak canlı yayınlanır. “Durdur” ile her an iptal
edilebilir.

### Opsiyonel gerçek CLI araçları
```bash
brew install subfinder nikto      # Homebrew (macOS)
# httpx işlevi zaten yerleşik (aiohttp) olarak gelir
```

---

## Özellikler
- Şık, minimalist **Liquid Glass** arayüz — **varsayılan Light**, tamamen nötr (mavisiz) **Dark** teması
- **Dinamik animasyonlu arka plan** (giriş ekranı ve ana ekran) + buton/panel geçişlerinde **yumuşak fade animasyonu**
- **Sol navigasyon paneli**: sonuç kategorileri arası geçiş, canlı istatistikler, tema düğmesi
- İsimle giriş ekranı, interaktif çip butonlarla araç seçimi
- Canlı sözel ilerleme + ilerleme çubuğu
- Sonuç bölümleri: Kritik Bulgular · Tüm Sonuçlar · Subdomainler · Censys · Nikto · Kaydedilenler
- **Kopyalanabilir bulgular**: her satıra sağ tık → *Kopyala / Tümünü Kopyala*, veya çift tıkla panoya al
- Subfinder ile bulunan **tüm hostlarda** wordlist denenir (host sınırı yok — `max_hosts=0`)
- Taramaları `~/OSINTURK_Kayitlar/` altına **JSON** olarak kaydetme / geri yükleme

---

## Dosya Yapısı
```
OSINTURK/
├── main.py            # PyQt6 arayüz + akış yönetimi
├── engine.py          # Asenkron tarama motoru (Qt sinyalleri)
├── wordlist.py        # Türkçe/İngilizce wordlist + kritik anahtar kelimeler
├── requirements.txt
└── README.md
```

## Notlar
- Censys yeni “Platform” API'sine geçtiyse kimlik/uç nokta güncellemesi gerekebilir;
  uygulama hatayı çökmeden arayüzde bildirir.
- Subfinder çok sayıda subdomain bulursa, tümünde geniş wordlist denemesi hedefte
  **ciddi trafik** üretir; yalnızca yetkili hedeflerde kullanın. Sınır koymak isterseniz
  `engine.py` içindeki `ScanConfig.max_hosts` değerini (0 = sınırsız) yükseltebilirsiniz.
- Her tarama öncesi uygulama **yetki onayı** ister (etik kullanım güvencesi).
