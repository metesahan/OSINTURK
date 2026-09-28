# -*- coding: utf-8 -*-
"""
OSINTURK - Wordlist Modülü
--------------------------
Dizin / endpoint keşfi için Türkçe + İngilizce kapsamlı kelime listesi.
Liste sonunda otomatik olarak tekilleştirilir (dict.fromkeys ile sıra korunur).

CRITICAL_KEYWORDS: 200 OK dönen ve bu anahtar kelimelerden birini içeren
yollar "Kritik Bulgular" sekmesinde öne çıkarılır.
"""

_RAW = [
    # ── İngilizce / Genel — Yönetim ──
    "admin", "administrator", "admins", "adm", "admincp", "adminarea",
    "admin_area", "admin-panel", "admin_panel", "adminpanel",
    "admincontrol", "adminlogin", "panel", "cpanel", "controlpanel",
    "control-panel", "webadmin", "sysadmin", "superadmin", "super-admin",
    "root", "master", "manager", "management", "manage", "backend",
    "backoffice", "dashboard", "dash", "console", "control", "portal", "intranet",

    # ── İngilizce — Kimlik / Giriş ──
    "login", "signin", "sign-in", "log-in", "logon", "signon",
    "auth", "authenticate", "authentication",
    "user", "users", "account", "accounts", "profile", "profiles",
    "register", "signup", "sign-up", "sign_up", "registration",
    "logout", "signout", "sign-out", "forgot-password", "reset-password",

    # ── İngilizce — Veritabanı ──
    "phpmyadmin", "phpMyAdmin", "pma", "mysql", "mysqladmin", "myadmin",
    "db", "database", "databases", "sql", "sqladmin", "dbadmin", "adminer",
    "postgres", "mongodb", "redis", "sqlite", "mssql", "oracle",

    # ── İngilizce — CMS ──
    "wp-admin", "wp-login", "wp-content", "wp-includes", "wordpress", "wp",
    "joomla", "drupal", "magento", "prestashop", "opencart", "shopify",
    "typo3", "modx", "bitrix", "bitrix/admin",

    # ── İngilizce — Konfig / Hassas Dosyalar ──
    "config", "configuration", "settings", "setup", "install", "installer",
    "upgrade", "update", "env", ".env", ".git", ".git/config", ".svn",
    ".htaccess", ".htpasswd", "web.config", "app.config",
    "composer.json", "package.json", ".DS_Store", ".well-known/security.txt",

    # ── İngilizce — API / Dokümantasyon ──
    "api", "apis", "api/v1", "api/v2", "api/v3", "rest", "graphql",
    "swagger", "swagger-ui", "swagger.json", "openapi.json",
    "api-docs", "apidocs", "docs", "documentation",

    # ── İngilizce — Test / Geliştirme ──
    "test", "tests", "testing", "dev", "development", "develop",
    "staging", "stage", "demo", "sample", "sandbox", "beta", "alpha",

    # ── İngilizce — Yedek / Geçici ──
    "backup", "backups", "bak", "old", "oldsite", "old-site",
    "archive", "archives", "temp", "tmp", "cache", "logs", "log",

    # ── İngilizce — Bilgi / Durum ──
    "info", "information", "about", "contact", "help", "support",
    "status", "server-status", "server-info", "health", "healthcheck",
    "version", "versions", "files", "file", "upload", "uploads", "download",
    "downloads", "media", "images", "img", "css", "js", "assets", "static",

    # ── İngilizce — E-ticaret ──
    "shop", "store", "cart", "checkout", "order", "orders", "payment",
    "payments", "invoice", "invoices", "billing", "product", "products",
    "category", "categories", "news", "blog", "forum", "community", "wiki",
    "faq", "search", "sitemap", "index", "home", "main", "default",

    # ── İngilizce — Güvenlik / Sistem ──
    "error", "errors", "private", "secret", "hidden", "internal",
    "confidential", "secure", "security", "ssl", "cert", "certificates",
    "remote", "shell", "cmd", "command", "exec", "system", "debug", "trace",
    "phpinfo", "robots", "humans", "cgi-bin", "scripts", "script",
    "xmlrpc", "wp-cron", "wp-config", "crossdomain", "clientaccesspolicy",
    "crossdomain.xml", "security.txt", "humans.txt", "robots.txt",
    "sitemap.xml", "phpinfo.php", "info.php", "test.php", "shell.php",
    "cmd.php", "upload.php", "download.php", "wp-config.php.bak",
    "wp-config.php.old",

    # ── TÜRKÇE — Yönetim / Panel ──
    "yonetim", "yonetici", "yonetim-paneli", "yonetim_paneli", "yonetimpanel",
    "yonetim-panel", "yonetimkontrol", "yonetim-kontrol",
    "kontrol", "kontrolpaneli", "kontrol-paneli", "kontrol_paneli",
    "kontrolpanel", "sistem", "sistem-yonetimi", "sistem-yonetim",
    "sistemayarlari", "sistem-ayarlari", "ayarlar", "ayar",
    "konfigurasyon", "yapilandirma",
    "yonetimci", "yonetimciler", "yonetim-girisi", "yonetim-giris",

    # ── TÜRKÇE — Kimlik / Giriş ──
    "giris", "giris-yap", "giris_yap", "girisyap",
    "giris-kayit", "giris-ekrani", "giris-ekran",
    "oturum-ac", "oturum-acma", "oturum", "oturumlar",
    "uyelik", "uyelikler", "uye", "uyeler",
    "uye-girisi", "uye-giris", "uye-ol", "uye-kayit", "uye-kaydi",
    "kayit", "kayit-ol", "kayit-formu", "kayitlar",
    "uyelik-islemleri",
    "hesap", "hesaplar", "hesabim", "hesap-ayarlari",
    "hesap-olustur", "profil", "profiller", "profilim",
    "sifre", "sifre-degistir",
    "sifremi-unuttum", "sifremiunuttum", "sifre-sifirla", "sifre-yenile",
    "parola", "parolam", "parola-degistir",
    "cikis", "cikis-yap", "oturum-kapat",

    # ── TÜRKÇE — İçerik / Bilgi ──
    "hakkimizda", "iletisim",
    "iletisim-formu", "iletisimformu", "bize-ulasin",
    "mesaj", "mesajlar", "mesaj-gonder", "mesajlarim",
    "bildirim", "bildirimler", "bildirimlerim", "duyuru", "duyurular",
    "haber", "haberler", "haber-detay", "makale", "makaleler",
    "yazi", "yazilar", "blog-yazilari", "etkinlik", "etkinlikler",
    "yardim", "destek", "destek-merkezi", "sikca-sorulan-sorular",
    "sss", "soru", "sorular", "yorum", "yorumlar",
    "arama", "arama-sonuclari", "site-haritasi", "site-harita",
    "harita", "konum", "adres", "sube", "subeler",

    # ── TÜRKÇE — E-ticaret ──
    "sepet", "sepetim", "sepete-ekle", "sepet-islemleri",
    "siparis", "siparisler", "siparis-ver",
    "siparis-takip", "siparis-takibi",
    "odeme", "odeme-yap", "odeme-islemleri",
    "odeme-sayfasi", "kredi-karti", "kredikarti",
    "fatura", "faturalar", "fatura-detay", "fatura-listesi",
    "urun", "urunler", "urun-detay",
    "kategori", "kategoriler", "kategori-listesi",
    "marka", "markalar", "stok", "stoklar", "kampanya", "kampanyalar",
    "indirim", "indirimler", "kupon", "kuponlar", "kargo", "kargo-takip",
    "iade", "iadeler", "iade-talebi", "magaza", "magazalar",
    "bayi", "bayiler", "bayi-girisi", "bayi-panel", "bayi-paneli",

    # ── TÜRKÇE — Kurumsal / Finans ──
    "kurumsal", "kurum", "sirket", "firma", "firmalar",
    "muhasebe", "finans", "finansal", "bordro", "bordrolar",
    "personel", "personeller", "calisan", "calisanlar",
    "ik", "insan-kaynaklari", "ise-alim",
    "basvuru", "basvurular", "basvuru-formu",
    "musteri", "musteriler", "musteri-hizmetleri",
    "crm", "erp", "stok-yonetimi", "depo", "depolar", "lojistik",
    "rapor", "raporlar", "raporlama", "istatistik", "istatistikler",
    "analiz", "analizler",

    # ── TÜRKÇE — Güvenlik / Sistem ──
    "guvenlik", "guvenlik-acigi", "guvenlik-duvari",
    "guvenlik-log", "guvenlik-loglari", "log-kayitlari", "loglar",
    "sistem-loglari", "erisim-loglari", "erisim-kayitlari",
    "ip-log", "ip-loglari", "oturum-loglari", "hata-loglari",
    "hata", "hatalar", "hata-sayfasi", "hata-kayitlari",
    "yedek", "yedekler", "yedekleme", "yedek-al", "sistem-yedegi",
    "veritabani", "veritabani-yonetimi",
    "sql-yonetim", "db-yonetim", "kullanici",
    "kullanicilar", "kullanici-yonetimi",
    "kullanici-listesi", "kullanici-ekle", "kullanici-sil",
    "yetki", "yetkiler", "yetkilendirme", "rol", "roller", "rol-yonetimi",
    "izinler", "izin-yonetimi", "modul", "moduller",
    "eklenti", "eklentiler", "tema", "temalar", "sablon", "sablonlar",

    # ── TÜRKÇE — İletişim / Sosyal ──
    "eposta", "e-posta", "mail", "mailler", "mail-gonder",
    "mail-admin", "admin-mail", "smtp", "smtp-ayarlari",
    "sms", "sms-gonder", "sms-ayarlari",
    "telefon", "telefonlar", "gsm", "whatsapp", "telegram",
    "sosyal-medya", "sosyalmedya", "paylas", "paylasim",
    "foto-galeri", "fotogaleri", "galeri", "galeriler", "video", "videolar",
    "resim", "resimler", "fotograf", "fotograflar",

    # ── TÜRKÇE — Diğer ──
    "anasayfa", "ana-sayfa", "ana_sayfa", "yonlendir",
    "yonlendirme", "kisa-yol", "kisayol",
    "taslak", "taslaklar", "onay", "onaylar", "onayla", "reddet",
    "beklemede", "bekleyen", "aktif", "pasif", "arsiv",
    "arsivlenen", "eski-surum",
    "beta-test", "beta-testi", "deneme",
    "gelistirme", "gelistirici",
    "servis", "servisler", "webservis", "webservisi",
    "wsdl", "soap", "xml-rpc", "rpc",
    "toplu-islem", "toplu-yukleme", "toplu-indirme",
    "ice-aktar", "disa-aktar", "export", "import",
    "csv", "excel", "pdf", "rapor-indir",
    "yazdir", "print", "goruntule",
]

# Sıra korunarak tekilleştir
WORDLIST = list(dict.fromkeys(w.strip() for w in _RAW if w and w.strip()))

# 200 OK döndüğünde "kritik" sayılacak hassas anahtar kelimeler
CRITICAL_KEYWORDS = [
    ".env", ".git", ".svn", ".htpasswd", ".htaccess", "web.config", "app.config",
    "wp-config", "phpinfo", "info.php", "adminer", "phpmyadmin", "pma", "myadmin",
    ".ds_store", "id_rsa", "backup", "yedek", "dump", "server-status", "server-info",
    "composer.json", "package.json", "config", "veritabani", "database", "sql",
    "admin", "yonetim", "panel", "cpanel", "shell", "cmd", "secret", ".well-known",
    "xmlrpc", "swagger", "actuator", "bak", "old",
]


def is_critical(path: str) -> bool:
    """Verilen yol (path) hassas bir anahtar kelime içeriyor mu?"""
    p = (path or "").lower().lstrip("/")
    return any(k in p for k in CRITICAL_KEYWORDS)
