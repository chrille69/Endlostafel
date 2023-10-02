
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

import logging
from PySide6 import QtCore
from PySide6.QtCore import QEvent, QPointF, QRect, QSizeF, Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QPainter, QPalette, QPen, QResizeEvent
from PySide6.QtWidgets import QApplication, QGraphicsRectItem, QGraphicsItem, QGraphicsScene, QGraphicsView, QMessageBox, QToolButton, QWidget, QPinchGesture

from icons import SVGCursor, SVGIcon, ItemCursor
from items import Ellipse, Kreis, Line, LineSnap, Pfad, Pfeil, PfeilSnap, Punkt, Quadrat, Rechteck, Stift
from geodreieck import Geodreieck
from radiergummi import Radiergummi
from undo import AddItem, RemoveItem, ChangePathItems, MoveItem

logger = logging.getLogger('GUI')

class Tafelview(QGraphicsView):

    eswurdegemalt = Signal()
    resized = Signal()
    statusbarinfo = Signal(str, int)
    mousemoved = Signal(QPointF)
    mousereleased = Signal()
    finishedEdit = Signal(QWidget)
    kalibriert = Signal(float)

    statusFreihand  = 'freihand'
    statusLinie     = 'linie'
    statusLinieS    = 'linies'
    statusPfeil     = 'pfeil'
    statusPfeilS    = 'pfeils'
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
        statusFreihand, statusLinie, statusPfeil, statusLinieS, statusPfeilS,
        statusKreis, statusQuadrat, statusEllipse, statusRechteck,
        statusKreisF, statusQuadratF, statusEllipseF, statusRechteckF,
        statusEdit, statusRadiere
    ]

    RADIERGUMMISIZESMALL = QSizeF(30, 60)
    RADIERGUMMISIZEBIG   = QSizeF(90, 180)

    def __init__(self, parent: QWidget, qcolor: QColor=QColor(Qt.black), pensize: float=3, status: str=statusFreihand):
        super().__init__(parent)
        self._status = status
        self._tmpStatus = None
        self._painting = False
        self._dreheGeo: bool = None
        self._verschiebeGeo: bool = None
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.viewport().grabGesture(Qt.PinchGesture)
        tafel = QGraphicsScene(self)
        self.setScene(tafel)
        self.setBackgroundBrush(QColor(Qt.transparent))
        self._currentItem: Pfad = None
        self._lastPos: QPointF = None
        self._drawpen = QPen(qcolor, pensize, Qt.SolidLine, c=Qt.RoundCap, j=Qt.RoundJoin)
        self._drawpen.setCosmetic(True)
        self._drawbrush = Qt.NoBrush
        self._arrowbrush = QBrush(QColor(qcolor))
        self._arrowpen = QPen(self._drawpen)
        self._arrowpen.setJoinStyle(Qt.MiterJoin)
        self._radiersize = QSizeF(pensize*5, pensize*10)
        self._radiergummi = Radiergummi(self, self._radiersize/self.transform().m11(), QPointF(0,0))
        self._currentpen: QPen = None
        self._currentbrush: QBrush = None
        self._totalTransform = self.transform()
        self._fgcolor = QApplication.instance().palette().color(QPalette.WindowText)
        self._kalibriere = False
        self._mittlerePointsize = parent.getKalibriert()
        self._countPointsize = 50
        self._bigpointfactor = parent.getBigPointFactor()
        self._verybigpointfactor = parent.getVeryBigPointFactor()
        self._clonedItems = {}

        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)

        self._status2cursor = self.initCursor()

        parent.newstatus.connect(self.setStatus)
        parent.pencolorChanged.connect(self.setPencolor)
        parent.pensizeChanged.connect(self.setPensize)
        parent.deleteClicked.connect(self.deleteItems)
        parent.copyClicked.connect(self.copyItems)
        parent.zoominClicked.connect(self.zoomin)
        parent.zoomresetClicked.connect(self.zoomreset)
        parent.zoomoutClicked.connect(self.zoomout)
        parent.newItemCreated.connect(self.importItem)
        parent.clearClicked.connect(self.clearall)
        parent.paletteChanged.connect(self.newPalette)
        parent.kalibrierenClicked.connect(self.starteKalibrieren)

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

    @Slot()
    def newPalette(self):
        self._status2cursor = self.initCursor()
        self.setCustomCursor()
        self._fgcolor = QApplication.instance().palette().color(QPalette.WindowText)

    @Slot(str)
    def setPencolor(self, colorname: str):
        if colorname == 'foreground':
            qcolor = self._fgcolor
        else:
            qcolor = QColor(colorname)
        self._drawpen.setColor(qcolor)
        self._arrowpen.setColor(qcolor)
        self._arrowbrush.setColor(qcolor)

    @Slot(float)
    def setPensize(self, pensize: float):
        self._drawpen.setWidthF(pensize)
        self._arrowpen.setWidthF(pensize)
        self._radiersize = QSizeF(pensize*5, pensize*10)
        self._radiergummi = Radiergummi(self, self._radiersize/self.transform().m11(), QPointF(0,0))
        self.setCustomCursor()

    def centerGeodreieck(self):
        center = self.mapToScene(self.viewport().rect().center() );
        self._geodreieck.setPos(center-self._geodreieck.transformOriginPoint())

    def initCursor(self):
        return {
            Tafelview.statusFreihand : SVGCursor(    'stift'),
            Tafelview.statusLinie    : SVGCursor(    'linie'),
            Tafelview.statusPfeil    : SVGCursor(    'pfeil'),
            Tafelview.statusLinieS   : SVGCursor(    'linie'),
            Tafelview.statusPfeilS   : SVGCursor(    'pfeil'),
            Tafelview.statusQuadrat  : SVGCursor(  'quadrat'),
            Tafelview.statusKreis    : SVGCursor(    'kreis'),
            Tafelview.statusRechteck : SVGCursor( 'rechteck'),
            Tafelview.statusEllipse  : SVGCursor(  'ellipse'),
            Tafelview.statusQuadratF : SVGCursor( 'quadratf'),
            Tafelview.statusKreisF   : SVGCursor(   'kreisf'),
            Tafelview.statusRechteckF: SVGCursor('rechteckf'),
            Tafelview.statusEllipseF : SVGCursor( 'ellipsef'),
            Tafelview.statusEdit     : SVGCursor(     'edit')
        }

    def setCustomCursor(self):
        if self._status == Tafelview.statusRadiere:
            cursor = ItemCursor(self._radiergummi, self.transform().m11(), -1, -1)
        else:
            cursor = self._status2cursor[self._status]
        self.viewport().setCursor(cursor)

    @Slot(str)
    def setStatus(self, status):
        if status not in self.statusArray:
            raise ValueError(f'Unbekannter Status: {status}')

        if self._status == Tafelview.statusEdit and status != Tafelview.statusEdit:
            for item in self.scene().items():
                item.setSelected(False)

        self._status = status
        self._painting = False
        self._dreheGeo = False
        self._verschiebeGeo = False
        
        # Stift und Pinsel dem Status anpassen
        if status in [self.statusFreihand, self.statusLinie, self.statusLinieS, self.statusKreis, self.statusQuadrat, self.statusEllipse, self.statusRechteck]:
            self._currentpen = self._drawpen
            self._currentbrush = Qt.NoBrush
        elif status in [self.statusKreisF, self.statusQuadratF, self.statusEllipseF, self.statusRechteckF]:
            self._currentpen = Qt.NoPen
            self._currentbrush = self._arrowbrush
        elif status in [self.statusPfeil, self.statusPfeilS]:
            self._currentpen = self._arrowpen
            self._currentbrush = self._arrowbrush
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
        elif self._status == Tafelview.statusLinieS:
            item = LineSnap(self, pos, self._currentpen, self._currentbrush)
        elif self._status == Tafelview.statusPfeilS:
            item = PfeilSnap(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusKreis, Tafelview.statusKreisF]:
            item = Kreis(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusEllipse, Tafelview.statusEllipseF]:
            item = Ellipse(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusQuadrat, Tafelview.statusQuadratF]:
            item = Quadrat(self, pos, self._currentpen, self._currentbrush)
        elif self._status in [Tafelview.statusRechteck, Tafelview.statusRechteckF]:
            item = Rechteck(self, pos, self._currentpen, self._currentbrush)
        elif self._status == Tafelview.statusRadiere:
            item = None
        else:
            raise Exception(f'Für den Status "{self._status}" gibt es kein Item.')

        if item:
            self.parent().undostack.push(AddItem(self.scene(), item))
        self._currentItem = item

    def deleteCurrentItem(self):
        try:
            self.scene().removeItem(self._currentItem)
            self._currentItem = None
        except Exception as e:
            logger.exception(e, exc_info=True)

    def scenePosFromEvent(self, event):
        tp = event.points().pop()
        pos = self.mapToScene(tp.pos().x(), tp.pos().y())
        return pos

    def bearbeitenStart(self,pos) -> bool:
        self._verschiebeGeo = self._geodreieck.posInVerschiebegriff(pos)
        self._dreheGeo = self._geodreieck.posInDrehgriff(pos)
        
        if not self._verschiebeGeo and not self._dreheGeo:
            pos = self.snapToGeodreieck(pos)
            self.setLastPos(pos)
            self.createCurrentItem(pos)
            self._painting = True

    def bearbeitenWeiter(self, pos) -> bool:
        if not self._painting:
            self._verschiebeGeo = self._geodreieck.posInVerschiebegriff(pos)
            self._dreheGeo = self._geodreieck.posInDrehgriff(pos)

        if self._dreheGeo:
            self._geodreieck.drehe(pos)
            self._painting = True
            return
        if self._verschiebeGeo:
            self._geodreieck.verschiebe(pos)
            self._painting = True
            return
        if self._status == Tafelview.statusRadiere:
            self._painting = True
            self.radiere(pos)
            return

        geopos = self.snapToGeodreieck(pos)
        if not self._painting:
            self.createCurrentItem(geopos)
            self._painting = True
        self.mousemoved.emit(geopos)
    
    def bearbeitenFertig(self,pos) -> bool:
        self._verschiebeGeo = False
        self._dreheGeo = False
        self._currentItem = None
        if pos:
            geopos = self.snapToGeodreieck(pos)
            if geopos == self._lastPos or not self._painting:   # MouseClick
                if self._status == Tafelview.statusFreihand:
                    item = Punkt(self,geopos,self._currentpen,self._currentbrush)
                    self.parent().undostack.undo()
                    self.parent().undostack.push(AddItem(self.scene(), item))
                elif self._status == Tafelview.statusRadiere:
                    self.radiere(geopos)
        if self._clonedItems:
            self.parent().undostack.push(ChangePathItems({k: self._clonedItems[k] for k in self._clonedItems}))
        self._clonedItems = {}
        self._painting = False
        self.setLastPos(None)
        self.mousereleased.emit()
        self.eswurdegemalt.emit()

    def touchPointSize(self, point):
        ellipse = point.ellipseDiameters()
        area = ellipse.height()**2 + ellipse.width()**2
        #logger.info(f"Pointsize: {ellipse}, Fläche={area}")
        return area
    
    def isBigPoint(self, pointsize) -> True:
        return pointsize > self._mittlerePointsize * self._bigpointfactor and not self._kalibriere

    def isVeryBigPoint(self, pointsize) -> True:
        return pointsize > self._mittlerePointsize * self._verybigpointfactor and not self._kalibriere

    def getPointSizeList(self, event):
        return [self.touchPointSize(point) for point in event.points()]

    def verschiebeLeinwand(self, point: QPointF, lastpoint: QPointF):
        scpoint = self.mapToScene(point.toPoint())
        sclastpoint = self.mapToScene(lastpoint.toPoint())
        dpoint = scpoint -sclastpoint
        rectvor = self.mapToScene(self.viewport().geometry()).boundingRect()
        self.translate(dpoint.x(), dpoint.y())
        rectnach = self.mapToScene(self.viewport().geometry()).boundingRect()
        if rectvor.x() == rectnach.x() and dpoint.x() != 0 or rectvor.y() == rectnach.y() and dpoint.y() != 0:
            logger.debug(f"dpoint={dpoint}")
            if dpoint.x() > 0:
                self.erweitern('left', self.mapFromParent(dpoint).x())
            if dpoint.x() < 0:
                self.erweitern('right', -self.mapFromParent(dpoint).x())
            if dpoint.y() > 0:
                self.erweitern('top', self.mapFromParent(dpoint).y())
            if dpoint.y() < 0:
                self.erweitern('bottom', -self.mapFromParent(dpoint).y())

    def aktiviereRadiergummi(self, pointsize, pos):
        self._tmpStatus = self._status
        size = Tafelview.RADIERGUMMISIZESMALL
        if self.isVeryBigPoint(pointsize):
            size = Tafelview.RADIERGUMMISIZEBIG
        self._radiergummi = Radiergummi(self, size/self.transform().m11(), pos)
        self.scene().addItem(self._radiergummi)
        self.setStatus(Tafelview.statusRadiere)

    def resizeRadiergummi(self, pointsize):
        if self._radiergummi.size() == Tafelview.RADIERGUMMISIZEBIG:
            return
        size = Tafelview.RADIERGUMMISIZESMALL
        if self.isVeryBigPoint(pointsize):
            size = Tafelview.RADIERGUMMISIZEBIG
        self._radiergummi.setSize(size/self.transform().m11())
    
    def deaktiviereRadiergummi(self):
        self.setStatus(self._tmpStatus)
        self._tmpStatus = None
        self.scene().removeItem(self._radiergummi)
        self._radiergummi = Radiergummi(self, self._radiersize/self.transform().m11(), QPointF(0,0))

    def viewportEvent(self, event: QtCore.QEvent) -> bool:
        #if logger.isEnabledFor(logging.DEBUG):
        #    logger.debug(str(event.type()))
        #    logger.debug(f"Status: {self._status}, Painting: {self._painting}")

        try:
            eventtype = event.type()

            if self._status == Tafelview.statusEdit:
                if eventtype in [QEvent.TouchCancel,QEvent.TouchEnd,QEvent.MouseButtonRelease]:
                    self.finishedEdit.emit(self.parent())
                    self.parent().undostack.push(MoveItem(None, QPointF(), QPointF()))
                return super().viewportEvent(event)

            if eventtype == QEvent.Gesture:
                gesture = event.gesture(Qt.PinchGesture)
                if gesture and not self._tmpStatus:
                    if gesture.state() == Qt.GestureUpdated and gesture.changeFlags() | QPinchGesture.CenterPointChanged:
                        self.verschiebeLeinwand(gesture.centerPoint(), gesture.lastCenterPoint())
                return True

            elif eventtype == QEvent.TouchBegin:
                maxPointSize = max(self.getPointSizeList(event))
                if self.isBigPoint(maxPointSize):
                    if not self._tmpStatus:
                        self.aktiviereRadiergummi(maxPointSize, self.scenePosFromEvent(event))
                self.bearbeitenStart(self.scenePosFromEvent(event))
                return True

            elif eventtype == QEvent.TouchUpdate:
                if event.pointCount() > 1:
                    self.deleteCurrentItem()
                maxPointSize = max(self.getPointSizeList(event))
                #logger.debug(event.points())
                self.kalibrierePointSize(maxPointSize)
                if self.isBigPoint(maxPointSize):
                    if not self._tmpStatus:
                        self.aktiviereRadiergummi(maxPointSize, self.scenePosFromEvent(event))
                    self.resizeRadiergummi(maxPointSize)
                self.bearbeitenWeiter(self.scenePosFromEvent(event))
                return True

            elif eventtype in [QEvent.TouchCancel,QEvent.TouchEnd]:
                self.bearbeitenFertig(self.scenePosFromEvent(event))
                if self._tmpStatus:
                    self.deaktiviereRadiergummi()
                return True

            elif eventtype == QEvent.MouseButtonPress:
                if event.source() == Qt.MouseEventSynthesizedBySystem:
                    return False
                self.bearbeitenStart(self.scenePosFromEvent(event))
                return True

            elif eventtype == QEvent.MouseMove:
                if event.source() == Qt.MouseEventSynthesizedBySystem:
                    return False
                if event.buttons() == Qt.NoButton:
                    return True
                self.bearbeitenWeiter(self.scenePosFromEvent(event))
                return True

            elif eventtype == QEvent.MouseButtonRelease:
                if event.source() == Qt.MouseEventSynthesizedBySystem:
                    return False
                self.bearbeitenFertig(self.scenePosFromEvent(event))
                return True

            elif eventtype == QEvent.MouseButtonDblClick:
                return False

            elif eventtype == QEvent.ContextMenu:
                return False

            return super().viewportEvent(event)
        
        except Exception as e:
            logger.exception(e, exc_info=True)

    def resizeEvent(self, event: QResizeEvent):
        self.resized.emit()
        return super().resizeEvent(event)

    def kalibrierePointSize(self, pointsize):
        if self._kalibriere:
            if self._countPointsize < 50:
                self._mittlerePointsize = (self._countPointsize * self._mittlerePointsize + pointsize) / (self._countPointsize+1)
                self._countPointsize += 1
                logger.debug(f"Kalibrieren: {self._mittlerePointsize}")
            else:
                self._kalibriere = False
                self.kalibriert.emit(self._mittlerePointsize)


    def snapToGeodreieck(self, pos):
        if self._geodreieck.scene() != self.scene():
            return pos
        posGeo = self._geodreieck.mapFromScene(pos)
        if posGeo.x() < 0 or posGeo.x() > 160:
            return pos
        if abs(posGeo.y()) < 10:
            posGeo.setY(0)
        return self._geodreieck.mapToScene(posGeo)
    
    def radiere(self, pos):
        self._radiergummi.setPos(pos)
        radierpath = QGraphicsRectItem(self._radiergummi.sceneBoundingRect()).shape()
        for item in self.scene().items(radierpath):
            if hasattr(item,'removeElements') and callable(item.removeElements):
                if item not in self._clonedItems:
                    self._clonedItems[item] = item.clone()
                item.removeElements(radierpath)
            if hasattr(item,'path') and callable(item.path) and item.path().elementCount() < 2:
                self.parent().undostack.push(RemoveItem(self.scene(), item))

    def berechneSceneRectNeu(self, item: QGraphicsItem):
        # Mögliche Erweiterung des sceneRect berechnen
        rect = item.sceneBoundingRect()
        rect |= self.sceneRect()
        self.setSceneRect(rect)

    def setSceneRectFromViewport(self):
        r = QRect(self.viewport().rect())
        r.setWidth(r.width()-20)
        self.scene().setSceneRect(r)
        self.centerGeodreieck()

    def scale(self, sx: float, sy: float):
        super().scale(sx, sy)
        self._radiergummi = Radiergummi(self, self._radiersize/self.transform().m11(), QPointF(0,0))
        self.setCustomCursor()

    def resetTransform(self):
        super().resetTransform()
        self._radiergummi = Radiergummi(self, self._radiersize/self.transform().m11(), QPointF(0,0))
        self.setCustomCursor()

    @Slot()
    def starteKalibrieren(self):
        logger.debug('Kalibriere')
        self._kalibriere = True
        self._countPointsize = 0
        self._mittlerePointsize = 0
    
    @Slot()
    def deleteItems(self):
        if not self.scene().selectedItems():
            QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
            return
        for item in self.scene().selectedItems():
            if item == self._geodreieck:
                continue
            self.parent().undostack.push(RemoveItem(self.scene(),item))
        self.eswurdegemalt.emit()

    @Slot()
    def copyItems(self):
        if not self.scene().selectedItems():
            QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
            return

        self.parent().undostack.beginMacro('Kopiere Elemente')
        funktioniert_nicht = False
        for item in self.scene().selectedItems():
            try:
                newitem = item.clone()
            except AttributeError:
                self.statusbarinfo.emit('Einige Elemente konnten nicht kopiert werden',1000) # funktioniert nicht
                funktioniert_nicht = True
                continue
            self.parent().undostack.push(AddItem(self.scene(),newitem))
            newitem.setSelected(True)
            item.setSelected(False)
        self.parent().undostack.endMacro()
        self.eswurdegemalt.emit()
        if not funktioniert_nicht:
            self.statusbarinfo.emit('Die Elemente sind kopiert. Bitte jetzt verschieben...',5000)

    @Slot(QGraphicsItem)
    def importItem(self, item: QGraphicsItem):
        self.parent().undostack.push(AddItem(self.scene(), item))
        item.setPos(self.mapToScene(0,0))
        if hasattr(item, 'registerPosition'):
            self.finishedEdit.connect(item.registerPosition)
        self.berechneSceneRectNeu(item)

        self.statusbarinfo.emit('Das Element oben links eingefügt. Bitte jetzt verschieben...',5000)
        self.eswurdegemalt.emit() 

    @Slot(str, float)
    def erweitern(self, richtung: str, laenge: float=0):
        scenerect = self.sceneRect()
        viewrect = self.mapToScene(self.viewport().geometry()).boundingRect()
        if richtung == 'bottom':
            offset = laenge if laenge else viewrect.height()/2
            if not scenerect.contains(viewrect.bottomLeft() + QPointF(0, offset)):
                scenerect.setBottom(viewrect.bottom() + offset)
                self.setSceneRect(scenerect)
            self.translate(0, -offset)
        elif richtung == 'top':
            offset = laenge if laenge else viewrect.height()/2
            if not scenerect.contains(viewrect.topLeft() - QPointF(0, offset)):
                scenerect.setTop(viewrect.top() - offset)
                self.setSceneRect(scenerect)
            self.translate(0, offset)
        elif richtung == 'left':
            offset = laenge if laenge else viewrect.width()/2
            if not scenerect.contains(viewrect.topLeft() - QPointF(offset,0)):
                scenerect.setLeft(viewrect.left() - offset)
                self.setSceneRect(scenerect)
            self.translate(offset, 0)
        elif richtung == 'right':
            offset = laenge if laenge else viewrect.width()/2
            if not scenerect.contains(viewrect.topRight() + QPointF(offset,0)):
                scenerect.setRight(viewrect.right() + offset)
                self.setSceneRect(scenerect)
            self.translate(-offset, 0)

    @Slot()
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

    @Slot()
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

    @Slot()
    def zoomreset(self):
        if self._status == self.statusEdit:
            if not self.scene().selectedItems():
                QMessageBox.warning(self, 'Hinweis', 'Bitte wählen Sie Elemente aus.')
                return
            for item in self.scene().selectedItems():
                item.setScale(1)
                self.berechneSceneRectNeu(item)
        else:
            self.resetTransform()

    @Slot()
    def clearall(self):
        geodreiecksichtbar = False
        if self._geodreieck.scene():
            geodreiecksichtbar = True
            self.scene().removeItem(self._geodreieck)
        self.parent().undostack.beginMacro('Lösche alles')
        for item in self.scene().items():
            self.parent().undostack.push(RemoveItem(self.scene(),item))
        self.parent().undostack.endMacro()
        if geodreiecksichtbar:
            self.scene().addItem(self._geodreieck)
        self.eswurdegemalt.emit()

    @Slot()
    def changeSceneRect(self):
        r = self.sceneRect()
        r2 = self.viewport().rect()
        self.scene().setSceneRect(r|r2)

    @Slot(bool)
    def enableGeodreieck(self, enable: bool):
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
        self.setIcon(SVGIcon('go-'+richtung))
        self.setToolTip('Seite erweitern')
        self.clicked.connect(lambda: self.erweitert.emit(self._richtung))
        self.setCursor(Qt.ArrowCursor)
        parent.parent().paletteChanged.connect(self.newPalette)

    @Slot()
    def newPalette(self):
        self.setIcon(SVGIcon('go-'+self._richtung))

    @Slot()
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
