
# Endlostafel - Ein einfaches Schreibprogramm für interaktive Tafeln
# Copyright (C) 2021  Christian Hoffmann
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/.

import sys
import logging
from functools import partial
from argparse import ArgumentParser
from typing import IO

from PySide6.QtCore import QLocale, QMarginsF, QSettings, QDate, QTime, QTimer, Qt, Slot
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QColor, QGuiApplication, QPainter, QPixmap, QPalette, QFont, QUndoStack
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QMainWindow, QMenu, QMessageBox, QSizePolicy, QToolBar, QToolButton, QWidget, QWidgetAction, QColorDialog, QUndoView


from icons import ColorIcon, SVGIcon
from items import Pixelbild, SVGBild, Karopapier, Linienpapier, TextItem
from vordrucke import MmLogDialog
from tafelview import Tafelview, Werkzeug, Status
from paletten import dark as paletteDark, light as paletteLight
from logwindow import LogWindowHandler, LogWindow
from undo import UndoWindow

# Zum Erzeugen der exe:
# pyinstaller.exe -F -i "oszli-icon.ico" -w endlostafel.py

VERSION='2.15'


class Editor(QMainWindow):

    def __init__(self, settings: QSettings, debug=False, undoview=False):
        super().__init__()
        QApplication.instance().applicationStateChanged.connect(self.lateInit)
        self._settings = settings
        self._debug = debug
        self._undoview = undoview
        self.logwindow = LogWindow(self)
        self._ungespeichert = False
        uhr = Uhr(self)
        self.undostack = QUndoStack(self)

        isdarkmode = False if self._settings.value("editor/darkmode", False) == 'false' else True
        QApplication.setPalette(paletteDark if isdarkmode else paletteLight)

        # Das wichtigste: Die QGraphicsView
        self._tafelview = Tafelview(self, self.undostack, self.getBigPointFactor(), self.getVeryBigPointFactor(), self.getKalibriert())

        # Die Statusleiste wird gebastelt
        self._speicherlabel = QLabel()
        self.statusBar().addWidget(uhr)
        self.statusBar().addPermanentWidget(self._speicherlabel)
        self.statusBar().addPermanentWidget(QLabel(f'Version {VERSION} '))

        # keine Kontextmenüs
        self.setContextMenuPolicy(Qt.NoContextMenu)

        # Actions erzeugen
        self._actC1 = Action( 'foreground', 'Normal', self, iscolor=True)
        actC2 = Action(  'royalblue',   'Blau', self, iscolor=True)
        actC3 = Action(        'red',    'Rot', self, iscolor=True)
        actC4 = Action(      'green',   'Grün', self, iscolor=True)
        self._coloractions = {
            self._actC1: 'foreground',
            actC2:  'royalblue',
            actC3:        'red',
            actC4:      'green',
        }
        self._colorgroup = QActionGroup(self)
        self.configureActionDict(self._coloractions, self._colorgroup, self.pencolorchange)
        self._actCbel = Action('customcolor', 'Farbauswahldialog', self)
        self._actCbel.setCheckable(True)
        self._actCbel.triggered.connect(self.customcolor)
        self._colorgroup.addAction(self._actCbel)

        actP1 = Action( 'pensize-1px',  '1px', self)
        self._actP2 = Action( 'pensize-3px',  '3px', self)
        actP3 = Action( 'pensize-5px', '10px', self)
        actP4 = Action('pensize-20px', '20px', self)
        self._pensizeactions = {
            actP1:  1,
            self._actP2:  3,
            actP3:  5,
            actP4: 20,
        }
        self._pensizegroup = QActionGroup(self)
        self.configureActionDict(self._pensizeactions, self._pensizegroup, self.pensizechange)

        self._actFreihand  = Action(    'stift',              'Freihand', self)
        actLinie     = Action(    'linie',          'Gerade Linie', self)
        actPfeil     = Action(    'pfeil',                 'Pfeil', self)
        actLinieS    = Action(   'linies','Gerade Linie (hor/ver)', self)
        actPfeilS    = Action(   'pfeils',       'Pfeil (hor/ver)', self)
        actKreis     = Action(    'kreis',                 'Kreis', self)
        actQuadrat   = Action(  'quadrat',               'Quadrat', self)
        actEllipse   = Action(  'ellipse',               'Ellipse', self)
        actRechteck  = Action( 'rechteck',              'Rechteck', self)
        actKreisF    = Action(   'kreisf',       'gefüllter Kreis', self)
        actQuadratF  = Action( 'quadratf',     'gefülltes Quadrat', self)
        actEllipseF  = Action( 'ellipsef',      'gefüllte Ellipse', self)
        actRechteckF = Action('rechteckf',    'gefülltes Rechteck', self)
        actRubber    = Action( 'radierer',              'Radieren', self)
        actEdit      = Action(     'edit',     'Objekte editieren', self)
        self._toolactions = {
            self._actFreihand:  Werkzeug.Freihand,
            actLinie:     Werkzeug.Linie,
            actPfeil:     Werkzeug.Pfeil,
            actLinieS:    Werkzeug.LinieS,
            actPfeilS:    Werkzeug.PfeilS,
            actKreis:     Werkzeug.Kreis,
            actQuadrat:   Werkzeug.Quadrat,
            actEllipse:   Werkzeug.Ellipse,
            actRechteck:  Werkzeug.Rechteck,
            actKreisF:    Werkzeug.KreisF,
            actQuadratF:  Werkzeug.QuadratF,
            actEllipseF:  Werkzeug.EllipseF,
            actRechteckF: Werkzeug.RechteckF,
        }
        self._statusactions = {
            actRubber:    Status.radieren,
            actEdit:      Status.editieren,
        }
        self._statusgroup = QActionGroup(self)
        self.configureActionDict(self._toolactions, self._statusgroup, self.toolchange)
        self.configureActionDict(self._statusactions, self._statusgroup, self.statuschange)

        self._deleteAction     = Action(       'delete', 'Löschen', self)
        self._copyAction       = Action(         'copy', 'Kopieren', self)
        self._undoAction             = self.undostack.createUndoAction(self)
        self._redoAction             = self.undostack.createRedoAction(self)
        speichernAction        = Action(         'save', 'Speichern', self)
        ladenAction            = Action(         'open', 'Laden', self)
        saveSettingsAction     = Action(        'prefs', 'Einstellungen (Farbe, Stiftgröße, Palette) speichern', self)
        zoominAction           = Action(      'zoom-in', 'Zoom in', self)
        zoomorigAction         = Action('zoom-original', 'Zoom normal', self)
        zoomoutAction          = Action(     'zoom-out', 'Zoom out', self)
        clearAction            = Action(        'trash', 'Alles Löschen', self)
        geodreieckAction       = Action(   'geodreieck', 'Geodreieck', self)
        self._fullscreenAction = Action(   'fullscreen', 'Vollbild', self)
        exitAction             = Action(         'exit', 'Tschüß', self)
        helpAction             = Action(         'help', 'Hilfe/Info', self)
        self._darkmodeAction   = Action(         'dark', 'Dunkelmodus', self)
        clipboardPasteAction   = Action('fromclipboard', 'Zwischenablage einfügen', self)
        kalibrierenAction      = Action('radierer-kalibrieren', 'Radierer kalibrieren', self)

        mmPapierDialog = MmLogDialog()
        mmPapierAction = Action('logpapier', 'mm/log-Papier', self)
        self._karopapierAction = Action('karopapier', 'kariertes Papier', self)
        self._linienpapierAction = Action('linienpapier', 'liniertes Papier', self)
        vordruckActions = ActionWidget(self, mmPapierAction, self._karopapierAction, self._linienpapierAction)
        vordruckActions.setPopupMode(QToolButton.InstantPopup)

        geodreieckAction.setCheckable(True)
        self._fullscreenAction.setCheckable(True)
        self._darkmodeAction.setCheckable(True)
        self._darkmodeAction.setChecked(isdarkmode)
        
        # Toolbar erzeugen und Actions platzieren
        self._toolframe = QToolBar()
        self.addToolBar(Qt.BottomToolBarArea, self._toolframe)

        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        pensizetool = ActionWidget(self, actP1, self._actP2, actP3, actP4, popupMode=QToolButton.InstantPopup)
        linesTool = ActionWidget(self, actLinie, actLinieS)
        pfeileTool = ActionWidget(self, actPfeil, actPfeilS)
        formsTool = ActionWidget(self, actKreis, actQuadrat, actEllipse, actRechteck, actKreisF, actQuadratF, actEllipseF, actRechteckF)

        self._toolframe.addAction(exitAction)
        self._toolframe.addWidget(left_spacer)

        self._toolframe.addAction(self._darkmodeAction)
        self._toolframe.addAction(self._fullscreenAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(vordruckActions)
        self._toolframe.addAction(geodreieckAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(self._actC1)
        self._toolframe.addAction(actC2)
        self._toolframe.addAction(actC3)
        self._toolframe.addAction(actC4)
        self._toolframe.addAction(self._actCbel)
        self._toolframe.addSeparator()

        self._toolframe.addAction(pensizetool)
        self._toolframe.addSeparator()

        self._toolframe.addAction(self._actFreihand)
        self._toolframe.addAction(linesTool)
        self._toolframe.addAction(pfeileTool)
        self._toolframe.addAction(formsTool)
        self._toolframe.addAction(actRubber)
        self._toolframe.addAction(actEdit)
        self._toolframe.addSeparator()

        self._toolframe.addAction(self._deleteAction)
        self._toolframe.addAction(self._copyAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(self._undoAction)
        self._toolframe.addAction(self._redoAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(speichernAction)
        self._toolframe.addAction(ladenAction)
        self._toolframe.addAction(clipboardPasteAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(zoominAction)
        self._toolframe.addAction(zoomorigAction)
        self._toolframe.addAction(zoomoutAction)
        self._toolframe.addSeparator()

        self._toolframe.addAction(clearAction)
        self._toolframe.addWidget(right_spacer)
        self._toolframe.addAction(saveSettingsAction)
        self._toolframe.addAction(kalibrierenAction)
        self._toolframe.addAction(helpAction)


        self._deleteAction.triggered.connect(self._tafelview.deleteItems)
        self._copyAction.triggered.connect(self._tafelview.copyItems)
        speichernAction.triggered.connect(self.speichern)
        ladenAction.triggered.connect(self.laden)
        saveSettingsAction.triggered.connect(self.einstellungenSpeichern)
        zoomoutAction.triggered.connect(self._tafelview.zoomout)
        zoomorigAction.triggered.connect(self._tafelview.zoomreset)
        zoominAction.triggered.connect(self._tafelview.zoomin)
        clearAction.triggered.connect(self._tafelview.clearall)
        geodreieckAction.triggered.connect(lambda: self._tafelview.enableGeodreieck(geodreieckAction.isChecked()))
        self._fullscreenAction.triggered.connect(lambda: self.fullScreen(self._fullscreenAction.isChecked()))
        exitAction.triggered.connect(self.close)
        helpAction.triggered.connect(self.showHelp)
        self._darkmodeAction.triggered.connect(lambda: QApplication.instance().setPalette(paletteDark if self._darkmodeAction.isChecked() else paletteLight))
        mmPapierAction.triggered.connect(lambda: mmPapierDialog.exec())
        mmPapierDialog.mmPapierCreated.connect(self._tafelview.importItem)
        clipboardPasteAction.triggered.connect(self.importClipboard)
        kalibrierenAction.triggered.connect(self._tafelview.starteKalibrieren)
        self._undoAction.setIcon(SVGIcon('undo'))
        self._redoAction.setIcon(SVGIcon('redo'))
        self._toolframe.findChild(QToolButton, "qt_toolbar_ext_button").setIcon(SVGIcon('toolbarbutton'))

    def initView(self):
        self.setCentralWidget(self._tafelview)

        # Zu den Signals verbinden
        self._tafelview.eswurdegemalt.connect(self.tafelHatGemalt)
        self._tafelview.statusbarinfo.connect(self.statusbarinfo)
        self._tafelview.kalibriert.connect(self.kalibriertSpeichern)
        self._karopapierAction.triggered.connect(lambda: self._tafelview.importItem(Karopapier()))
        self._linienpapierAction.triggered.connect(lambda: self._tafelview.importItem(Linienpapier()))
        self.displayMemoryUsage()
        
        # Trigger das Standard-Werkzeug freihand
        self._actFreihand.trigger()

        # Trigger die Standard-Farbe
        colorstr = self._settings.value('editor/colorstr', 'Normal')
        coloraction = [act for act in self._coloractions if act.text() == colorstr]
        if coloraction:
            coloraction.pop().trigger()
        else:
            self._actC1.trigger()

        # Trigger die Standard Pensize
        pensize = self._settings.value('editor/pensize', '3px')
        pensizeaction = [act for act in self._pensizeactions if act.text() == pensize]
        if pensizeaction:
            pensizeaction.pop().trigger()
        else:
            self._actP2.trigger()

    def lateInit(self, appstate: Qt.ApplicationState):
        'Einige Dinge können erst nach dem aktivieren des Fenster eingestellt werden (z.B. viewport)'
        if appstate == Qt.ApplicationActive:
            if self._debug:
                self.logwindow.show()
            self.initView()
            self._fullscreenAction.setChecked(self.isFullScreen())
            self._tafelview.setSceneRectFromViewport()
            QApplication.instance().applicationStateChanged.disconnect()
            if self._undoview:
                UndoWindow(self, self.undostack).show()

    def tafelHatGemalt(self):
        self.setUngespeichert()
        self.displayMemoryUsage()

    def getKalibriert(self) -> float:
        return float(self._settings.value('editor/kalibriert', 1500))

    def getBigPointFactor(self) -> float:
        return float(self._settings.value('editor/bigpointfactor', 3))

    def getVeryBigPointFactor(self) -> float:
        return float(self._settings.value('editor/verybigpointfactor', 6))

    def setUngespeichert(self):
        self._ungespeichert = True

    def kalibriertSpeichern(self, value: float):
        self._settings.setValue('editor/kalibriert', value)
        self.statusbarinfo(f"Kalibrierter Wert: {value}", 5000)
        QApplication.beep()

    def displayMemoryUsage(self):
        anzahl = len(self._tafelview.scene().items())
        self._speicherlabel.setText(f'{anzahl} Element' + ('' if anzahl == 1 else 'e') )

    def ungespeichertFortfahren(self, text: str):
        if self._ungespeichert:
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Warning)
            mb.setText('Es gibt ungesicherte Änderungen.')
            mb.setInformativeText('Wollen Sie wirklich fortfahren?')
            mb.addButton(text, QMessageBox.YesRole)
            neinButton = mb.addButton('Ich will speichern', QMessageBox.NoRole)
            mb.exec()
            if mb.clickedButton() == neinButton:
                return False
        self._ungespeichert = False
        return True

    def closeEvent(self, event: QCloseEvent):
        if not self.ungespeichertFortfahren('Trotzdem Schließen'):
            event.ignore()
            return
        event.accept()

    def configureActionDict(self, actiondict, actiongroup, slot):
        for action in actiondict:
            action.setCheckable(True)
            actiongroup.addAction(action)
            action.triggered.connect(partial(slot, actiondict[action]))

    def setActionsDisabled(self, actionarray, value):
        for action in actionarray:
            action.setDisabled(value)

    def toolchange(self, tool):
        self.statuschange(Status.kreativ)
        self._tafelview.setTool(tool)

    def statuschange(self, status):
        if status == Status.kreativ:
            self.setActionsDisabled(self._coloractions, False)
            self.setActionsDisabled([self._actCbel], False)
            self.setActionsDisabled(self._pensizeactions, False)
        else:
            self.setActionsDisabled(self._coloractions, True)
            self.setActionsDisabled([self._actCbel], True)
            self.setActionsDisabled(self._pensizeactions, True)

        if status == Status.editieren:
            self.setActionsDisabled([self._deleteAction, self._copyAction], False)
        else:
            self.setActionsDisabled([self._deleteAction, self._copyAction], True)

        self._tafelview.setStatus(status)

    def pensizechange(self, pensize):
        self._tafelview.setPensize(pensize)
    
    def pencolorchange(self, colorname):
        self._tafelview.setPencolor(colorname)

    @Slot(str,int)
    def statusbarinfo(self, txt, timeout):
        self.statusBar().showMessage(txt,timeout)

    def laden(self):
        filename = QFileDialog.getOpenFileName(self, 'SVG-Datei laden', filter='Alle Dateien (*.*);;SVG-Dateien (*.svg);;Bilder (*.png *.xpm *.bmp *.jpg)')[0]
        if filename:
            if filename[-4:] == '.svg':
                self._tafelview.importItem(SVGBild(filename))
            else:
                self._tafelview.importItem(Pixelbild(QPixmap(filename)))

    def einstellungenSpeichern(self):
        self._settings.setValue('editor/darkmode', self._darkmodeAction.isChecked())
        self._settings.setValue('editor/show', self.settingShowName())
        self._settings.setValue('editor/colorstr', self._colorgroup.checkedAction().text())
        self._settings.setValue('editor/pensize', self._pensizegroup.checkedAction().text())
        text = f'''<p>Folgende Einstellungen sind gespeichert:</p>
        <table>
            <tr><td align='right'>Farbe:&nbsp;</td><td>{self._settings.value('editor/colorstr')}</td></tr>
            <tr><td align='right'>Stiftbreite:&nbsp;</td><td>{self._settings.value('editor/pensize')}</td></tr>
            <tr><td align='right'>Dunkler Modus:&nbsp;</td><td>{self._settings.value('editor/darkmode')}</td></tr>
            <tr><td align='right'>Start der Anwendung:&nbsp;</td><td>{self._settings.value('editor/show')}</td></tr>
            <tr><td align='right'>Kalibrierter Flächeninhalt:&nbsp;</td><td>{self._settings.value('editor/kalibriert')}</td></tr>
            <tr><td align='right'>BigPointFactor:&nbsp;</td><td>{self._settings.value('editor/bigpointfactor',2)}</td></tr>
            <tr><td align='right'>VeryBigPointFactor:&nbsp;</td><td>{self._settings.value('editor/verybigpointfactor',4)}</td></tr>
        </table>
        <p>Der Start der Anwendung kann mit der Kommandozeilenoption <code>--show [fullscreen,maximized,normal]</code> gesetzt werden.
        Rufen Sie die Endlostafel mit der Option <code>--help</code> auf, um alle Kommandozeilenoptionen zu sehen. </p>'''
        QMessageBox.information(self,'Einstellungen speichern',text)

    def settingShowName(self):
        name = 'normal'
        if self.isFullScreen():
            name = 'fullscreen'
        elif self.isMaximized():
            name = 'maximized'
        return name

    def speichern(self):
        filename = QFileDialog.getSaveFileName(self, "Datei für den SVG-Export öffnen", filter='SVG-Dateien (*.svg);;Alle Dateien (*.*)')[0]
        if not filename:
            return

        backgroundcolor = self.palette().color(QPalette.Base)
        rect = self._tafelview.scene().itemsBoundingRect().marginsAdded(QMarginsF(50,50,50,50))
        generator = QSvgGenerator()
        generator.setFileName(filename)
        generator.setViewBox(rect)
        generator.setTitle('Tafelbild')
        generator.setDescription('Tafelbild')
        generator.setResolution(QGuiApplication.primaryScreen().physicalDotsPerInch())
        generator.setSize(rect.size().toSize())
        painter = QPainter()
        painter.begin(generator)
        if backgroundcolor != QColor(Qt.white):
            painter.fillRect(rect,backgroundcolor)
        self._tafelview.scene().render(painter,rect,rect)
        painter.end()
        self._ungespeichert = False

    def fullScreen(self, ischecked: bool):
        if ischecked:
            self.showFullScreen()
        else:
            self.showMaximized()

    def importClipboard(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()

        if mimeData.hasImage():
            item = Pixelbild(QPixmap(mimeData.imageData()))
            self._tafelview.importItem(item)
        elif mimeData.hasHtml():
            item = TextItem()
            item.setHtml(mimeData.html())
            self._tafelview.importItem(item)
        elif mimeData.hasText():
            item = TextItem()
            item.setPlainText(mimeData.text())
            self._tafelview.importItem(item)

    def showHelp(self):
        text = '''<h1>Endlostafel</h1>
            <h3>Autor: Christian Hoffmann</h3>
            <p>Dieses Programm stellt ein einfaches Schreibwerkzeug für den Frontalunterricht dar.</p>
            <h4>Kommandozeilenoptionen</h4>
            <p><code>--logging [debug,info,warning,error,critical]<br/>
            --show [fullscreen,maximized,normal]<br/>
            --undoview<br/>
            --bigpointfactor float<br/>
            --verybigpointfactor float</code></p>
            <p>Startet die Tafel in Vollbild, maximiertem Fenster oder Fenster in Normalgröße. Bei
            einem ungültigen Wert, wird maximized angenommen. Ist diese Option nicht gegeben, wird der Wert
            in den Einstellungen angenommen. Ist der Wert in den Einstellungen nicht gesetzt, wird mit
            maximized gestartet.</p>
            <h4>Bekannte Bugs</h4>
            <ul>
                <li>Beim Editieren von Objekten funktioniert das Rubberband erst beim zweiten
                    Anlauf (nur Touchscreens).</li>
            </ul>
            <p>Berlin, Oktober 2023</p>'''
        QMessageBox.about(self, 'Über Endlostafel',text)

    def customcolor(self):
        color = QColorDialog.getColor(parent=self)
        self._tafelview.setPencolor(color.name())


class Action(QAction):
    def __init__(self, iconname: str, text: str, parent: QWidget, iscolor=False):
        super().__init__(text, parent)
        if iscolor:
            self.setIcon(ColorIcon(iconname))
        else:
            self.setIcon(SVGIcon(iconname))

class ActionWidget(QWidgetAction):
    def __init__(self, parent, *actionArray, popupMode: QToolButton.ToolButtonPopupMode = QToolButton.MenuButtonPopup):
        super().__init__(parent)
        menu = QMenu(parent)
        for action in actionArray:
            menu.addAction(action)
        self.button = QToolButton()
        self.button.setPopupMode(popupMode)
        self.button.setDefaultAction(actionArray[0])
        self.button.setMenu(menu)
        self.setDefaultWidget(self.button)
        menu.triggered.connect(self.button.setDefaultAction)
    
    def setPopupMode(self, mode):
        self.button.setPopupMode(mode)


class Uhr(QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        #self.setStyleSheet("font-size: 14pt; font-family: Courier; font-weight: bold;")
        self.setTextFormat(Qt.PlainText)
        font = QFont("Courier", 14, QFont.Bold)
        self.setFont(font)

        timer = QTimer(self)
        timer.timeout.connect(self.anzeige)
        timer.start(1000)
        self.anzeige()

    def anzeige(self):
        time = QTime.currentTime()
        date = QDate.currentDate()
        text = date.toString('dd.MMM yyyy')+' - '+time.toString('hh:mm')
        if time.second() % 2 == 0:
            text = text[:-3]+' '+text[-2:]
        self.setText(text)

class EndlostafelArgumentParserError(Exception):
    pass

class EndlostafelArgumentParser(ArgumentParser):
    def error(self, message):
        raise EndlostafelArgumentParserError(message+"\n"+self.format_usage())
    def print_help(self, file: IO[str] | None = None) -> None:
        raise EndlostafelArgumentParserError(self.format_help())

logger = logging.getLogger('GUI')

def ausnahmen(typ, ausnahme, wasanderes):
    logger.exception(ausnahme, exc_info=True)

if __name__ == "__main__":
    QLocale.setDefault(QLocale.German)
    app = QApplication()
    app.setStyle('Fusion')
    app.setWindowIcon(SVGIcon('oszli'))
    app.setApplicationDisplayName('Endlostafel')

    parser = EndlostafelArgumentParser(description='Endlostafel für das digitale Klassenzimmer. Einfach nur schreiben.')
    parser.add_argument('--logging',choices=['debug','info','warning','error','critical'],help='Öffnet ein Log-Window mit Debug-Meldungen.')
    parser.add_argument('--show',choices=['normal','fullscreen','maximized'],help='Gibt an, wie die Tafel geöffnet werden soll.')
    parser.add_argument('--bigpointfactor',type=float,help='Größe eines großen Touchpoints gegenüber des kalibrierten Touchpoints.')
    parser.add_argument('--verybigpointfactor',type=float,help='Größe eines sehr großen Touchpoints gegenüber des kalibrierten Touchpoints.')
    parser.add_argument('--undoview',action='store_true',help='Zeigt ein Undo-Fenster an.')

    try:
        options=vars(parser.parse_args())
    except EndlostafelArgumentParserError as e:
        logwindow = LogWindow(None)
        logwindow.show()
        logwindow.append(e.args[0])
        sys.exit(app.exec())

    if options['logging']:
        logger.setLevel(options['logging'].upper())
    sys.excepthook = ausnahmen


    settings = QSettings('hoffmann', 'endlostafel')
    if options['show']:
        showmode = options['show']
    else:
        showmode = settings.value('editor/show','maximized')

    if options['bigpointfactor']:
        settings.setValue('editor/bigpointfactor', options['bigpointfactor'])

    if options['verybigpointfactor']:
        settings.setValue('editor/verybigpointfactor', options['verybigpointfactor'])

    d = Editor(settings, options['logging'], options['undoview'])
    handler = LogWindowHandler(d.logwindow)

    logger.addHandler(handler)
    logger.info(f"Starte Endlostafel Version {VERSION}")

    if showmode == 'normal':
        d.resize(800,600)
        d.showNormal()
    elif showmode == 'fullscreen':
        d.showFullScreen()
    else:
        d.showMaximized()

    sys.exit(app.exec())

