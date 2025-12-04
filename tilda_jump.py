# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QInputDialog
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsPointXY
)
from qgis.utils import iface

from urllib.parse import urlparse, parse_qs
import math


def tr(message):
    return QCoreApplication.translate("TildaJumpPlugin", message)


def jump_to_tilda_url(url: str):
    """
    Liest eine TILDA-URL mit map=zoom/lat/lon (WGS84) und setzt
    die QGIS-Kartenansicht auf diese Position mit ähnlichem Maßstab.
    """
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if "map" not in query:
        raise ValueError("In der URL wurde kein 'map=' Parameter gefunden.")

    map_param = query["map"][0]  # z.B. "12.3/52.546/13.423"

    parts = map_param.split("/")
    if len(parts) != 3:
        raise ValueError("Der 'map'-Parameter hat nicht das Format zoom/lat/lon.")

    zoom = float(parts[0])
    lat = float(parts[1])
    lon = float(parts[2])

    # WGS84 -> Projekt-Koordinatensystem transformieren
    wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
    project_crs = QgsProject.instance().crs()
    transform = QgsCoordinateTransform(wgs84, project_crs, QgsProject.instance())

    # Achtung: QgsPointXY(lon, lat) – Reihenfolge ist x=Lon, y=Lat
    center_project = transform.transform(QgsPointXY(lon, lat))

    # Maßstab aus Web-Mercator-Zoom ungefähr ableiten
    earth_circumference = 40075016.68557849  # Meter
    initial_resolution = earth_circumference / 256.0  # Auflösung bei Zoom 0 am Äquator

    # Auflösung für gegebenen Zoom (inkl. cos(lat) für Breitenabhängigkeit)
    resolution = (initial_resolution / (2 ** zoom)) * math.cos(math.radians(lat))

    # Auflösung -> Maßstab
    scale = resolution / 0.00028

    canvas = iface.mapCanvas()
    canvas.setCenter(center_project)
    canvas.zoomScale(scale)
    canvas.refresh()


class TildaJumpPlugin:
    def __init__(self, iface_):
        """
        iface_ : QgisInterface
        """
        self.iface = iface_
        self.action = None

    def initGui(self):
        """
        Wird beim Laden des Plugins aufgerufen.
        Hier legen wir Menüeintrag und Toolbar-Icon an.
        """

        self.action = QAction(tr("Zu TILDA-URL springen..."), self.iface.mainWindow())
        self.action.setStatusTip(tr("TILDA-Webmap-URL mit map=zoom/lat/lon einfügen und Canvas dorthin verschieben."))
        self.action.triggered.connect(self.run)

        # Plugin-Menüeintrag
        self.iface.addPluginToMenu(tr("&Tilda Jump"), self.action)

        # Optional: Toolbar-Icon hinzufügen
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """
        Wird beim Deaktivieren/Entfernen des Plugins aufgerufen.
        Aufräumen.
        """
        if self.action is not None:
            self.iface.removePluginMenu(tr("&Tilda Jump"), self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None

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
