# TildaJump – QGIS Plugin

TildaJump ist ein kleines QGIS-Plugin, mit dem du per TILDA-Webmap-URL direkt zu einer Position im QGIS-Kartenfenster springen kannst.  

Es liest den Parameter `map=zoom/lat/lon` aus einer URL wie:

https://tilda-geo.de/regionen/<REGION>?map=12.3/52.546/13.423&config=...


und setzt den QGIS-Canvas auf die entsprechende Position (lat/lon in WGS84) mit einem ähnlichen Maßstab.

---

## Features

- Eingabedialog für eine TILDA-URL
- Extrahiert `zoom`, `lat`, `lon` aus `map=` (WGS84)
- Transformiert automatisch ins aktuelle Projekt-Koordinatensystem
- Setzt Kartenmittelpunkt und Maßstab im QGIS-Canvas
- Aktion kann mit einem eigenen Tastenkürzel belegt werden

---

## Installation per ZIP

1. Hier in GitHub grünen Button „Code“ → „Download ZIP“ anklicken.
2. Im QGIS Erweiterungsmanager direkt aus dem ZIP installieren.
