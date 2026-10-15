# -*- coding: utf-8 -*-
"""
Konfigurierte TILDA-Regionen: Speichern in den QGIS-Einstellungen
und der Konfigurationsdialog.
"""
import json
import re
from urllib.parse import urlparse

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

try:
    from qgis.PyQt.QtWidgets import QShortcut
except ImportError:  # Qt6: QShortcut liegt in QtGui
    from qgis.PyQt.QtGui import QShortcut
from qgis.core import QgsSettings

TILDA_BASE_URL = "https://tilda-geo.de"
SETTINGS_KEY = "TildaJump/regions"
SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def tr(message):
    return QCoreApplication.translate("TildaJumpPlugin", message)


def load_regions():
    """Liste der konfigurierten Region-Slugs aus den QGIS-Einstellungen."""
    raw = QgsSettings().value(SETTINGS_KEY, "[]")
    try:
        regions = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return [r for r in regions if isinstance(r, str) and r]


def save_regions(regions):
    QgsSettings().setValue(SETTINGS_KEY, json.dumps(regions))


def parse_region_input(text: str) -> str:
    """
    Akzeptiert einen Slug ("berlin") oder eine TILDA-URL
    ("https://tilda-geo.de/regionen/berlin?map=12/52.5/13.4") und gibt den Slug zurück.
    """
    text = text.strip()
    if "/" in text:
        segments = [s for s in urlparse(text).path.split("/") if s]
        if "regionen" not in segments or segments.index("regionen") + 1 >= len(segments):
            raise ValueError(tr("In der URL wurde kein /regionen/<slug> gefunden."))
        text = segments[segments.index("regionen") + 1]
    if not SLUG_PATTERN.match(text):
        raise ValueError(tr("Ungültiger Slug: {}").format(text))
    return text


class RegionsDialog(QDialog):
    """Regionen-Liste bearbeiten: Enter fügt hinzu, Entf/Button entfernt."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("TILDA-Regionen konfigurieren"))
        self.setMinimumWidth(420)
        self.regions = load_regions()

        self.input = QLineEdit()
        self.input.setPlaceholderText(tr("Slug oder TILDA-URL eingeben und Enter drücken"))
        self.input.returnPressed.connect(self.add_region)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #c00;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        delete_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self.list)
        delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        delete_shortcut.activated.connect(self.remove_selected)

        # Keine Default-Buttons, damit Enter im Eingabefeld den Dialog nicht schließt
        remove_button = QPushButton(tr("Entfernen"))
        remove_button.setAutoDefault(False)
        remove_button.clicked.connect(self.remove_selected)
        close_button = QPushButton(tr("Schließen"))
        close_button.setAutoDefault(False)
        close_button.clicked.connect(self.accept)

        buttons = QHBoxLayout()
        buttons.addWidget(remove_button)
        buttons.addStretch()
        buttons.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.input)
        layout.addWidget(self.error_label)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.refresh_list()

    def refresh_list(self):
        self.list.clear()
        for slug in self.regions:
            self.list.addItem(QListWidgetItem(slug))

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(bool(message))

    def add_region(self):
        text = self.input.text().strip()
        if not text:
            return
        try:
            slug = parse_region_input(text)
        except ValueError as e:
            self.show_error(str(e))
            return

        if slug not in self.regions:
            self.regions.append(slug)
            self.regions.sort()
            save_regions(self.regions)

        self.show_error("")
        self.input.clear()
        self.refresh_list()

    def remove_selected(self):
        slugs = {item.text() for item in self.list.selectedItems()}
        if not slugs:
            return
        self.regions = [r for r in self.regions if r not in slugs]
        save_regions(self.regions)
        self.refresh_list()
