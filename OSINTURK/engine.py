# -*- coding: utf-8 -*-
"""
OSINTURK - Tarama Motoru (Asenkron)
-----------------------------------
Tüm ağ işlemleri ayrı bir QThread içinde çalışan bir asyncio olay döngüsünde
yürütülür. Böylece arayüz (UI) yüksek hacimli taramalarda bile donmaz.
İlerleme, bulgular ve hatalar Qt sinyalleri ile ana thread'e iletilir.

Araç mantığı:
  • Subfinder : Sistemde `subfinder` binary'si varsa kullanılır; yoksa saf
                Python ile Sertifika Şeffaflığı (crt.sh) üzerinden PASİF
                subdomain keşfi yapılır.
  • Httpx     : `aiohttp` ile asenkron HTTP durum kodu tespiti + dizin/endpoint
                keşfi (fuzzing). Harici binary gerekmez.
  • Censys    : Censys Search v2 API (Basic Auth: API ID + Secret).
  • Nikto     : Sistemde `nikto` binary'si varsa çalıştırılır (opsiyonel).
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from PyQt6.QtCore import QThread, pyqtSignal

try:
    import aiohttp
except ImportError:  # aiohttp yoksa UI net bir hata gösterebilsin
    aiohttp = None

from wordlist import WORDLIST, is_critical


# --------------------------------------------------------------------------- #
#  Yapılandırma
# --------------------------------------------------------------------------- #
@dataclass
class ScanConfig:
    target: str
    use_subfinder: bool = True
    use_dirscan: bool = True
    use_censys: bool = False
    use_nikto: bool = False
    censys_id: str = ""
    censys_secret: str = ""
    concurrency: int = 40          # eşzamanlı istek sınırı
    timeout: float = 8.0           # istek başına zaman aşımı (sn)
    max_hosts: int = 0             # fuzzing host üst sınırı (0 = SINIRSIZ / tüm hostlar)
    user_agent: str = "OSINTURK/1.0 (+ethical-recon)"


# --------------------------------------------------------------------------- #
#  Yardımcı
# --------------------------------------------------------------------------- #
def _normalize(target: str) -> str:
    """https://a.b.com/yol -> a.b.com  (şema, yol ve portu temizler)."""
    t = (target or "").strip()
    if not t:
        return ""
    if "://" not in t:
        t = "http://" + t
    host = urlparse(t).hostname or ""
    return host.lower().strip(".")


def _status_label(status: int) -> str:
    if status == 200:
        return "200 · Erişilebilir"
    if status in (301, 302, 307, 308):
        return f"{status} · Yönlendirme"
    if status in (401, 403):
        return f"{status} · Yetkisiz/Yasak"
    if status == 500:
        return "500 · Sunucu Hatası"
    return str(status)


