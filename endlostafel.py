
import sys
import logging
from functools import partial
import os
import psutil

from PySide6.QtCore import QEvent, QLocale, QSettings, QSize, QTime, QTimer, Qt, Signal
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QColor, QGuiApplication, QPainter, QPixmap, QPalette
from PySide6.QtWidgets import QApplication, QFileDialog, QFrame, QGraphicsItem, QGraphicsTextItem, QLCDNumber, QLabel, QMainWindow, QMenu, QMessageBox, QSizePolicy, QToolBar, QToolButton, QWidget, QWidgetAction


from icons import getIconColor, getIconSvg
from items import Pixelbild, SVGBild, Karopapier, Linienpapier
from vordrucke import MmLogDialog
from tafelview import Tafelview
from paletten import dark as paletteDark, light as paletteLight

# Zum Erzeugen der exe:
# pyinstaller.exe -F -i "oszli-icon.ico" -w endlostafel.py

log = logging.getLogger(__name__)
VERSION='1.20'


class Editor(QMainWindow):

    newstatus = Signal(str)
    pencolorChanged = Signal(str)
    pensizeChanged = Signal(float)
    deleteClicked = Signal()
    copyClicked = Signal()
    undoClicked = Signal()
    redoClicked = Signal()
    zoominClicked = Signal()
    zoomoutClicked = Signal()
    zoomresetClicked = Signal()
    newItemCreated = Signal(QGraphicsItem)
    clearClicked = Signal()
    geodreieckClick = Signal(bool)
    paletteChanged = Signal()
    karopapierClicked = Signal()
    linienpapierClicked = Signal()


    def __init__(self, settings: QSettings):
        super().__init__()
        QApplication.instance().applicationStateChanged.connect(self.lateInit)

        self._settings = settings
        self._ungespeichert = False
        uhr = Uhr(self)

        isdarkmode = False if self._settings.value("editor/darkmode", False) == 'false' else True
        QApplication.setPalette(paletteDark if isdarkmode else paletteLight)

        # Das wichtigste: Die QGraphicsView
        self._tafelview = Tafelview(self)
        self.setCentralWidget(self._tafelview)

        # Die Statusleiste wird gebastelt
        self._process = psutil.Process(os.getpid())
        self._speicherlabel = QLabel()
        self.statusBar().addWidget(uhr, 1)
        self.statusBar().addPermanentWidget(self._speicherlabel)
        self.statusBar().addPermanentWidget(QLabel(f'Version {VERSION} '))
        self.displayMemoryUsage()



        # keine Kontextmenüs
        self.setContextMenuPolicy(Qt.NoContextMenu)

        # Actions erzeugen
        actC1 = Action( 'foreground', 'Normal', self, iscolor=True)
        actC2 = Action(       'blue',   'Blau', self, iscolor=True)
        actC3 = Action(        'red',    'Rot', self, iscolor=True)
        actC4 = Action(      'green',   'Grün', self, iscolor=True)
        self._coloractions = {
            actC1: 'foreground',
            actC2:       'blue',
            actC3:        'red',
            actC4:      'green',
        }
        self._colorgroup = QActionGroup(self)
        self.configureActionDict(self._coloractions, self._colorgroup, self.pencolorChanged.emit)

        actP1 = Action( 'pensize-1px',  '1px', self)
        actP2 = Action( 'pensize-3px',  '3px', self)
        actP3 = Action( 'pensize-5px', '10px', self)
        actP4 = Action('pensize-20px', '20px', self)
        self._pensizeactions = {
            actP1:  1,
            actP2:  3,
            actP3:  5,
            actP4: 20,
        }
        self._pensizegroup = QActionGroup(self)
        self.configureActionDict(self._pensizeactions, self._pensizegroup, self.pensizeChanged.emit)

        actFreihand  = Action(    'stift',           'Freihand', self)
        actLinie     = Action(    'linie',       'Gerade Linie', self)
        actPfeil     = Action(    'pfeil',              'Pfeil', self)
        actKreis     = Action(    'kreis',              'Kreis', self)
        actQuadrat   = Action(  'quadrat',            'Quadrat', self)
        actEllipse   = Action(  'ellipse',            'Ellipse', self)
        actRechteck  = Action( 'rechteck',           'Rechteck', self)
        actKreisF    = Action(   'kreisf',    'gefüllter Kreis', self)
        actQuadratF  = Action( 'quadratf',  'gefülltes Quadrat', self)
        actEllipseF  = Action( 'ellipsef',   'gefüllte Ellipse', self)
        actRechteckF = Action('rechteckf', 'gefülltes Rechteck', self)
        actRubber    = Action( 'radierer',           'Radieren', self)
        actEdit      = Action(     'edit',  'Objekte editieren', self)
        self._statusactions = {
            actFreihand:  Tafelview.statusFreihand,
            actLinie:     Tafelview.statusLinie,
            actPfeil:     Tafelview.statusPfeil,
            actKreis:     Tafelview.statusKreis,
            actQuadrat:   Tafelview.statusQuadrat,
            actEllipse:   Tafelview.statusEllipse,
            actRechteck:  Tafelview.statusRechteck,
            actKreisF:    Tafelview.statusKreisF,
            actQuadratF:  Tafelview.statusQuadratF,
            actEllipseF:  Tafelview.statusEllipseF,
            actRechteckF: Tafelview.statusRechteckF,
            actRubber:    Tafelview.statusRadiere,
            actEdit:      Tafelview.statusEdit,
        }
        self._statusgroup = QActionGroup(self)
        self.configureActionDict(self._statusactions, self._statusgroup, self.statuschange)

        self._deleteAction     = Action(       'delete', 'Löschen', self)
        self._copyAction       = Action(         'copy', 'Kopieren', self)
        undoAction             = Action(         'undo', 'Undo', self)
        redoAction             = Action(         'redo', 'Redo', self)
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

        mmPapierDialog = MmLogDialog()
        mmPapierAction = Action('logpapier', 'mm/log-Papier', self)
        karopapierAction = Action('karopapier', 'kariertes Papier', self)
        linienpapierAction = Action('linienpapier', 'liniertes Papier', self)
        vordruckActions = ActionWidget(self, mmPapierAction, karopapierAction, linienpapierAction)
        vordruckActions.setPopupMode(QToolButton.InstantPopup)

        geodreieckAction.setCheckable(True)
        self._fullscreenAction.setCheckable(True)
        self._darkmodeAction.setCheckable(True)
        self._darkmodeAction.setChecked(isdarkmode)
        
        # Toolbar erzeugen und Actions platzieren
        toolframe = QToolBar()
        self.addToolBar(Qt.BottomToolBarArea, toolframe)

        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        formsTool = ActionWidget(self, actKreis, actQuadrat, actEllipse, actRechteck, actKreisF, actQuadratF, actEllipseF, actRechteckF)

        toolframe.addAction(exitAction)
        toolframe.addWidget(left_spacer)

        toolframe.addAction(self._darkmodeAction)
        toolframe.addAction(self._fullscreenAction)
        toolframe.addSeparator()

        toolframe.addAction(vordruckActions)
        toolframe.addAction(geodreieckAction)
        toolframe.addSeparator()

        toolframe.addAction(actC1)
        toolframe.addAction(actC2)
        toolframe.addAction(actC3)
        toolframe.addAction(actC4)
        toolframe.addSeparator()

        toolframe.addAction(actP1)
        toolframe.addAction(actP2)
        toolframe.addAction(actP3)
        toolframe.addAction(actP4)
        toolframe.addSeparator()

        toolframe.addAction(actFreihand)
        toolframe.addAction(actLinie)
        toolframe.addAction(actPfeil)
        toolframe.addAction(formsTool)
        toolframe.addAction(actRubber)
        toolframe.addAction(actEdit)
        toolframe.addSeparator()

        toolframe.addAction(self._deleteAction)
        toolframe.addAction(self._copyAction)
        toolframe.addSeparator()

        toolframe.addAction(undoAction)
        toolframe.addAction(redoAction)
        toolframe.addSeparator()

        toolframe.addAction(speichernAction)
        toolframe.addAction(ladenAction)
        toolframe.addAction(clipboardPasteAction)
        toolframe.addAction(saveSettingsAction)
        toolframe.addSeparator()

        toolframe.addAction(zoominAction)
        toolframe.addAction(zoomorigAction)
        toolframe.addAction(zoomoutAction)
        toolframe.addSeparator()

        toolframe.addAction(clearAction)
        toolframe.addWidget(right_spacer)
        toolframe.addAction(helpAction)

        # Zu den Signals verbinden
        self._tafelview.eswurdegemalt.connect(self.tafelHatGemalt)
        self._tafelview.statusbarinfo.connect(self.statusbarinfo)

        self._deleteAction.triggered.connect(self.deleteClicked.emit)
        self._copyAction.triggered.connect(self.copyClicked.emit)
        undoAction.triggered.connect(self.undoClicked.emit)
        redoAction.triggered.connect(self.redoClicked.emit)
        speichernAction.triggered.connect(self.speichern)
        ladenAction.triggered.connect(self.laden)
        saveSettingsAction.triggered.connect(self.einstellungenSpeichern)
        zoomoutAction.triggered.connect(self.zoomoutClicked.emit)
        zoomorigAction.triggered.connect(self.zoomresetClicked.emit)
        zoominAction.triggered.connect(self.zoominClicked.emit)
        clearAction.triggered.connect(self.clearall)
        geodreieckAction.triggered.connect(lambda: self.geodreieckClick.emit(geodreieckAction.isChecked()))
        self._fullscreenAction.triggered.connect(lambda: self.fullScreen(self._fullscreenAction.isChecked()))
        exitAction.triggered.connect(self.close)
        helpAction.triggered.connect(self.showHelp)
        self._darkmodeAction.triggered.connect(lambda: QApplication.instance().setPalette(paletteDark if self._darkmodeAction.isChecked() else paletteLight))
        mmPapierAction.triggered.connect(lambda: mmPapierDialog.exec())
        mmPapierDialog.mmPapierCreated.connect(self.newItemCreated.emit)
        karopapierAction.triggered.connect(lambda: self.newItemCreated.emit(Karopapier(self._tafelview)))
        linienpapierAction.triggered.connect(lambda: self.newItemCreated.emit(Linienpapier(self._tafelview)))
        clipboardPasteAction.triggered.connect(self.importClipboard)

        # Trigger den Standard-Status freihand
        actFreihand.trigger()

        # Trigger die Standard-Farbe und Standard Pensize
        colorstr = self._settings.value('editor/colorstr', 'Rot')
        coloraction = [act for act in self._coloractions if act.text() == colorstr]
        if coloraction:
            coloraction.pop().trigger()
        else:
            actC1.trigger()

        pensize = self._settings.value('editor/pensize', '3px')
        pensizeaction = [act for act in self._pensizeactions if act.text() == pensize]
        if pensizeaction:
            pensizeaction.pop().trigger()
        else:
            actP1.trigger()

    def lateInit(self, appstate: Qt.ApplicationState):
        'Einige Dinge können erst nach dem aktivieren des Fenster eingestellt werden (z.B. viewport)'
        if appstate == Qt.ApplicationActive:
            self._fullscreenAction.setChecked(self.isFullScreen())
            self._tafelview.setSceneRectFromViewport()
            QApplication.instance().applicationStateChanged.disconnect()

    def event(self, ev: QEvent):
        if ev.type() == QEvent.ApplicationPaletteChange:
            self.paletteChanged.emit()
        return super().event(ev)

    def tafelHatGemalt(self):
        self.setUngespeichert()
        self.displayMemoryUsage()

    def setUngespeichert(self):
        self._ungespeichert = True

    def displayMemoryUsage(self):
        megabytes = self._process.memory_info().rss/1048576
        anzahl = len(self._tafelview.scene().items())
        self._speicherlabel.setText(f'{anzahl} Elemente, Speichernutzung: {megabytes:10.2f}MB')

    def clearall(self):
        if self.ungespeichertFortfahren('Trotzdem alles löschen'):
            self.clearClicked.emit()
            self._ungespeichert = False

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

    def statuschange(self, status):
        if status in [Tafelview.statusRadiere, Tafelview.statusEdit]:
            self.setActionsDisabled(self._coloractions, True)
        else:
            self.setActionsDisabled(self._coloractions, False)

        if status == Tafelview.statusEdit:
            self.setActionsDisabled([self._deleteAction, self._copyAction], False)
            self.setActionsDisabled(self._pensizeactions, True)
        else:
            self.setActionsDisabled([self._deleteAction, self._copyAction], True)
            self.setActionsDisabled(self._pensizeactions, False)

        self.newstatus.emit(status)

    def statusbarinfo(self, txt, timeout):
        self.statusBar().showMessage(txt,timeout)

    def laden(self):
        filename = QFileDialog.getOpenFileName(self, 'SVG-Datei laden', filter='Alle Dateien (*.*);;SVG-Dateien (*.svg);;Bilder (*.png *.xpm *.bmp *.jpg)')[0]
        if filename:
            if filename[-4:] == '.svg':
                self.newItemCreated.emit(SVGBild(filename))
            else:
                self.newItemCreated.emit(Pixelbild(QPixmap(filename)))

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
        </table>
        <p>Der Start der Anwendung kann mit der Kommandozeilenoption <code>--show [fullscreen,maximized,normal]</code>
        gesetzt werden.</p>'''
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
        tafel = self._tafelview.scene()
        rect = self._tafelview.scene().sceneRect()
        w, h = rect.size().toTuple()
        generator = QSvgGenerator()
        generator.setFileName(filename)
        generator.setSize(QSize(int(w), int(h)))
        generator.setViewBox(rect)
        generator.setTitle('Tafelbild')
        generator.setDescription('Tafelbild')
        generator.setResolution(QGuiApplication.primaryScreen().physicalDotsPerInch())
        painter = QPainter()
        painter.begin(generator)
        if backgroundcolor != QColor(Qt.white):
            painter.fillRect(rect,backgroundcolor)
        tafel.render(painter,rect)
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
            self.newItemCreated.emit(item)
        elif mimeData.hasHtml():
            item = QGraphicsTextItem()
            item.setHtml(mimeData.html())
            item.setFlag(QGraphicsItem.ItemIsMovable, True)
            item.setFlag(QGraphicsItem.ItemIsSelectable, True)            
            self.newItemCreated.emit(item)
        elif mimeData.hasText():
            item = QGraphicsTextItem(mimeData.text())
            item.setFlag(QGraphicsItem.ItemIsMovable, True)
            item.setFlag(QGraphicsItem.ItemIsSelectable, True)            
            self.newItemCreated.emit(item)

    def showHelp(self):
        text = '''<h1>Endlostafel</h1>
            <h3>Autor: Christian Hoffmann</h3>
            <p>Dieses Programm stellt ein einfaches Schreibwerkzeug für den Frontalunterricht dar.</p>
            <h4>Kommandozeilenoptionen</h4>
            <p><code>--show [fullscreen,maximized,normal]</code></p>
            <p>Startet die Tafel in Vollbild, maximiertem Fenster oder Fenster in Normalgröße. Bei
            einem ungültigen Wert, wird maximized angenommen. Ist diese Option nicht gegeben, wird der Wert
            in den Einstellungen angenommen. Ist der Wert in den Einstellungen nicht gesetzt, wird mit
            maximized gestartet.</p>
            <p>Berlin, November 2021</p>'''
        QMessageBox.about(self, 'Über Endlostafel',text)


class Action(QAction):
    def __init__(self, iconname: str, text: str, parent: QWidget, iscolor=False):
        parent.paletteChanged.connect(self.newPalette)
        super().__init__(text, parent)
        self._iconname = iconname
        self._iscolor = iscolor
        self.newPalette()

    def newPalette(self):
        if self._iscolor:
            if self._iconname == 'foreground':
                qcolor = QApplication.instance().palette().color(QPalette.WindowText)
            else:
                qcolor = QColor(self._iconname)
            self.setIcon(getIconColor(qcolor))
        else:
            self.setIcon(getIconSvg(self._iconname))
        if self._iconname == 'foreground' and self._iscolor and self.isChecked():
            self.trigger()


class ActionWidget(QWidgetAction):
    def __init__(self, parent, *actionArray):
        super().__init__(parent)
        menu = QMenu(parent)
        for action in actionArray:
            menu.addAction(action)
        self.button = QToolButton()
        self.button.setPopupMode(QToolButton.MenuButtonPopup)
        self.button.setDefaultAction(actionArray[0])
        self.button.setMenu(menu)
        self.setDefaultWidget(self.button)
        menu.triggered.connect(self.button.setDefaultAction)
    
    def setPopupMode(self, mode):
        self.button.setPopupMode(mode)


class Uhr(QLCDNumber):
    def __init__(self, parent):
        super().__init__(parent)

        self.setSegmentStyle(QLCDNumber.Flat)
        self.setFrameShape(QFrame.NoFrame)

        timer = QTimer(self)
        timer.timeout.connect(self.anzeige)
        timer.start(1000)
        self.anzeige()

    def anzeige(self):
        time = QTime.currentTime()
        text = time.toString('hh:mm')
        if time.second() % 2 == 0:
            text = text[:2]+' '+text[-2:]
        self.display(text)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Digitale Tafel für Physiklehrer und andere. Einfach nur schreiben.')
    parser.add_argument('--show',help='Wie soll die Tafel geöffnet werden (default: maximized)?')
    options=vars(parser.parse_args())

    QLocale.setDefault(QLocale.German)
    app = QApplication()
    app.setStyle('Fusion')
    app.setWindowIcon(getIconSvg('oszli'))
    app.setApplicationDisplayName('Endlostafel')

    settings = QSettings('hoffmann', 'endlostafel')
    if options['show']:
        showmode = options['show']
    else:
        showmode = settings.value('editor/show','maximized')

    d = Editor(settings)
    if showmode == 'normal':
        d.setFixedSize(800,600)
        d.showNormal()
    elif showmode == 'fullscreen':
        d.showFullScreen()
    else:
        d.showMaximized()
    sys.exit(app.exec())

