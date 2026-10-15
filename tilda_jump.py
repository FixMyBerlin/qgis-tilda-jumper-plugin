# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QMenu, QToolButton
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsPointXY
)
from qgis.utils import iface

from urllib.parse import quote, urlparse, parse_qs
import math

from .regions import TILDA_BASE_URL, RegionsDialog, load_regions

EARTH_CIRCUMFERENCE = 40075016.68557849  # Meter
# Auflösung bei Zoom 0 am Äquator (256px-Kacheln)
INITIAL_RESOLUTION = EARTH_CIRCUMFERENCE / 256.0
# Pixelgröße in Metern, die QGIS-Maßstab und Web-Mercator-Zoom verbindet
PIXEL_SIZE = 0.00028


def tr(message):
    return QCoreApplication.translate("TildaJumpPlugin", message)


def parse_map_param(map_param: str):
    """
    Zerlegt einen TILDA map-Parameter "zoom/lat/lon" in (zoom, lat, lon).
    """
    parts = map_param.split("/")
    if len(parts) != 3:
        raise ValueError("Der 'map'-Parameter hat nicht das Format zoom/lat/lon.")
    return float(parts[0]), float(parts[1]), float(parts[2])


def jump_to(zoom: float, lat: float, lon: float):
    """
    Setzt die QGIS-Kartenansicht auf eine WGS84-Position mit einem
    Maßstab ähnlich dem Web-Mercator-Zoom.
    """
    # WGS84 -> Projekt-Koordinatensystem transformieren
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    project_crs = QgsProject.instance().crs()
    transform = QgsCoordinateTransform(wgs84, project_crs, QgsProject.instance())

    # Achtung: QgsPointXY(lon, lat) – Reihenfolge ist x=Lon, y=Lat
    center_project = transform.transform(QgsPointXY(lon, lat))

    # Maßstab aus Web-Mercator-Zoom ungefähr ableiten
    # Auflösung für gegebenen Zoom (inkl. cos(lat) für Breitenabhängigkeit)
    resolution = (INITIAL_RESOLUTION / (2 ** zoom)) * math.cos(math.radians(lat))

    # Auflösung -> Maßstab
    scale = resolution / PIXEL_SIZE

    canvas = iface.mapCanvas()
    canvas.setCenter(center_project)
    canvas.zoomScale(scale)
    canvas.refresh()


def current_map_param() -> str:
    """
    Gegenstück zu jump_to: aktuelle QGIS-Kartenansicht als TILDA
    map-Parameter "zoom/lat/lon" (WGS84).
    """
    canvas = iface.mapCanvas()
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    project_crs = QgsProject.instance().crs()
    transform = QgsCoordinateTransform(project_crs, wgs84, QgsProject.instance())
    center = transform.transform(canvas.center())
    lat, lon = center.y(), center.x()

    resolution = canvas.scale() * PIXEL_SIZE
    zoom = math.log2(INITIAL_RESOLUTION * math.cos(math.radians(lat)) / resolution)
    zoom = min(max(zoom, 0), 22)  # TILDA akzeptiert Zoom 0–22

    return f"{zoom:.1f}/{lat:.5f}/{lon:.5f}"


def tilda_region_url(slug: str) -> str:
    """TILDA-URL der Region an der aktuellen QGIS-Kartenposition."""
    return f"{TILDA_BASE_URL}/regionen/{quote(slug)}?map={current_map_param()}"


