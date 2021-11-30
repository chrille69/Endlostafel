
from PySide6 import QtCore
from PySide6.QtCore import QEvent, QLineF, QPointF, QRect, QRectF, QSizeF, Qt, Signal, qWarning
from PySide6.QtGui import QBrush, QColor, QPainter, QPalette, QPen, QResizeEvent, QTransform
from PySide6.QtWidgets import QApplication, QGraphicsEllipseItem, QGraphicsScene, QGraphicsView, QMessageBox, QToolButton, QWidget

from icons import getNameCursor, getIconSvg
from items import Ellipse, Kreis, Line, Pfad, Pfeil, Punkt, Quadrat, Rechteck, Stift
from geodreieck import Geodreieck


class Tafelview(QGraphicsView):

    eswurdegemalt = Signal()
    resized = Signal()
    statusbarinfo = Signal(str, int)
    mousemoved = Signal(QPointF)
    mousereleased = Signal()

    statusFreihand  = 'freihand'
    statusLinie     = 'linie'
    statusPfeil     = 'pfeil'
    statusKreis     = 'kreis'
    statusQuadrat   = 'quadrat'
    statusEllipse   = 'ellipse'
    statusRechteck  = 'rechteck'
    statusKreisF    = 'kreisf'
    statusQuadratF  = 'quadratf'
    statusEllipseF  = 'ellipsef'
    statusRechteckF = 'rechteckf'
    statusRadiere   = 'radiere'
    statusEdit      = 'edit'

    statusArray = [
        statusFreihand, statusLinie, statusPfeil,
        statusKreis, statusQuadrat, statusEllipse, statusRechteck,
        statusKreisF, statusQuadratF, statusEllipseF, statusRechteckF,
        statusEdit, statusRadiere
    ]

    def __init__(self, parent: QWidget, qcolor: QColor=QColor(Qt.black), pensize: float=3, status: str=statusFreihand):
        super().__init__(parent)
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents)
        tafel = QGraphicsScene(self)
        self.setScene(tafel)
        self.setBackgroundBrush(QColor(Qt.transparent))
        self._currentItem: Pfad = None
        self._redoitems = []
        self._lastPos: QPointF = None
        self._status = status
        self._dreheGeo: bool = None
        self._verschiebeGeo: bool = None
        self._drawpen = QPen(qcolor, pensize, Qt.SolidLine, c=Qt.RoundCap, j=Qt.RoundJoin)
        self._drawpen.setCosmetic(True)
        self._radiererpen = QPen(Qt.white, 6, Qt.SolidLine, c=Qt.RoundCap, j=Qt.RoundJoin)
        self._radiererpen.setCosmetic(True)
        self._drawbrush = Qt.NoBrush
        self._arrowbrush = QBrush(QColor(qcolor))
        self._arrowpen = QPen(self._drawpen)
        self._arrowpen.setJoinStyle(Qt.MiterJoin)
        self._currentpen: QPen = None
        self._currentbrush: QBrush = None
        self._totalTransform = self.transform()
        self._fgcolor = QApplication.instance().palette().color(QPalette.WindowText)
        self._bgcolor = QApplication.instance().palette().color(QPalette.Base)
        self._ereaser = None

        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)

        self._status2cursor = self.initCursor()

        parent.newstatus.connect(self.setStatus)
        parent.pencolorChanged.connect(self.setPencolor)
        parent.pensizeChanged.connect(self.setPensize)
        parent.deleteClicked.connect(self.deleteItems)
        parent.copyClicked.connect(self.copyItems)
        parent.undoClicked.connect(self.undo)
        parent.redoClicked.connect(self.redo)
        parent.zoominClicked.connect(self.zoomin)
        parent.zoomresetClicked.connect(self.zoomreset)
        parent.zoomoutClicked.connect(self.zoomout)
        parent.newItemCreated.connect(self.importItem)
        parent.clearClicked.connect(self.clearall)
        parent.paletteChanged.connect(self.newPalette)

        self.resized.connect(self.changeSceneRect)
        
        btn_bottom = erweiternButton('bottom', self)
        btn_bottom.setFixedWidth(200)
        btn_bottom.setFixedHeight(20)
        btn_bottom.erweitert.connect(self.erweitern)
        self.resized.connect(btn_bottom.moveToSide)

        btn_top = erweiternButton('top', self)
        btn_top.setFixedWidth(200)
        btn_top.setFixedHeight(20)
        btn_top.erweitert.connect(self.erweitern)
        self.resized.connect(btn_top.moveToSide)

        btn_left = erweiternButton('left', self)
        btn_left.setFixedWidth(20)
        btn_left.setFixedHeight(200)
        btn_left.erweitert.connect(self.erweitern)
        self.resized.connect(btn_left.moveToSide)

        btn_right = erweiternButton('right', self)
        btn_right.setFixedWidth(20)
        btn_right.setFixedHeight(200)
        btn_right.erweitert.connect(self.erweitern)
        self.resized.connect(btn_right.moveToSide)

        self._geodreieck = Geodreieck(self)
        self._drehgriff = self._geodreieck.drehgriff()
        self._schiebegriff = self._geodreieck.schiebegriff()
        self.centerGeodreieck()
        parent.geodreieckClick.connect(self.enableGeodreieck)
    
    def fgcolor(self):
        return self._fgcolor

    def bgcolor(self):
        return self._bgcolor

    def newPalette(self):
        self._status2cursor = self.initCursor()
        self.setCustomCursor()
        self._fgcolor = QApplication.instance().palette().color(QPalette.WindowText)
        self._bgcolor = QApplication.instance().palette().color(QPalette.Base)
        self.setRadiererColor()

    def setRadiererColor(self):
        self._radiererpen.setColor(self._bgcolor)

    def setPencolor(self, colorname):
        if colorname == 'foreground':
            qcolor = self._fgcolor
        else:
            qcolor = QColor(colorname)
        self._drawpen.setColor(qcolor)
        self._arrowpen.setColor(qcolor)
        self._arrowbrush.setColor(qcolor)

    def setPensize(self, pensize):
        self._drawpen.setWidthF(pensize)
        self._arrowpen.setWidthF(pensize)
        self._radiererpen.setWidthF(10*pensize)
        self.setCustomCursor()

    def centerGeodreieck(self):
        center = self.mapToScene(self.viewport().rect().center() );
        self._geodreieck.setPos(center-self._geodreieck.transformOriginPoint())

    def initCursor(self):
        return {
            Tafelview.statusFreihand : getNameCursor(    'stift'),
            Tafelview.statusLinie    : getNameCursor(    'linie'),
            Tafelview.statusPfeil    : getNameCursor(    'pfeil'),
            Tafelview.statusQuadrat  : getNameCursor(  'quadrat'),
            Tafelview.statusKreis    : getNameCursor(    'kreis'),
            Tafelview.statusRechteck : getNameCursor( 'rechteck'),
            Tafelview.statusEllipse  : getNameCursor(  'ellipse'),
            Tafelview.statusQuadratF : getNameCursor( 'quadratf'),
            Tafelview.statusKreisF   : getNameCursor(   'kreisf'),
            Tafelview.statusRechteckF: getNameCursor('rechteckf'),
            Tafelview.statusEllipseF : getNameCursor( 'ellipsef'),
            Tafelview.statusRadiere  : getNameCursor( 'erease-noborder'),
            Tafelview.statusEdit     : getNameCursor(     'edit')
        }

    def setCustomCursor(self):
        if self._status == Tafelview.statusRadiere:
            cursor = getNameCursor( 'erease-noborder',self._currentpen.widthF() if self._currentpen else 32)
        else:
            cursor = self._status2cursor[self._status]
        self.setCursor(cursor)

    def setStatus(self, status):
        if status not in self.statusArray:
            raise ValueError(f'Unbekannter Status: {status}')

        self._status = status
        self._dreheGeo = False
        self._verschiebeGeo = False

       # Edit-Modus der Items setzen
        if status == self.statusEdit:
            # self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
        
        # Stift und Pinsel dem Status anpassen
        if status in [self.statusFreihand, self.statusLinie, self.statusKreis, self.statusQuadrat, self.statusEllipse, self.statusRechteck]:
            self._currentpen = self._drawpen
            self._currentbrush = Qt.NoBrush
        elif status in [self.statusKreisF, self.statusQuadratF, self.statusEllipseF, self.statusRechteckF]:
            self._currentpen = Qt.NoPen
            self._currentbrush = self._arrowbrush
        elif status == self.statusPfeil:
            self._currentpen = self._arrowpen
            self._currentbrush = self._arrowbrush
        elif status == self.statusRadiere:
            self._currentpen = self._radiererpen
            self._currentbrush = Qt.NoBrush
        else:
            self._currentpen = Qt.NoPen
            self._currentbrush = Qt.NoBrush
        self.setCustomCursor()

    def setLastPos(self, pos):
        self._lastPos = pos

    def createCurrentItem(self, pos):
        if self._status == Tafelview.statusFreihand:
            item = Stift(self, pos, self._currentpen, self._currentbrush)
        elif self._status == Tafelview.statusLinie:
            item = Line(self, pos, self._currentpen, self._currentbrush)
        elif self._status == Tafelview.statusPfeil:
            item = Pfeil(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusKreis, Tafelview.statusKreisF]:
            item = Kreis(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusEllipse, Tafelview.statusEllipseF]:
            item = Ellipse(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusQuadrat, Tafelview.statusQuadratF]:
            item = Quadrat(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusRechteck, Tafelview.statusRechteckF]:
            item = Rechteck(self, pos, self._currentpen, self._currentbrush)
        else:
            raise Exception(f'Für den Status "{self._status}" gibt es kein Item.')

        if item:
            self.scene().addItem(item)
        self._currentItem = item

    def scenePosFromEvent(self, event):
        if event.type() in [QEvent.TouchBegin,QEvent.TouchUpdate,QEvent.TouchEnd]:
            tp = event.points().pop()
            pos = self.mapToScene(tp.pos().x(), tp.pos().y())
        elif event.type() in [QEvent.MouseButtonPress,QEvent.MouseMove,QEvent.MouseButtonRelease]:
            pos = self.mapToScene(event.pos())
        else:
            raise Exception('Keine Position gefunden!')
        return pos

    def viewportEvent(self, event: QtCore.QEvent) -> bool:

        if event.type() in [QEvent.TouchBegin, QEvent.MouseButtonPress]:
            qWarning('Event '+str(event.type()))

            pos = self.scenePosFromEvent(event)
            qWarning('pos '+str(pos))

            self._totalTransform = self.transform()
            self._verschiebeGeo = self._geodreieck.posInVerschiebegriff(pos)
            self._dreheGeo = self._geodreieck.posInDrehgriff(pos)
            if self._status in [Tafelview.statusEdit, Tafelview.statusRadiere]:
                return super().viewportEvent(event)
            
            qWarning('item '+str(self._currentItem))
            if not self._verschiebeGeo and not self._dreheGeo:
                pos = self.snapToGeodreieck(pos)
                self.setLastPos(pos)
                self.createCurrentItem(pos)
            return True

        elif event.type() in [QEvent.TouchUpdate, QEvent.MouseMove]:
            qWarning('Event '+str(event.type()))

            pos = self.scenePosFromEvent(event)
            qWarning('pos '+str(pos))

            if event.type() == QEvent.TouchUpdate:
                touchpoints = event.points()
                if len(touchpoints) == 2:
                    if self._currentItem:
                        self.scene().removeItem(self._currentItem)
                        self._currentItem = None
                    tp0 = touchpoints.pop()
                    tp1 = touchpoints.pop()
                    startLine = QLineF(tp0.pos(), tp1.pos())
                    line = QLineF(tp0.startPos(),tp1.startPos())
                    faktor = startLine.length()/line.length()
                    transform = QTransform(self._totalTransform)
                    transform.scale(faktor,faktor)
                    self.setTransform(transform)
                    return True
            elif event.type() == QEvent.MouseMove:
                if event.buttons() == Qt.NoButton:
                    return super().viewportEvent(event)
            
            if self._dreheGeo:
                self._geodreieck.drehe(pos)
                return True
            if self._verschiebeGeo:
                self._geodreieck.verschiebe(pos)
                return True
            if self._status == self.statusEdit:
                return super().viewportEvent(event)
            if self._status == Tafelview.statusRadiere:
                durchmesser = self._radiererpen.widthF()/self.transform().m11()
                ellipse = QGraphicsEllipseItem(QRectF(pos-QPointF(durchmesser/2,durchmesser/2),QSizeF(durchmesser,durchmesser)))
                for item in self.scene().items(ellipse.shape()):
                    if hasattr(item,'removeElements') and callable(item.removeElements):
                        item.removeElements(ellipse)
                    if item.path().elementCount() < 2:
                        self.scene().removeItem(item)
                return True

            qWarning('item '+str(self._currentItem))
            pos = self.snapToGeodreieck(pos)
            if not self._currentItem:
                self.createCurrentItem(pos)
            self.mousemoved.emit(pos)
            return True
                
        elif event.type() in [QEvent.TouchEnd, QEvent.MouseButtonRelease]:
            qWarning('Event '+str(event.type()))
            qWarning('item '+str(self._currentItem))

            self._verschiebeGeo = False
            self._dreheGeo = False

            if self._status == self.statusEdit:
                return super().viewportEvent(event)

            pos = self.scenePosFromEvent(event)
            qWarning('pos '+str(pos))
            pos = self.snapToGeodreieck(pos)
            if pos == self._lastPos:   # MouseClick
                if self._status == Tafelview.statusFreihand:
                    item = Punkt(self,pos,self._currentpen,self._currentbrush)
                    self.scene().addItem(item)

            self._currentItem = None
            self._redoitems = []
            self.mousereleased.emit()
            self.eswurdegemalt.emit()

            return True
        
        return super().viewportEvent(event)

    def snapToGeodreieck(self, pos):
        if self._geodreieck.scene() != self.scene():
            return pos
        posGeo = self._geodreieck.mapFromScene(pos)
        if posGeo.x() < 0 or posGeo.x() > 160:
            return pos
        if abs(posGeo.y()) < 10:
            posGeo.setY(0)
        return self._geodreieck.mapToScene(posGeo)
    
    def deleteItems(self):
        if not self.scene().selectedItems():
            QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
            return
        for item in self.scene().selectedItems():
            if item == self._geodreieck:
                continue
            self._redoitems.append(item)
            self.scene().removeItem(item)
        self.eswurdegemalt.emit()

    def copyItems(self):
        if not self.scene().selectedItems():
            QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
            return

        funktioniert_nicht = False
        for item in self.scene().selectedItems():
            try:
                newitem = item.clone()
            except AttributeError:
                self.statusbarinfo.emit('Einige Elemente konnten nicht kopiert werden',1000) # funktioniert nicht
                funktioniert_nicht = True
                continue
            self.scene().addItem(newitem)
            newitem.stackBefore(item)
        self.eswurdegemalt.emit()
        if not funktioniert_nicht:
            self.statusbarinfo.emit('Die Elemente sind kopiert. Bitte jetzt verschieben...',5000)

    def erweitern(self, richtung):
        _, _, wv, hv = self.viewport().rect().getRect()
        xs, ys, ws, hs = self.sceneRect().getRect()
        dh = hv*0.4
        dw = wv*0.4
        if richtung == 'bottom':
            self.setSceneRect(xs, ys, ws, hs+dh)
            self.scene().setSceneRect(xs, ys, ws, hs+dh)
            self.verticalScrollBar().setValue(hs+dh)
        elif richtung == 'top':
            self.setSceneRect(xs, ys-dh, ws, hs+dh)
            self.scene().setSceneRect(xs, ys-dh, ws, hs+dh)
            self.verticalScrollBar().setValue(ys-dh)
        elif richtung == 'left':
            self.setSceneRect(xs-dw, ys, ws+dw, hs)
            self.scene().setSceneRect(xs-dw, ys, ws+dw, hs)
            self.horizontalScrollBar().setValue(xs-dw)
        elif richtung == 'right':
            self.setSceneRect(xs, ys, ws+dw, hs)
            self.scene().setSceneRect(xs, ys, ws+dw, hs)
            self.horizontalScrollBar().setValue(ws+dw)

    def importItem(self, item):
        self.scene().addItem(item)
        item.setPos(self.mapToScene(self.viewport().rect().topLeft()))

        self.berechneSceneRectNeu(item)

        self.statusbarinfo.emit('Das Element wurde in der Mitte eingefügt. Bitte jetzt verschieben...',5000)
        self.eswurdegemalt.emit()

    def berechneSceneRectNeu(self, item):
        # Mögliche Erweiterung des sceneRect berechnen
        rect = item.mapToScene(item.boundingRect()).boundingRect()
        rect |= self.sceneRect()
        self.setSceneRect(rect)
        self.scene().setSceneRect(rect)

    def undo(self):
        items = self.scene().items()
        for item in items:
            if item in [self._geodreieck,self._drehgriff, self._schiebegriff]:
                continue
            self._redoitems.append(item)
            self.scene().removeItem(item)
            break
        self.eswurdegemalt.emit()

    def redo(self):
        if self._redoitems:
            item = self._redoitems.pop()
            self.scene().addItem(item)
        self.eswurdegemalt.emit()

    def zoomin(self):
        if self._status == self.statusEdit:
            if not self.scene().selectedItems():
                QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
                return
            for item in self.scene().selectedItems():
                s = item.scale()
                item.setScale(1.1*s)
                self.berechneSceneRectNeu(item)
        else:
            self.scale(1.1,1.1)

    def zoomout(self):
        if self._status == self.statusEdit:
            if not self.scene().selectedItems():
                QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
                return
            for item in self.scene().selectedItems():
                s = item.scale()
                item.setScale(s/1.1)
                self.berechneSceneRectNeu(item)
        else:
            self.scale(1/1.1,1/1.1)

    def zoomreset(self):
        if self._status == self.statusEdit:
            if not self.scene().selectedItems():
                QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
                return
            for item in self.scene().selectedItems():
                item.setScale(1)
                self.berechneSceneRectNeu(item)
        else:
            self.setTransform(QTransform())

    def clearall(self):
        geodreiecksichtbar = False
        if self._geodreieck.scene():
            geodreiecksichtbar = True
            self.scene().removeItem(self._geodreieck)
        self.scene().clear()
        if geodreiecksichtbar:
            self.scene().addItem(self._geodreieck)
        self.eswurdegemalt.emit()

    def resizeEvent(self, event: QResizeEvent):
        self.resized.emit()
        return super().resizeEvent(event)

    def setSceneRectFromViewport(self):
        r = QRect(self.viewport().rect())
        r.setWidth(r.width()-20)
        self.scene().setSceneRect(r)
        self.centerGeodreieck()

    def changeSceneRect(self):
        r = self.sceneRect()
        self.scene().setSceneRect(r)

    def enableGeodreieck(self, enable):
        if enable:
            self.scene().addItem(self._geodreieck)
            self._geodreieck.setPos(self.mapToScene(self.viewport().rect().center()))
        else:
            self.scene().removeItem(self._geodreieck)



class erweiternButton(QToolButton):

    erweitert = Signal(str)

    def __init__(self, richtung: str, parent: QWidget):
        super().__init__(parent)
        self._richtung = richtung
        self.setIcon(getIconSvg('go-'+richtung))
        self.setToolTip('Seite erweitern')
        self.clicked.connect(lambda: self.erweitert.emit(self._richtung))
        self.setCursor(Qt.ArrowCursor)
        parent.parent().paletteChanged.connect(self.newPalette)

    def newPalette(self):
        self.setIcon(getIconSvg('go-'+self._richtung))

    def moveToSide(self):
        parent = self.parentWidget()
        _, _, w, h = parent.viewport().rect().getRect()
        if self._richtung == 'bottom':
            self.move((w-self.width())/2, h-25)
        elif self._richtung == 'top':
            self.move((w-self.width())/2, 5)
        elif self._richtung == 'left':
            self.move(5, (h-self.height())/2)
        elif self._richtung == 'right':
            self.move(w-25, (h-self.height())/2)

