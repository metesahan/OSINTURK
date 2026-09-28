# -*- coding: utf-8 -*-
"""
OSINTURK - Pasif Bilgi Toplama Arayüzü
======================================
Mete Şahan Tarafından Geliştirilmiştir. · 2026

Çalıştırma:
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python main.py

Yalnızca yetkili olduğunuz sistemlerde kullanın.
"""

import json
import math
import os
import sys
from datetime import datetime

from PyQt6.QtCore import (
    Qt, QRectF, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QRadialGradient, QPen,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QStackedLayout, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QProgressBar, QMessageBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QMenu, QButtonGroup,
    QSizePolicy, QScrollArea,
)

from engine import ScanEngine, ScanConfig

APP_NAME = "OSINTURK"
AUTHOR_LINE = "Mete Şahan Tarafından Geliştirilmiştir. · 2026"
SAVE_DIR = os.path.expanduser("~/OSINTURK_Kayitlar")


# ═══════════════════════════════════════════════════════════════════════════ #
#  Dinamik (animasyonlu) arka plan — nötr tonlar, mavi yok
# ═══════════════════════════════════════════════════════════════════════════ #
class AnimatedBackground(QWidget):
    """Gümüş liquid-glass estetiği: yavaşça süzülen, yumuşak kenarlı cam
    levhalar (neumorfik highlight + gölge) ve diyagonal gümüş gradyan."""

    # normalize (x, y, w, h) — hap/stadyum biçimli levhalar
    _SLABS = [
        (0.03, 0.08, 0.40, 0.15),
        (0.52, 0.04, 0.52, 0.14),
        (0.60, 0.28, 0.48, 0.19),
        (-0.05, 0.40, 0.34, 0.17),
        (0.28, 0.60, 0.40, 0.16),
        (0.66, 0.66, 0.46, 0.20),
        (0.02, 0.80, 0.44, 0.16),
    ]

    def __init__(self, dark=False):
        super().__init__()
        self.dark = dark
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30 FPS

    def set_dark(self, dark: bool):
        self.dark = dark
        self.update()

    def _tick(self):
        self._t += 0.004  # yavaş, sakin sürüklenme
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # --- diyagonal gümüş zemin ---
        grad = QLinearGradient(0, 0, w, h)
        if self.dark:
            grad.setColorAt(0.0, QColor("#15161a"))
            grad.setColorAt(0.55, QColor("#0e0e11"))
            grad.setColorAt(1.0, QColor("#08080a"))
            fill = QColor(255, 255, 255, 10)
            hi = QColor(255, 255, 255, 26)
            sh = QColor(0, 0, 0, 110)
        else:
            grad.setColorAt(0.0, QColor("#d5d9df"))
            grad.setColorAt(0.5, QColor("#e4e7ec"))
            grad.setColorAt(1.0, QColor("#f1f3f6"))
            fill = QColor(255, 255, 255, 90)
            hi = QColor(255, 255, 255, 210)
            sh = QColor(150, 158, 172, 90)
        p.fillRect(self.rect(), grad)

        for i, (sx, sy, sw, sh_n) in enumerate(self._SLABS):
            dx = math.sin(self._t + i * 1.3) * 0.012
            dy = math.cos(self._t * 0.8 + i * 0.9) * 0.010
            x = (sx + dx) * w
            y = (sy + dy) * h
            rw, rh = sw * w, sh_n * h
            radius = rh / 2.0

            # gölge (sağ-alt)
            shadow = QRectF(x + 6, y + 8, rw, rh)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(sh)
            p.drawRoundedRect(shadow, radius, radius)

            # cam levha
            rect = QRectF(x, y, rw, rh)
            p.setBrush(fill)
            p.drawRoundedRect(rect, radius, radius)

            # highlight kenar (sol-üst)
            pen = QPen(hi)
            pen.setWidthF(1.6)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            hi_rect = QRectF(x + 1, y + 1, rw - 2, rh - 2)
            p.drawArc(hi_rect, 45 * 16, 180 * 16)  # üst-sol yay = ışık kenarı