# --------------------------------------------------------------------------- #
#  Motor
# --------------------------------------------------------------------------- #
class ScanEngine(QThread):
    # UI'ya iletilen sinyaller
    progress = pyqtSignal(str)          # sözel durum satırı
    stage = pyqtSignal(str, int)        # aşama adı, yüzde (0-100)
    subdomain_found = pyqtSignal(str)
    result_found = pyqtSignal(dict)     # {url, path, status, label, critical}
    critical_found = pyqtSignal(dict)
    censys_result = pyqtSignal(dict)    # {ip, services}
    nikto_line = pyqtSignal(str)
    error = pyqtSignal(str)
    finished_scan = pyqtSignal(dict)    # özet

    def __init__(self, cfg: ScanConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self._cancel = False
        self.summary = {
            "target": cfg.target,
            "started": datetime.now().isoformat(timespec="seconds"),
            "subdomains": 0, "results": 0, "criticals": 0,
            "censys": 0, "nikto": False,
        }

    # Dışarıdan iptal
    def cancel(self):
        self._cancel = True

    # QThread giriş noktası -> yeni bir asyncio döngüsü kurar
    def run(self):
        if aiohttp is None:
            self.error.emit("`aiohttp` kütüphanesi bulunamadı. Lütfen 'pip install aiohttp' çalıştırın.")
            self.finished_scan.emit(self.summary)
            return
        try:
            asyncio.run(self._orchestrate())
        except Exception as exc:  # motor asla arayüzü çökertmemeli
            self.error.emit(f"Beklenmeyen hata: {exc}")
        finally:
            self.summary["finished"] = datetime.now().isoformat(timespec="seconds")
            self.finished_scan.emit(self.summary)

    # ---------------------------------------------------------------- #
    async def _orchestrate(self):
        domain = _normalize(self.cfg.target)
        if not domain:
            self.error.emit("Geçersiz hedef adresi.")
            return

        self.progress.emit(f"🎯 Hedef belirlendi: {domain}")
        self.progress.emit("Tarama motoru başlatılıyor, hazırlıklar yapılıyor…")

        timeout = aiohttp.ClientTimeout(total=self.cfg.timeout)
        connector = aiohttp.TCPConnector(ssl=False, limit=self.cfg.concurrency + 10)
        headers = {"User-Agent": self.cfg.user_agent}

        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector, headers=headers
        ) as session:

            hosts = [domain]

            # 1) SUBDOMAIN KEŞFİ ------------------------------------------------
            if self.cfg.use_subfinder and not self._cancel:
                self.stage.emit("Subdomain Keşfi", 5)
                self.progress.emit("🔎 Pasif kaynaklardan subdomain keşfi başlatılıyor…")
                subs = await self._discover_subdomains(session, domain)
                for s in sorted(subs):
                    self.subdomain_found.emit(s)
                self.summary["subdomains"] = len(subs)
                if subs:
                    self.progress.emit(f"✅ {len(subs)} adet subdomain bulundu.")
                    hosts = list(dict.fromkeys([domain] + sorted(subs)))
                else:
                    self.progress.emit("ℹ️ Ek subdomain bulunamadı, ana hedefle devam ediliyor.")

            # Varsayılan: bulunan TÜM hostlarda wordlist denenir (max_hosts=0).
            # İsteğe bağlı bir üst sınır verilmişse yalnızca o kadarı taranır.
            if self.cfg.max_hosts and len(hosts) > self.cfg.max_hosts:
                self.progress.emit(
                    f"⚙️ {len(hosts)} host bulundu; ilk {self.cfg.max_hosts} tanesi taranacak."
                )
                hosts = hosts[: self.cfg.max_hosts]
            else:
                self.progress.emit(
                    f"⚙️ Toplam {len(hosts)} host üzerinde wordlist taraması yapılacak."
                )

            # 2) DİZİN / ENDPOINT + DURUM KODU TARAMASI (Httpx) ----------------
            if self.cfg.use_dirscan and not self._cancel:
                await self._dir_scan(session, hosts)

            # 3) CENSYS --------------------------------------------------------
            if self.cfg.use_censys and not self._cancel:
                self.stage.emit("Censys Sorgusu", 90)
                self.progress.emit("🛰️ Censys üzerinden altyapı bilgileri sorgulanıyor…")
                await self._censys(session, domain)

            # 4) NIKTO ---------------------------------------------------------
            if self.cfg.use_nikto and not self._cancel:
                self.stage.emit("Nikto Taraması", 95)
                await self._nikto(hosts[0])

        if self._cancel:
            self.progress.emit("⛔ Tarama kullanıcı tarafından durduruldu.")
        else:
            self.stage.emit("Tamamlandı", 100)
            self.progress.emit("🏁 Tarama tamamlandı. Sonuçlar aşağıda listeleniyor.")

    # ---------------------------------------------------------------- #
    #  Subdomain keşfi
    # ---------------------------------------------------------------- #
    async def _discover_subdomains(self, session, domain) -> set:
        # Öncelik: sistemde gerçek subfinder binary'si
        if shutil.which("subfinder"):
            self.progress.emit("subfinder binary'si tespit edildi, kullanılıyor…")
            subs = await self._subfinder_binary(domain)
            if subs:
                return subs
            self.progress.emit("subfinder çıktısı boş; crt.sh'e geçiliyor…")

        # Yedek: crt.sh Sertifika Şeffaflığı (pasif)
        return await self._crtsh(session, domain)

    async def _subfinder_binary(self, domain) -> set:
        subs = set()
        try:
            proc = await asyncio.create_subprocess_exec(
                "subfinder", "-d", domain, "-silent",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            while True:
                if self._cancel:
                    proc.kill()
                    break
                line = await proc.stdout.readline()
                if not line:
                    break
                name = line.decode(errors="ignore").strip().lower()
                if name.endswith(domain):
                    subs.add(name)
            await proc.wait()
        except Exception as exc:
            self.progress.emit(f"subfinder çalıştırılamadı: {exc}")
        return subs

    async def _crtsh(self, session, domain) -> set:
        subs = set()
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=25)) as r:
                if r.status != 200:
                    self.progress.emit(f"crt.sh yanıt vermedi (HTTP {r.status}).")
                    return subs
                data = await r.json(content_type=None)
            for row in data or []:
                for name in (row.get("name_value") or "").split("\n"):
                    name = name.strip().lstrip("*.").lower()
                    if name and name.endswith(domain) and " " not in name:
                        subs.add(name)
        except asyncio.TimeoutError:
            self.progress.emit("crt.sh zaman aşımına uğradı.")
        except Exception as exc:
            self.progress.emit(f"crt.sh sorgusunda hata: {exc}")
        return subs

    # ---------------------------------------------------------------- #
    #  Dizin / endpoint taraması (Httpx eşdeğeri)
    # ---------------------------------------------------------------- #
    async def _dir_scan(self, session, hosts):
        sem = asyncio.Semaphore(self.cfg.concurrency)
        total = max(1, len(hosts) * (len(WORDLIST) + 1))
        done = 0

        for host in hosts:
            if self._cancel:
                break
            base = await self._detect_base(session, host)
            if not base:
                self.progress.emit(f"⚠️ {host} erişilemedi, atlanıyor.")
                done += len(WORDLIST) + 1
                continue

            self.progress.emit(f"📂 {host} üzerinde dizin/endpoint taraması yapılıyor…")

            # kök sayfa
            root = await self._fetch(session, sem, base, "")
            done += 1
            if root:
                self._handle_result(root)

            # wordlist
            tasks = [self._fetch(session, sem, base, w) for w in WORDLIST]
            for coro in asyncio.as_completed(tasks):
                if self._cancel:
                    break
                res = await coro
                done += 1
                if res:
                    self._handle_result(res)
                if done % 40 == 0:
                    pct = 5 + int(80 * done / total)   # 5-85 arası
                    self.stage.emit("Dizin Taraması", min(pct, 85))
                    self.progress.emit(
                        f"… {done}/{total} yol denendi · {self.summary['results']} bulgu"
                    )

    async def _detect_base(self, session, host) -> str | None:
        for scheme in ("https://", "http://"):
            try:
                async with session.get(scheme + host, allow_redirects=True) as r:
                    _ = r.status
                    return scheme + host
            except Exception:
                continue
        return None

    async def _fetch(self, session, sem, base, path) -> dict | None:
        if self._cancel:
            return None
        url = base.rstrip("/") + ("/" + path.lstrip("/") if path else "")
        async with sem:
            try:
                async with session.get(url, allow_redirects=False) as resp:
                    status = resp.status
            except Exception:
                return None
        return {"url": url, "path": path, "status": status}

    def _handle_result(self, res):
        status = res["status"]
        if status == 404:
            return  # 404'ler listelenmez (sadece özet için önemsiz)
        res["label"] = _status_label(status)
        res["critical"] = bool(res["path"]) and status == 200 and is_critical(res["path"])
        self.summary["results"] += 1
        self.result_found.emit(res)
        if res["critical"]:
            self.summary["criticals"] += 1
            self.critical_found.emit(res)
            self.progress.emit(f"🚨 KRİTİK: {res['url']} (200 OK)")

    # ---------------------------------------------------------------- #
    #  Censys Search v2
    # ---------------------------------------------------------------- #
    async def _censys(self, session, domain):
        cid = self.cfg.censys_id.strip()
        secret = self.cfg.censys_secret.strip()
        if not cid or not secret:
            self.progress.emit("ℹ️ Censys API ID/Secret girilmedi, atlanıyor.")
            return
        url = "https://search.censys.io/api/v2/hosts/search"
        params = {"q": domain, "per_page": 25}
        auth = aiohttp.BasicAuth(cid, secret)
        try:
            async with session.get(
                url, params=params, auth=auth,
                timeout=aiohttp.ClientTimeout(total=25),
            ) as r:
                if r.status == 401:
                    self.progress.emit("❌ Censys kimlik doğrulaması başarısız (401).")
                    return
                if r.status != 200:
                    self.progress.emit(f"❌ Censys sorgusu başarısız (HTTP {r.status}).")
                    return
                data = await r.json(content_type=None)
        except Exception as exc:
            self.progress.emit(f"Censys hatası: {exc}")
            return

        hits = (((data or {}).get("result") or {}).get("hits")) or []
        for h in hits:
            ip = h.get("ip", "?")
            services = [
                f"{s.get('port')}/{s.get('service_name', '?')}"
                for s in (h.get("services") or [])
            ]
            self.summary["censys"] += 1
            self.censys_result.emit({"ip": ip, "services": ", ".join(services) or "-"})
        self.progress.emit(f"🛰️ Censys: {len(hits)} kayıt bulundu.")

    # ---------------------------------------------------------------- #
    #  Nikto (opsiyonel, harici binary)
    # ---------------------------------------------------------------- #
    async def _nikto(self, host):
        if not shutil.which("nikto"):
            self.progress.emit(
                "ℹ️ Nikto sistemde kurulu değil. Kurulum: 'brew install nikto'. Bu adım atlandı."
            )
            return
        self.summary["nikto"] = True
        self.progress.emit(f"🧪 Nikto taraması başlatılıyor: {host} (biraz sürebilir)…")
        try:
            proc = await asyncio.create_subprocess_exec(
                "nikto", "-h", host, "-maxtime", "180s", "-ask", "no",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            while True:
                if self._cancel:
                    proc.kill()
                    break
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors="ignore").rstrip()
                if text:
                    self.nikto_line.emit(text)
            await proc.wait()
        except Exception as exc:
            self.progress.emit(f"Nikto çalıştırılamadı: {exc}")
