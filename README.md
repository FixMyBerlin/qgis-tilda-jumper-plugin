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
- Toolbar-Button „TILDA-Region“: öffnet die aktuelle QGIS-Kartenstelle in einer konfigurierten TILDA-Region im Browser

---

## Regionen konfigurieren

Über „Erweiterungen → Tilda Jump → TILDA-Regionen konfigurieren…“ (oder unten im Menü des Toolbar-Buttons „TILDA-Region“):

- Slug eintippen (z. B. `berlin`) und **Enter** drücken – schon ist die Region in der Liste.
- Entfernen: Einträge markieren und **Entf** drücken oder „Entfernen“ klicken.

Ein Klick auf eine Region im Menü öffnet `https://tilda-geo.de/regionen/<slug>?map=zoom/lat/lon` mit Mittelpunkt und Maßstab der aktuellen QGIS-Kartenansicht im Browser. Statt eines Slugs kann auch eine TILDA-URL eingefügt werden; der Slug wird daraus übernommen.

---

## Installation per ZIP

1. Hier in GitHub grünen Button „Code“ → „Download ZIP“ anklicken.
2. Im QGIS Erweiterungsmanager direkt aus dem ZIP installieren.
