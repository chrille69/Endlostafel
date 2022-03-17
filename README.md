# Endlostafel für das digitale Klassenzimmer
Eine einfache Schreibfläche für digitale Tafeln mit nützlichen Extras für den Unterricht.

Diese Open-Source Softwarelösung unterliegt der GPL.

## Hintergrund
Eine digitale Tafel besteht aus zwei Hardware-Komponenten:
* einen Beamer oder Touchbildschirm (Display) mit Stift oder Touchfunktion und
* einem PC.

Das Display fungiert einerseits als Anzeigegerät und andererseits als Eingabegerät (Maus) für den PC.
Daher ist das Display mit HDMI oder DP und mit USB verbunden.
Alternativ gibt es auch Lösungen, bei dem die Displays mit dem Rechner über das Netzwerk (LAN) kommunizieren. 

## Funktionsumfang
Dieses Programm stellt eine möglichst große Schreibfläche für den Unterricht zur Verfügung.
Es wurde so konzipiert, dass alle Funktionen mit Klicks ausgeführt werden können.
Die Menge an implementierten Funktionen sind auf ein Nötigstes reduziert.
Es ist kein Zeichenprogramm.

Folgende Funktionen stehen zur Verfügung:

* Hell- und Dunkelmodus
* Vollbildschirm
* Vier vordefinierte Farben
* Vier vordefinierte Stiftgrößen
* Linien
* Pfeile
* Einfache geometrische Formen wie Kreise, Ellipsen, Quadrate und Rechtecke
* Kariertes Papier, liniertes Papier, Logarithmuspapier, Millimeterpapier
* Einblenden eines Geodreiecks mit Snap-Funktion
* Verschieben und Löschen einzelner Elemente
* Speichern der Inhalte als SVG-Dateien
* Laden von SVGs und Bitmaps
* Einfügen der Zwischenablage als Grafik
* Speichern einiger weniger Voreinstellungen
* Zoomen einzelner Elemente oder der gesamten Zeichenfläche

Einmal gespeicherte Tafelbilder können im nachhinein **nicht** mehr bearbeitet werden.

## Technische Details

Das Programm ist in Python 3 geschrieben (https://www.python.org/) und benötigt
die Bibliotheken **pyside6**, **psutil** und zum Erzeugen einer statischen, ausführbaren
Datei **pyinstaller**, die mit Hilfe von **pip** installiert werden können.

### Pyside6
Pyside6 ist eine von Qt zur Verfügung gestellte Python-Anbindung an die Bibliotheken von Qt (https://www.qt.io/).
SVG Grafiken werden über Qt verarbeitet und sind daher im Rahmen von XSVG  implementiert (https://doc.qt.io/qt-5/qtsvg-attribution-xsvg.html).

### Pyinstaller
Um unter Windows eine ausführbare Datei zu erzeugen, verwendet man den Befehl:

    pyinstaller.exe -F -i oszli-icon.ico -w endlostafel.py

## Bekannte Bugs
* Die Undo-Funktion funktioniert nicht beim Radieren oder Löschen von Objekten.
* Beim Umschalten in den Edit-Modus funktioniert das Rubberband erst beim zweiten Versuch (nur bei Touchscreens).

## Über den Autor
Ich bin Physik- und Mathematiklehrer an der Lise-Meitner-Schule in Berlin.
