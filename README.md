# OSINTURK

Pasif Bilgi Toplama Konsolu — Subfinder, Httpx, Censys ve Nikto araçlarını tek
Türkçe arayüzde toplayan; macOS Apple Silicon (ARM64) uyumlu, asenkron ve donma
yapmayan liquid-glass masaüstü uygulaması.

Mete Şahan Tarafından Geliştirilmiştir. 2026

---

## Yasal Sorumluluk Reddi

OSINTURK yalnızca eğitim, kurumsal güvenlik değerlendirmesi ve yetkili sızma
testi amacıyla geliştirilmiş bir araçtır. Aracı kullanmadan önce aşağıdaki
koşulları kabul etmiş sayılırsınız:

- Bu aracı yalnızca sahibi olduğunuz ya da tarama için açık ve yazılı izniniz
  bulunan sistemler üzerinde kullanın.
- İzinsiz erişim, tarama veya bilgi toplama; başta Türkiye'de 5237 sayılı TCK'nın
  243 ve 244. maddeleri olmak üzere birçok ülkede suç teşkil eder ve cezai
  yaptırıma tabidir.
- Bu yazılımın kullanımından doğacak her türlü hukuki, cezai ve mali sorumluluk
  tamamen son kullanıcıya aittir.
- Geliştirici ve katkıda bulunanlar, aracın kötüye kullanımından veya
  kullanımından kaynaklanan doğrudan ya da dolaylı hiçbir zarardan sorumlu
  tutulamaz.
- Yazılım "olduğu gibi" (as-is), herhangi bir garanti verilmeksizin sunulur.

Uygulama, her tarama başlamadan önce kullanıcıdan yetki onayı ister.

---

## Kurulum ve Çalıştırma

Gereksinim: Python 3.10 veya üzeri (macOS / Linux / Windows). PyQt6 ve aiohttp,
Apple Silicon dahil tüm platformlarda hazır "wheel" paketleriyle gelir; derleme
veya harici bağımlılık hatası oluşmaz.

### 1. Depoyu klonla

```bash
git clone https://github.com/metesahan/OSINTURK
cd OSINTURK
```

### 2. Sanal ortam oluştur ve etkinleştir

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 4. Uygulamayı çalıştır

```bash
python main.py
```

Sonraki açılışlarda yalnızca sanal ortamı etkinleştirip çalıştırman yeterlidir:

```bash
source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
python main.py
```

### Opsiyonel: Gerçek CLI araçları

Subfinder ve Nikto'nun gerçek sürümleri sistemde kuruluysa uygulama bunları
otomatik olarak kullanır. Kurulu değilse saf Python yedeğiyle (crt.sh + aiohttp)
çalışmaya devam eder.

```bash
brew install subfinder nikto
```

---

## Nasıl Çalışır?

| Modül | Uygulama İçi Davranış |
|-------|------------------------|
| Subfinder | Sistemde gerçek `subfinder` binary'si varsa onu kullanır; yoksa saf Python ile Sertifika Şeffaflığı (`crt.sh`) üzerinden pasif subdomain keşfi yapar. |
| Httpx | `aiohttp` ile asenkron olarak ana hedefe ve bulunan tüm subdomain'lere geniş Türkçe/İngilizce wordlist uygular; HTTP durum kodlarını (200/301/403/404/500 vb.) tespit eder. |
| Kritik Bulgular | `.env`, `.git`, `wp-config`, `phpmyadmin`, admin panelleri gibi hassas yollar 200 OK dönerse ayrı bir bölümde öne çıkarılır. |
| Censys | API ID ve Secret girilirse Censys Search v2 API'sini sorgular (IP / açık servisler). |
| Nikto | Sistemde `nikto` kuruluysa çalıştırır ve çıktısını canlı akıtır; kurulu değilse bu adımı atlar. |

Tüm ağ işlemleri ayrı bir thread'deki asyncio döngüsünde yürütülür; arayüz
donmaz ve ilerleme sözel olarak canlı yayınlanır. "Durdur" ile tarama her an
iptal edilebilir.

---

## Özellikler

- Minimalist, tamamen nötr koyu (dark) liquid-glass arayüz
- Dinamik animasyonlu arka plan; ekran ve panel geçişlerinde sıralı fade animasyonları
- Sol navigasyon paneli: sonuç kategorileri arası geçiş, canlı istatistikler
- İsimle giriş ekranı ve interaktif çip butonlarla araç seçimi
- Canlı sözel ilerleme ve ilerleme çubuğu
- Sonuç bölümleri: Kritik Bulgular, Tüm Sonuçlar, Subdomainler, Censys, Nikto, Kaydedilenler
- Kopyalanabilir bulgular: her satıra sağ tık (Kopyala / Tümünü Kopyala) veya çift tıklama
- Subfinder ile bulunan tüm hostlarda wordlist denemesi (varsayılan host sınırı yok)
- Taramaları `~/OSINTURK_Kayitlar/` altına JSON olarak kaydetme ve geri yükleme
- Tek yüzeyde dikey kaydırılabilir içerik

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

---

## Notlar

- Censys yeni "Platform" API'sine geçtiyse kimlik veya uç nokta güncellemesi
  gerekebilir; uygulama bu hatayı çökmeden arayüzde bildirir.
- Subfinder çok sayıda subdomain bulursa, tümünde geniş wordlist denemesi hedefte
  ciddi trafik üretir; yalnızca yetkili hedeflerde kullanın. Sınır koymak
  isterseniz `engine.py` içindeki `ScanConfig.max_hosts` değerini yükseltebilirsiniz
  (0 = sınırsız).
- Her tarama öncesi uygulama yetki onayı ister.