# ═══════════════════════════════════════════════════════════════════════════ #
#  Yardımcılar
# ═══════════════════════════════════════════════════════════════════════════ #
def fade_in(widget: QWidget, duration: int = 420, delay: int = 0):
    """Bir widget'ı yavaşça (opaklık 0→1) LİNEER animasyonla açar.
    delay > 0 ise sıralı (staggered) giriş için gecikmeyle başlar."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    eff.setOpacity(0.0)

    def _run():
        anim = QPropertyAnimation(eff, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.Linear)  # lineer geçiş
        anim.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
        anim.start()
        widget._fade_anim = anim  # referansı canlı tut

    if delay > 0:
        QTimer.singleShot(delay, _run)
    else:
        _run()


def reveal_height(widget: QWidget, duration: int = 520):
    """Widget'ı yükseklik 0 → doğal yükseklik olacak şekilde açar
    (aşağıdan yukarı 'gelme' hissi). Gölge efektini bozmaz."""
    hint = widget.sizeHint().height()
    target = hint if hint > 40 else max(widget.height(), 320)
    widget.setMaximumHeight(0)
    anim = QPropertyAnimation(widget, b"maximumHeight", widget)
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(target)
    anim.setEasingCurve(QEasingCurve.Type.Linear)
    anim.finished.connect(lambda: widget.setMaximumHeight(16777215))
    anim.start()
    widget._reveal_anim = anim


def stagger_in(widgets, base: int = 380, step: int = 90):
    """Bir widget listesini birbiri ardına (sıralı) fade ile açar."""
    for i, w in enumerate(widgets):
        fade_in(w, base, delay=i * step)


def glass_card(shadow=True) -> QFrame:
    f = QFrame()
    f.setObjectName("Glass")
    if shadow:
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(44)
        sh.setXOffset(0)
        sh.setYOffset(12)
        sh.setColor(QColor(0, 0, 0, 55))
        f.setGraphicsEffect(sh)
    return f


# ═══════════════════════════════════════════════════════════════════════════ #
#  Temalar — Light (varsayılan) & tamamen nötr Dark (mavisiz)
# ═══════════════════════════════════════════════════════════════════════════ #
def build_qss(dark: bool) -> str:
    if dark:
        c = dict(
            text="#ededee", sub="#9a9a9f",
            glass="rgba(255,255,255,0.06)", glass_border="rgba(255,255,255,0.12)",
            field="rgba(255,255,255,0.07)", field_border="rgba(255,255,255,0.14)",
            accent="#dcdce0", accent_hover="#ececf0", accent_press="#c7c7cc",
            accent_text="#161618",
            chip="rgba(255,255,255,0.06)", chip_on="rgba(255,255,255,0.16)",
            chip_on_border="rgba(255,255,255,0.46)",
            header="rgba(255,255,255,0.04)",
            nav_hover="rgba(255,255,255,0.07)", nav_on="rgba(255,255,255,0.13)",
            dialog_bg="#1a1b1f", dialog_border="rgba(255,255,255,0.14)",
            crit="#d08585", ok="#7cbf95", warn="#cbb06a",
        )
    else:
        c = dict(
            text="#1b1d22", sub="#5f6570",
            glass="rgba(255,255,255,0.55)", glass_border="rgba(255,255,255,0.75)",
            field="rgba(255,255,255,0.78)", field_border="rgba(120,130,145,0.30)",
            accent="#2b2d33", accent_hover="#3a3c44", accent_press="#202127",
            accent_text="#ffffff",
            chip="rgba(255,255,255,0.42)", chip_on="rgba(255,255,255,0.85)",
            chip_on_border="rgba(120,130,145,0.55)",
            header="rgba(255,255,255,0.30)",
            nav_hover="rgba(255,255,255,0.45)", nav_on="rgba(255,255,255,0.72)",
            dialog_bg="#eef1f5", dialog_border="rgba(120,130,145,0.35)",
            crit="#b04a4a", ok="#3f8a5f", warn="#a9822f",
        )

    return f"""
    QWidget {{
        color: {c['text']};
        font-family: -apple-system, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', sans-serif;
        font-size: 14px;
    }}
    #Root, #Content, #ResultArea, QStackedWidget#Content > QWidget {{ background: transparent; }}
    QScrollArea#Scroll {{ background: transparent; border: none; }}
    QScrollArea#Scroll > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 4px 2px 4px 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['field_border']}; border-radius: 5px; min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {c['sub']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    /* ── Liquid glass paneller ── */
    #Glass {{
        background-color: {c['glass']};
        border: 1px solid {c['glass_border']};
        border-radius: 26px;
    }}
    #Sidebar {{
        background-color: {c['glass']};
        border: 1px solid {c['glass_border']};
        border-radius: 28px;
    }}
    #Title {{ font-size: 26px; font-weight: 700; letter-spacing: 1px; }}
    #Sub {{ color: {c['sub']}; font-size: 13px; }}
    #Author {{ color: {c['sub']}; font-size: 12px; }}
    #NavHead {{ color: {c['sub']}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}
    #Toast {{ color: {c['sub']}; font-size: 12px; }}

    QLineEdit#Field {{
        background-color: {c['field']};
        border: 1px solid {c['field_border']};
        border-radius: 22px; padding: 12px 18px;
        selection-background-color: {c['accent']};
    }}
    QLineEdit#Field:focus {{ border: 1px solid {c['accent']}; }}

    /* ── Köşesiz şeffaf liquid-glass butonlar ── */
    QPushButton#Primary {{
        background-color: {c['chip']}; color: {c['text']};
        border: 1px solid {c['glass_border']}; border-radius: 24px;
        padding: 12px 28px; font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background-color: {c['chip_on']}; border: 1px solid {c['accent']};
    }}
    QPushButton#Primary:pressed {{ background-color: {c['chip_on']}; }}
    QPushButton#Primary:disabled {{ color: {c['sub']}; }}

    QPushButton#Ghost {{
        background-color: {c['chip']}; border: 1px solid {c['glass_border']};
        border-radius: 24px; padding: 11px 20px; color: {c['text']};
    }}
    QPushButton#Ghost:hover {{ border: 1px solid {c['accent']}; }}
    QPushButton#Ghost:disabled {{ color: {c['sub']}; }}

    QPushButton#Chip {{
        background-color: {c['chip']}; border: 1px solid {c['glass_border']};
        border-radius: 22px; padding: 9px 18px; color: {c['sub']}; font-weight: 600;
    }}
    QPushButton#Chip:hover {{ color: {c['text']}; }}
    QPushButton#Chip:checked {{
        background-color: {c['chip_on']}; border: 1px solid {c['chip_on_border']};
        color: {c['text']};
    }}

    QPushButton#Nav {{
        background-color: transparent; border: none; border-radius: 20px;
        padding: 11px 16px; text-align: left; color: {c['sub']}; font-weight: 500;
    }}
    QPushButton#Nav:hover {{ background-color: {c['nav_hover']}; color: {c['text']}; }}
    QPushButton#Nav:checked {{ background-color: {c['nav_on']}; color: {c['text']}; font-weight: 600; }}

    QTableWidget {{
        background-color: transparent; border: none; gridline-color: {c['glass_border']};
    }}
    QTableWidget::item {{ padding: 6px; }}
    QTableWidget::item:selected {{ background: {c['chip_on']}; color: {c['text']}; }}
    QHeaderView::section {{
        background-color: {c['header']}; color: {c['sub']};
        border: none; padding: 8px; font-weight: 600;
    }}

    QTextEdit#Log {{
        background-color: {c['field']}; border: 1px solid {c['glass_border']};
        border-radius: 16px; padding: 8px;
        font-family: 'SF Mono', Menlo, Consolas, monospace; font-size: 12px;
    }}
    QListWidget {{
        background-color: {c['field']}; border: 1px solid {c['glass_border']};
        border-radius: 16px; padding: 4px;
    }}
    QListWidget::item {{ padding: 8px; border-radius: 10px; }}
    QListWidget::item:selected {{ background: {c['chip_on']}; color: {c['text']}; }}

    QProgressBar {{
        border: 1px solid {c['glass_border']}; border-radius: 8px;
        background-color: {c['field']}; height: 10px; text-align: center;
    }}
    QProgressBar::chunk {{ background-color: {c['accent']}; border-radius: 7px; }}

    QMenu {{
        background-color: {c['dialog_bg']}; border: 1px solid {c['dialog_border']};
        border-radius: 12px; padding: 4px;
    }}
    QMenu::item {{ padding: 7px 18px; border-radius: 8px; color: {c['text']}; }}
    QMenu::item:selected {{ background-color: {c['chip_on']}; }}

    /* ── Onay/uyarı kutuları: temaya tam uyum ── */
    QMessageBox, QDialog {{ background-color: {c['dialog_bg']}; }}
    QMessageBox QLabel, QDialog QLabel {{ color: {c['text']}; background: transparent; }}
    QMessageBox QPushButton, QDialog QPushButton {{
        background-color: {c['accent']}; color: {c['accent_text']};
        border: none; border-radius: 20px; padding: 9px 22px; font-weight: 600;
        min-width: 80px;
    }}
    QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
        background-color: {c['accent_hover']};
    }}
    QMessageBox QPushButton:pressed, QDialog QPushButton:pressed {{
        background-color: {c['accent_press']};
    }}
    """


# ═══════════════════════════════════════════════════════════════════════════ #
#  Kopyalama davranışı (sağ tık menüsü + çift tık)
# ═══════════════════════════════════════════════════════════════════════════ #
def _selection_text(widget) -> str:
    if isinstance(widget, QTableWidget):
        rows = sorted({i.row() for i in widget.selectedItems()})
        lines = []
        for r in rows:
            cells = [
                widget.item(r, cidx).text() if widget.item(r, cidx) else ""
                for cidx in range(widget.columnCount())
            ]
            lines.append("  ".join(cells).strip())
        return "\n".join(lines)
    if isinstance(widget, QListWidget):
        return "\n".join(i.text() for i in widget.selectedItems())
    return ""


class CopyMixin:
    """Bir tablo/listeye kopyalama menüsü + çift tık kopyalama ekler."""

    def _attach_copy(self, widget, on_copied):
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(
            lambda pos, w=widget: self._copy_menu(w, pos, on_copied)
        )

    def _copy_menu(self, widget, pos, on_copied):
        menu = QMenu(widget)
        act_row = menu.addAction("Kopyala")
        act_all = menu.addAction("Tümünü Kopyala")
        chosen = menu.exec(widget.mapToGlobal(pos))
        if chosen == act_row:
            self._do_copy(_selection_text(widget), on_copied)
        elif chosen == act_all:
            widget.selectAll()
            self._do_copy(_selection_text(widget), on_copied)

    def _do_copy(self, text, on_copied):
        if text:
            QApplication.clipboard().setText(text)
            on_copied(text)


# ═══════════════════════════════════════════════════════════════════════════ #
#  Giriş ekranı
# ═══════════════════════════════════════════════════════════════════════════ #
class LoginView(QWidget):
    logged_in = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.addStretch()

        card = glass_card()
        card.setFixedWidth(460)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(44, 48, 44, 36)
        cl.setSpacing(14)

        logo = QLabel("◇ OSINTURK")
        logo.setObjectName("Title")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Pasif Bilgi Toplama Konsolu")
        sub.setObjectName("Sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name = QLineEdit()
        self.name.setObjectName("Field")
        self.name.setPlaceholderText("Adınızı girin…")
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name.returnPressed.connect(self._enter)

        btn = QPushButton("Giriş Yap")
        btn.setObjectName("Primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._enter)

        author = QLabel(AUTHOR_LINE)
        author.setObjectName("Author")
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cl.addWidget(logo)
        cl.addWidget(sub)
        cl.addSpacing(16)
        cl.addWidget(self.name)
        cl.addWidget(btn)
        cl.addSpacing(12)
        cl.addWidget(author)

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(card)
        wrap.addStretch()
        outer.addLayout(wrap)
        outer.addStretch()

        self._card = card
        self._seq = [logo, sub, self.name, btn, author]

    def play_entrance(self):
        """Kartı aşağıdan yukarı açar, içindeki öğeleri sıralı belirtir."""
        reveal_height(self._card, 560)
        stagger_in(self._seq, base=440, step=110)

    def showEvent(self, e):
        super().showEvent(e)
        self.play_entrance()

    def _enter(self):
        self.logged_in.emit(self.name.text().strip() or "Analist")


# ═══════════════════════════════════════════════════════════════════════════ #
#  Ana uygulama ekranı (sol panel + içerik)
# ═══════════════════════════════════════════════════════════════════════════ #
NAV_ITEMS = [
    ("🚨", "Kritik Bulgular"),
    ("◪", "Tüm Sonuçlar"),
    ("⋔", "Subdomainler"),
    ("🛰", "Censys"),
    ("🧪", "Nikto"),
    ("💾", "Kaydedilenler"),
]


class MainView(QWidget, CopyMixin):

    def __init__(self):
        super().__init__()
        self.engine: ScanEngine | None = None
        self.user = "Analist"
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(lambda: self.toast.setText(""))
        self._reset_current()
        os.makedirs(SAVE_DIR, exist_ok=True)
        self._build()

    def _reset_current(self):
        self.current = {
            "target": "", "user": self.user, "timestamp": "",
            "subdomains": [], "results": [], "criticals": [],
            "censys": [], "nikto": [],
        }

    # ---------------------------------------------------------------- UI
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(16)
        root.addWidget(self._sidebar())

        # İçerik tek bir dikey kaydırılabilir yüzey — ayrı pencereler yok
        scroll = QScrollArea()
        scroll.setObjectName("Scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._content())
        root.addWidget(scroll, 1)

    # ---- SOL PANEL
    def _sidebar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("Sidebar")
        bar.setFixedWidth(236)
        v = QVBoxLayout(bar)
        v.setContentsMargins(18, 22, 18, 20)
        v.setSpacing(6)

        logo = QLabel("◇ OSINTURK")
        logo.setObjectName("Title")
        logo.setStyleSheet("font-size:20px;")
        self.hello = QLabel("")
        self.hello.setObjectName("Sub")
        v.addWidget(logo)
        v.addWidget(self.hello)
        v.addSpacing(18)

        head = QLabel("SONUÇLAR")
        head.setObjectName("NavHead")
        v.addWidget(head)
        v.addSpacing(4)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        for idx, (icon, label) in enumerate(NAV_ITEMS):
            b = QPushButton(f"  {icon}   {label}")
            b.setObjectName("Nav")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=idx: self._show_page(i))
            self.nav_group.addButton(b, idx)
            self.nav_buttons.append(b)
            v.addWidget(b)
        self.nav_group.button(0).setChecked(True)

        v.addStretch()

        # canlı istatistikler
        self.stat_lbl = QLabel("—")
        self.stat_lbl.setObjectName("Sub")
        self.stat_lbl.setWordWrap(True)
        v.addWidget(self.stat_lbl)
        v.addSpacing(10)

        self.btn_shutdown = QPushButton("⏻   Sistemi Kapat")
        self.btn_shutdown.setObjectName("Ghost")
        self.btn_shutdown.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_shutdown.clicked.connect(self._shutdown)
        v.addWidget(self.btn_shutdown)

        author = QLabel(AUTHOR_LINE)
        author.setObjectName("Author")
        author.setWordWrap(True)
        v.addWidget(author)
        return bar

    # ---- İÇERİK
    def _content(self) -> QWidget:
        wrap = QWidget()
        col = QVBoxLayout(wrap)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(16)

        # arama kartı
        sc_card = glass_card()
        sc = QVBoxLayout(sc_card)
        sc.setContentsMargins(22, 20, 22, 20)
        sc.setSpacing(14)

        row = QHBoxLayout()
        self.target = QLineEdit()
        self.target.setObjectName("Field")
        self.target.setPlaceholderText("Hedef adres  ·  örn: example.com")
        self.target.returnPressed.connect(self._start)
        self.btn_start = QPushButton("Taramayı Başlat")
        self.btn_start.setObjectName("Primary")
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.clicked.connect(self._start)
        self.btn_stop = QPushButton("Durdur")
        self.btn_stop.setObjectName("Ghost")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_save = QPushButton("Kaydet")
        self.btn_save.setObjectName("Ghost")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save_current)
        row.addWidget(self.target, 1)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_save)
        sc.addLayout(row)

        chips = QHBoxLayout()
        chips.setSpacing(10)
        lbl = QLabel("Araçlar:")
        lbl.setObjectName("Sub")
        chips.addWidget(lbl)
        self.chip_sub = self._chip("Subfinder", True)
        self.chip_dir = self._chip("Httpx Dizin Taraması", True)
        self.chip_cen = self._chip("Censys", False)
        self.chip_nik = self._chip("Nikto", False)
        self.chip_cen.toggled.connect(lambda on: self.censys_wrap.setVisible(on))
        for ch in (self.chip_sub, self.chip_dir, self.chip_cen, self.chip_nik):
            chips.addWidget(ch)
        chips.addStretch()
        sc.addLayout(chips)

        self.cen_id = QLineEdit()
        self.cen_id.setObjectName("Field")
        self.cen_id.setPlaceholderText("Censys API ID")
        self.cen_secret = QLineEdit()
        self.cen_secret.setObjectName("Field")
        self.cen_secret.setPlaceholderText("Censys API Secret")
        self.cen_secret.setEchoMode(QLineEdit.EchoMode.Password)
        cen_row = QHBoxLayout()
        cen_row.addWidget(self.cen_id)
        cen_row.addWidget(self.cen_secret)
        self.censys_wrap = QWidget()
        self.censys_wrap.setLayout(cen_row)
        self.censys_wrap.setVisible(False)
        sc.addWidget(self.censys_wrap)
        col.addWidget(sc_card)

        # ilerleme kartı
        pg_card = glass_card()
        pg = QVBoxLayout(pg_card)
        pg.setContentsMargins(22, 16, 22, 16)
        pg.setSpacing(8)
        head = QHBoxLayout()
        self.stage_lbl = QLabel("Hazır")
        self.stage_lbl.setObjectName("Sub")
        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("Sub")
        head.addWidget(self.stage_lbl)
        head.addStretch()
        head.addWidget(self.count_lbl)
        pg.addLayout(head)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        pg.addWidget(self.bar)
        self.log = QTextEdit()
        self.log.setObjectName("Log")
        self.log.setReadOnly(True)
        self.log.setFixedHeight(108)
        pg.addWidget(self.log)
        col.addWidget(pg_card)

        # sonuç alanı — çerçevesiz/şeffaf, sayfaya gömülü (ayrı pencere değil)
        res_card = QWidget()
        res_card.setObjectName("ResultArea")
        rc = QVBoxLayout(res_card)
        rc.setContentsMargins(4, 6, 4, 6)
        rc.setSpacing(8)

        self.result_stack = QStackedWidget()
        self.tbl_crit = self._table(["URL", "Durum"])
        self.tbl_all = self._table(["URL", "Yol", "Durum"])
        self.list_sub = QListWidget()
        self.list_sub.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tbl_cen = self._table(["IP", "Servisler"])
        self.txt_nik = QTextEdit()
        self.txt_nik.setObjectName("Log")
        self.txt_nik.setReadOnly(True)

        # kopyalama davranışları
        for t in (self.tbl_crit, self.tbl_all, self.tbl_cen):
            self._attach_copy(t, self._flash_copy)
            t.cellDoubleClicked.connect(
                lambda r, c, w=t: self._do_copy(_selection_text(w), self._flash_copy)
            )
        self._attach_copy(self.list_sub, self._flash_copy)
        self.list_sub.itemDoubleClicked.connect(
            lambda it: self._do_copy(it.text(), self._flash_copy)
        )

        self.result_stack.addWidget(self.tbl_crit)
        self.result_stack.addWidget(self.tbl_all)
        self.result_stack.addWidget(self.list_sub)
        self.result_stack.addWidget(self.tbl_cen)
        self.result_stack.addWidget(self.txt_nik)
        self.result_stack.addWidget(self._saved_page())
        self.result_stack.setMinimumHeight(380)
        rc.addWidget(self.result_stack, 1)

        self.toast = QLabel("")
        self.toast.setObjectName("Toast")
        rc.addWidget(self.toast)
        col.addWidget(res_card, 1)

        # Giriş animasyonu için kart referansları
        self._content_cards = [sc_card, pg_card, res_card]

        self._refresh_saved()
        return wrap

    def play_enter_animation(self):
        """Ana ekrana geçişte kartları ve navigasyonu sıralı (dinamik) açar."""
        stagger_in(self._content_cards, base=420, step=110)
        stagger_in(self.nav_buttons, base=300, step=55)

    def _chip(self, text, checked):
        b = QPushButton(text)
        b.setObjectName("Chip")
        b.setCheckable(True)
        b.setChecked(checked)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        # Metnin (seçili/normal her durumda) tam sığması için içeriğe göre
        # sabit genişlik ver — kalınlaşınca kırpılmayı önler.
        b.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        b.setMinimumWidth(b.sizeHint().width() + 18)
        return b

    def _table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        t.horizontalHeader().setStretchLastSection(True)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        return t

    def _saved_page(self):
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        btn_ref = QPushButton("Yenile")
        btn_ref.setObjectName("Ghost")
        btn_ref.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ref.clicked.connect(self._refresh_saved)
        hint = QLabel("Kaydetmek için üstteki “Kaydet” · açmak için çift tıklayın.")
        hint.setObjectName("Sub")
        bar.addWidget(btn_ref)
        bar.addStretch()
        bar.addWidget(hint)
        l.addLayout(bar)
        self.list_saved = QListWidget()
        self.list_saved.itemDoubleClicked.connect(self._load_saved)
        l.addWidget(self.list_saved)
        return c

    # ---------------------------------------------------------------- akış
    def set_user(self, name):
        self.user = name
        self.current["user"] = name
        self.hello.setText(f"Hoş geldin, {name}")

    def _show_page(self, idx):
        """Sol panel navigasyonu — seçilen sayfayı animasyonlu açar."""
        self.result_stack.setCurrentIndex(idx)
        fade_in(self.result_stack.currentWidget(), 360)

    def _flash_copy(self, text):
        preview = text.splitlines()[0] if text else ""
        if len(preview) > 46:
            preview = preview[:46] + "…"
        self.toast.setText(f"✓ Panoya kopyalandı:  {preview}")
        self._toast_timer.start(2200)

    def _log(self, text):
        self.log.append(f"[{datetime.now():%H:%M:%S}]  {text}")
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_stats(self):
        self.stat_lbl.setText(
            f"Bulgu: {len(self.current['results'])}\n"
            f"Kritik: {len(self.current['criticals'])}\n"
            f"Subdomain: {len(self.current['subdomains'])}"
        )

    def _start(self):
        target = self.target.text().strip()
        if not target:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen bir hedef adres girin.")
            return
        if not any([self.chip_sub.isChecked(), self.chip_dir.isChecked(),
                    self.chip_cen.isChecked(), self.chip_nik.isChecked()]):
            QMessageBox.warning(self, "Araç Seçilmedi", "En az bir araç seçin.")
            return

        ok = QMessageBox.question(
            self, "Yetki Onayı",
            f"'{target}' hedefini taramak için yasal yetkiye sahip olduğunuzu "
            "onaylıyor musunuz?\n\nİzinsiz tarama suç teşkil edebilir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ok != QMessageBox.StandardButton.Yes:
            self._log("⛔ Tarama iptal edildi (yetki onaylanmadı).")
            return

        for t in (self.tbl_crit, self.tbl_all, self.tbl_cen):
            t.setRowCount(0)
        self.list_sub.clear()
        self.txt_nik.clear()
        self.log.clear()
        self.bar.setValue(0)
        self._reset_current()
        self.current["target"] = target
        self.current["user"] = self.user
        self.current["timestamp"] = datetime.now().isoformat(timespec="seconds")
        self._update_stats()

        cfg = ScanConfig(
            target=target,
            use_subfinder=self.chip_sub.isChecked(),
            use_dirscan=self.chip_dir.isChecked(),
            use_censys=self.chip_cen.isChecked(),
            use_nikto=self.chip_nik.isChecked(),
            censys_id=self.cen_id.text(),
            censys_secret=self.cen_secret.text(),
        )
        self.engine = ScanEngine(cfg)
        self.engine.progress.connect(self._log)
        self.engine.stage.connect(self._on_stage)
        self.engine.subdomain_found.connect(self._on_sub)
        self.engine.result_found.connect(self._on_result)
        self.engine.critical_found.connect(self._on_critical)
        self.engine.censys_result.connect(self._on_censys)
        self.engine.nikto_line.connect(self._on_nikto)
        self.engine.error.connect(lambda m: self._log(f"❌ {m}"))
        self.engine.finished_scan.connect(self._on_finished)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.nav_group.button(1).setChecked(True)
        self._show_page(1)  # Tüm Sonuçlar sekmesine geç (animasyonlu)
        self.engine.start()

    def _stop(self):
        if self.engine and self.engine.isRunning():
            self.engine.cancel()
            self._log("⛔ Durdurma isteği gönderildi…")

    def _shutdown(self):
        ok = QMessageBox.question(
            self, "Sistemi Kapat",
            "Uygulamayı kapatmak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ok != QMessageBox.StandardButton.Yes:
            return
        # Çalışan taramayı önce güvenle durdur
        if self.engine and self.engine.isRunning():
            self.engine.cancel()
            self.engine.wait(1500)
        QApplication.instance().quit()

    # ---- motor slotları
    def _on_stage(self, name, pct):
        self.stage_lbl.setText(name)
        self.bar.setValue(pct)

    def _on_sub(self, sub):
        self.list_sub.addItem(QListWidgetItem(sub))
        self.current["subdomains"].append(sub)
        self._update_stats()

    def _on_result(self, res):
        self.current["results"].append(res)
        r = self.tbl_all.rowCount()
        self.tbl_all.insertRow(r)
        self.tbl_all.setItem(r, 0, QTableWidgetItem(res["url"]))
        self.tbl_all.setItem(r, 1, QTableWidgetItem(res["path"] or "/"))
        item = QTableWidgetItem(res["label"])
        if res["status"] == 200:
            item.setForeground(QColor("#4f9e77"))
        elif res["status"] in (401, 403):
            item.setForeground(QColor("#b0902f"))
        self.tbl_all.setItem(r, 2, item)
        self.count_lbl.setText(
            f"{len(self.current['results'])} bulgu · {len(self.current['criticals'])} kritik"
        )
        self._update_stats()

    def _on_critical(self, res):
        self.current["criticals"].append(res)
        r = self.tbl_crit.rowCount()
        self.tbl_crit.insertRow(r)
        u = QTableWidgetItem(res["url"])
        u.setForeground(QColor("#c05a5a"))
        self.tbl_crit.setItem(r, 0, u)
        self.tbl_crit.setItem(r, 1, QTableWidgetItem(res["label"]))
        self._update_stats()

    def _on_censys(self, row):
        self.current["censys"].append(row)
        r = self.tbl_cen.rowCount()
        self.tbl_cen.insertRow(r)
        self.tbl_cen.setItem(r, 0, QTableWidgetItem(row["ip"]))
        self.tbl_cen.setItem(r, 1, QTableWidgetItem(row["services"]))

    def _on_nikto(self, line):
        self.current["nikto"].append(line)
        self.txt_nik.append(line)

    def _on_finished(self, summary):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(True)
        self.stage_lbl.setText("Tamamlandı")
        crit = len(self.current["criticals"])
        self._log(
            f"📊 Özet — {len(self.current['results'])} bulgu, {crit} kritik, "
            f"{len(self.current['subdomains'])} subdomain."
        )
        if crit:
            self.nav_group.button(0).setChecked(True)
            self._show_page(0)

    # ---- kayıt
    def _save_current(self):
        if not self.current["target"]:
            return
        safe = self.current["target"].replace("/", "_").replace(":", "_")
        path = os.path.join(SAVE_DIR, f"{safe}_{datetime.now():%Y%m%d_%H%M%S}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.current, f, ensure_ascii=False, indent=2)
            self._log(f"💾 Kaydedildi: {path}")
            self._refresh_saved()
            QMessageBox.information(self, "Kaydedildi", f"Tarama kaydedildi:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Hata", f"Kaydedilemedi: {exc}")

    def _refresh_saved(self):
        self.list_saved.clear()
        try:
            files = sorted((f for f in os.listdir(SAVE_DIR) if f.endswith(".json")), reverse=True)
        except FileNotFoundError:
            files = []
        for f in files:
            self.list_saved.addItem(QListWidgetItem(f))

    def _load_saved(self, item):
        path = os.path.join(SAVE_DIR, item.text())
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            QMessageBox.critical(self, "Hata", f"Açılamadı: {exc}")
            return

        for t in (self.tbl_crit, self.tbl_all, self.tbl_cen):
            t.setRowCount(0)
        self.list_sub.clear()
        self.txt_nik.clear()
        self.current = data

        for s in data.get("subdomains", []):
            self.list_sub.addItem(QListWidgetItem(s))
        for res in data.get("results", []):
            r = self.tbl_all.rowCount()
            self.tbl_all.insertRow(r)
            self.tbl_all.setItem(r, 0, QTableWidgetItem(res.get("url", "")))
            self.tbl_all.setItem(r, 1, QTableWidgetItem(res.get("path") or "/"))
            self.tbl_all.setItem(r, 2, QTableWidgetItem(res.get("label", "")))
        for res in data.get("criticals", []):
            r = self.tbl_crit.rowCount()
            self.tbl_crit.insertRow(r)
            self.tbl_crit.setItem(r, 0, QTableWidgetItem(res.get("url", "")))
            self.tbl_crit.setItem(r, 1, QTableWidgetItem(res.get("label", "")))
        for row in data.get("censys", []):
            r = self.tbl_cen.rowCount()
            self.tbl_cen.insertRow(r)
            self.tbl_cen.setItem(r, 0, QTableWidgetItem(row.get("ip", "")))
            self.tbl_cen.setItem(r, 1, QTableWidgetItem(row.get("services", "")))
        self.txt_nik.setPlainText("\n".join(data.get("nikto", [])))
        self._update_stats()
        self._log(f"📂 Kayıt yüklendi: {item.text()}")
        self.nav_group.button(1).setChecked(True)
        self._show_page(1)


# ═══════════════════════════════════════════════════════════════════════════ #
#  Kök widget — animasyonlu arka plan + içerik üst üste
# ═══════════════════════════════════════════════════════════════════════════ #
class RootWidget(QWidget):
    def __init__(self, background, content):
        super().__init__()
        self.setObjectName("Root")
        lay = QStackedLayout(self)
        lay.setStackingMode(QStackedLayout.StackingMode.StackAll)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(background)
        lay.addWidget(content)
        lay.setCurrentWidget(content)
        background.lower()
        content.raise_()


class OsinturkWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1160, 780)
        self.setMinimumSize(960, 660)
        self.dark = True  # ── STANDART: KOYU TEMA (tek tema) ──

        self.bg = AnimatedBackground(dark=self.dark)

        self.stack = QStackedWidget()
        self.stack.setObjectName("Content")
        self.login = LoginView()
        self.main = MainView()
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.main)

        self.setCentralWidget(RootWidget(self.bg, self.stack))

        self.login.logged_in.connect(self._enter_app)
        QApplication.instance().setStyleSheet(build_qss(self.dark))

    def _enter_app(self, name):
        self.main.set_user(name)
        self.stack.setCurrentWidget(self.main)
        fade_in(self.main, 460)              # ekranın tümü lineer belirir
        QTimer.singleShot(60, self.main.play_enter_animation)  # kartlar sıralı gelir


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    win = OsinturkWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