def jump_to_tilda_url(url: str):
    """
    Liest eine TILDA-URL mit map=zoom/lat/lon (WGS84) und setzt
    die QGIS-Kartenansicht auf diese Position mit ähnlichem Maßstab.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if "map" not in query:
        raise ValueError("In der URL wurde kein 'map=' Parameter gefunden.")

    jump_to(*parse_map_param(query["map"][0]))  # z.B. "12.3/52.546/13.423"


class TildaJumpPlugin:
    def __init__(self, iface_):
        """
        iface_ : QgisInterface
        """
        self.iface = iface_
        self.action = None
        self.region_menu = None
        self.region_action = None
        self.region_toolbar_action = None
        self.config_action = None

    def initGui(self):
        """
        Wird beim Laden des Plugins aufgerufen.
        Hier legen wir Menüeinträge und Toolbar-Buttons an.
        """
        main_window = self.iface.mainWindow()

        self.action = QAction(tr("Zu TILDA-URL springen..."), main_window)
        self.action.setStatusTip(tr("TILDA-Webmap-URL mit map=zoom/lat/lon einfügen und Canvas dorthin verschieben."))
        self.action.triggered.connect(self.run)

        self.config_action = QAction(tr("TILDA-Regionen konfigurieren..."), main_window)
        self.config_action.triggered.connect(self.configure_regions)

        # Menü mit den konfigurierten Regionen, wird bei jedem Öffnen neu aufgebaut
        self.region_menu = QMenu(tr("Aktuelle Stelle in TILDA-Region öffnen"), main_window)
        self.region_menu.aboutToShow.connect(self.populate_region_menu)
        self.region_action = self.region_menu.menuAction()

        # Plugin-Menüeinträge
        self.iface.addPluginToMenu(tr("&Tilda Jump"), self.action)
        self.iface.addPluginToMenu(tr("&Tilda Jump"), self.region_action)
        self.iface.addPluginToMenu(tr("&Tilda Jump"), self.config_action)

        # Toolbar: URL-Sprung und Regionen-Auswahl
        self.iface.addToolBarIcon(self.action)
        region_button = QToolButton(main_window)
        region_button.setText(tr("TILDA-Region"))
        region_button.setToolTip(tr("Aktuelle Kartenstelle in einer TILDA-Region im Browser öffnen"))
        region_button.setMenu(self.region_menu)
        region_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.region_toolbar_action = self.iface.addToolBarWidget(region_button)

    def unload(self):
        """
        Wird beim Deaktivieren/Entfernen des Plugins aufgerufen.
        Aufräumen.
        """
        for action in (self.action, self.region_action, self.config_action):
            if action is not None:
                self.iface.removePluginMenu(tr("&Tilda Jump"), action)
        if self.action is not None:
            self.iface.removeToolBarIcon(self.action)
        if self.region_toolbar_action is not None:
            self.iface.removeToolBarIcon(self.region_toolbar_action)
        if self.region_menu is not None:
            self.region_menu.deleteLater()

        self.action = None
        self.region_menu = None
        self.region_action = None
        self.region_toolbar_action = None
        self.config_action = None

    def populate_region_menu(self):
        self.region_menu.clear()
        regions = load_regions()
        if not regions:
            empty = self.region_menu.addAction(tr("Keine Regionen konfiguriert"))
            empty.setEnabled(False)
        for slug in regions:
            action = self.region_menu.addAction(slug)
            action.triggered.connect(lambda _checked=False, s=slug: self.open_region(s))
        self.region_menu.addSeparator()
        self.region_menu.addAction(self.config_action)

    def configure_regions(self):
        RegionsDialog(self.iface.mainWindow()).exec()

    def open_region(self, slug):
        try:
            QDesktopServices.openUrl(QUrl(tilda_region_url(slug)))
        except Exception as e:
            self.iface.messageBar().pushWarning(tr("TildaJump Fehler"), f"{e}")

    def run(self):
        """
        Wird aufgerufen, wenn der Menüeintrag / Toolbar-Button
        (oder der Shortcut) ausgelöst wird.
        """
        url, ok = QInputDialog.getText(
            self.iface.mainWindow(),
            tr("TILDA-URL eingeben"),
            tr("Gesamte TILDA URL eingeben:")
        )

        if not ok or not url:
            return

        try:
            jump_to_tilda_url(url)
        except Exception as e:
            # Einfache Fehlermeldung über Statusleiste
            self.iface.messageBar().pushWarning(
                tr("TildaJump Fehler"),
                f"{e}"
            )
