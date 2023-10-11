
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
logger = logging.getLogger('GUI')

from math import sqrt, log10
from typing import Any
from PySide6.QtCore import QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPalette, QPen, QPixmap
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem

from undo import MoveItem

class Pfad(QGraphicsPathItem):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__()
        self._colorisfgcolor = False
        self.setPos(pos)
        self.setPen(pen)
        self.setBrush(brush)
        self.setPath(QPainterPath())
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self._shape = None
        self._oldpos = None

    def oldPos(self):
        return self._oldpos

    def setColorIsFGColor(self, isfgcolor: bool):
        self._colorisfgcolor = isfgcolor

    def newPalette(self, palette):
        newfgcolor = palette.color(QPalette.WindowText)
        pen = self.pen()
        brush = self.brush()
        if self._colorisfgcolor:
            pen.setColor(newfgcolor)
            self.setPen(pen)
            brush.setColor(newfgcolor)
            self.setBrush(brush)
    
    def change(self):
        self.setTransformOriginPoint(self.boundingRect().center())

    def registerPosition(self, undostack):
        if self._oldpos:
            undostack.push(MoveItem(self, QPointF(self._oldpos), QPointF(self.pos())))
            self._oldpos = None

    def shape(self):
        if self._shape:
            return self._shape
        else:
            return super().shape()

    def setShape(self, shape):
        self._shape = shape

    def clone(self):
        clonepfad = Pfad(self.pos(), self.pen(), self.brush())
        clonepfad.setPath(self.path())
        clonepfad.setPos(self.pos())
        clonepfad.setScale(self.scale())
        clonepfad.change()
        if self._shape:
            clonepfad.setShape(self._shape)
        return clonepfad

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange:
            if not self._oldpos:
                self._oldpos = self.pos()
        return super().itemChange(change, value)

    def removeElements(self, radiererpfadscene: QPainterPath):
        radiererpfad = self.mapFromScene(radiererpfadscene)
        neupfad = QPainterPath()
        if self.brush() != Qt.NoBrush:
            # Gefüllte Elemente werden gelöscht.
            self.setPath(neupfad)
            return
        anzahl = self.path().elementCount()
        if anzahl > 1:
            geschnitten = False
            i=0
            while i < anzahl:
                element = self.path().elementAt(i)
                pos = QPointF(element.x, element.y)
                cp1 = None
                cp2 = None
                if element.isCurveTo():
                    cp1 = pos
                    i += 1
                    de1 = self.path().elementAt(i)
                    cp2 = QPointF(de1.x,de1.y)
                    i += 1
                    de2 = self.path().elementAt(i)
                    pos = QPointF(de2.x,de2.y)
                #logger.info(f"{i}: {pos}, {element.type}, {cp1} : {cp2}")
                if radiererpfad.contains(pos) and element.type != QPainterPath.CurveToDataElement:
                    # Dieser Punkt wird nicht gezeichnet
                    geschnitten = True
                else:
                    if geschnitten:
                        neupfad.moveTo(pos)
                    else:
                        if element.isLineTo():
                            neupfad.lineTo(pos)
                        elif element.isCurveTo():
                            neupfad.cubicTo(cp1,cp2,pos)
                        else:
                            neupfad.moveTo(pos)
                    geschnitten=False
                i += 1

        self.setPath(neupfad)
        self.setTransformOriginPoint(self.boundingRect().center())


class Stift(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        path = self.path()
        path.lineTo(pos)
        self.setPath(path)
        super().change()


class Linie(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        path = QPainterPath()
        path.lineTo(pos)
        self.setPath(path)
        super().change()


class LinieSnap(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        newpos = QPointF(0, pos.y())
        if abs(pos.y()) <= abs(pos.x()):
            newpos.setX(pos.x())
            newpos.setY(0)
        path = QPainterPath()
        path.lineTo(newpos)
        self.setPath(path)
        super().change()


class Pfeil(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        path = QPainterPath()
        path.lineTo(pos)
        ds = pos
        ds0 = ds/sqrt(ds.x()*ds.x()+ds.y()*ds.y())
        dl0 = QPointF(ds0.y(), -ds0.x())
        lw = self.pen().widthF()
        path.moveTo(pos)
        path.lineTo(pos-5*lw*ds0+lw*dl0)
        path.lineTo(pos-5*lw*ds0-lw*dl0)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class PfeilSnap(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        newpos = QPointF(0, pos.y())
        if abs(pos.y()) <= abs(pos.x()):
            newpos.setX(pos.x())
            newpos.setY(0)
        path = QPainterPath()
        path.lineTo(newpos)
        ds = newpos
        ds0 = ds/sqrt(ds.x()*ds.x()+ds.y()*ds.y())
        dl0 = QPointF(ds0.y(), -ds0.x())
        lw = self.pen().widthF()
        path.moveTo(newpos)
        path.lineTo(newpos-5*lw*ds0+lw*dl0)
        path.lineTo(newpos-5*lw*ds0-lw*dl0)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Kreis(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)
    
    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        rx = pos.x()
        ry = pos.y()
        r = sqrt(rx*rx+ry*ry)
        rect = QRectF(QPointF(-r,-r), QSizeF(2*r,2*r))
        path = QPainterPath(QPointF(r,0))
        for winkel in range(0,360,15):
            path.arcTo(rect, winkel, 15)
        self.setPath(path)
        super().change()


class Ellipse(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        rx = abs(pos.x())
        ry = abs(pos.y())
        rect = QRectF(-QPointF(rx,ry), QSizeF(2*rx,2*ry))
        path = QPainterPath(QPointF(rx,0))
        for winkel in range(0,360,15):
            path.arcTo(rect, winkel, 15)
        self.setPath(path)
        super().change()


class Quadrat(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        dx, dy = pos.toTuple()
        d = max(abs(dx), abs(dy))
        dx = d if dx > 0 else -d
        dy = d if dy > 0 else -d
        path = QPainterPath()
        path.lineTo( 0, dy)
        path.lineTo(dx, dy)
        path.lineTo(dx,  0)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Rechteck(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)

    def change(self, posscene: QPointF):
        pos = self.mapFromScene(posscene)
        x2, y2 = pos.toTuple()
        path = QPainterPath()
        path.lineTo( 0, y2)
        path.lineTo(x2, y2)
        path.lineTo(x2,  0)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Punkt(Pfad):
    def __init__(self, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(pos, pen, brush)
        path = self.path()
        path.lineTo(.0001,0)
        self.setPath(path)
        self.change()


class Karopapier(Pfad):
    def __init__(self):
        super().__init__(QPointF(), Qt.NoPen, Qt.NoBrush)
        pen = QPen(QColor('lightblue'))
        pen.setCosmetic(True)
        self.setPen(pen)
        self._karosize = 50
        self._anzahl = 100
        self._length = self._karosize*self._anzahl


        path = self.path()
        for n in range(self._anzahl+1):
            a = n*self._karosize
            path.moveTo(0,a)
            path.lineTo(self._length,a)
            path.moveTo(a,0)
            path.lineTo(a, self._length)
        self.setPath(path)

        shape = QPainterPath(QPointF(0,0))
        shape.lineTo(self._length, 0)
        shape.lineTo(self._length, self._length)
        shape.lineTo(0, self._length)
        self.setShape(shape)


class Linienpapier(Pfad):
    def __init__(self):
        super().__init__(QPointF(), Qt.NoPen, Qt.NoBrush)
        pen = QPen(QColor('lightblue'))
        pen.setCosmetic(True)
        self.setPen(pen)
        self._liniensize = 75
        self._anzahl = 100
        self._length = self._liniensize*self._anzahl

        path = self.path()
        for n in range(self._anzahl+1):
            a = n*self._liniensize
            path.moveTo(0,a)
            path.lineTo(self._length,a)
        self.setPath(path)

        shape = QPainterPath(QPointF(0,0))
        shape.lineTo(self._length, 0)
        shape.lineTo(self._length, self._length)
        shape.lineTo(0, self._length)
        self.setShape(shape)


class MmLogPapier(QGraphicsRectItem):
    def __init__(self, length, xanz, xtyp, yanz, ytyp):
        super().__init__()
        self.setPen(Qt.NoPen)
        self._length = length
        self._xanz = xanz
        self._xtyp = xtyp
        self._yanz = yanz
        self._ytyp = ytyp
        for x in range(xanz):
            for y in range(yanz):
                xachse = MmLogRect(length, xtyp)
                xachse.setParentItem(self)
                xachse.moveBy(x*length,y*length)
                yachse = MmLogRect(length, ytyp)
                yachse.setParentItem(self)
                yachse.setRotation(-90)
                yachse.moveBy(x*length,y*length)
        self.setRect(0,0,xanz*length,yanz*length)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def clone(self):
        newitem = MmLogPapier(self._length, self._xanz, self._xtyp, self._yanz, self._ytyp)
        newitem.setPos(self.pos())
        newitem.setScale(self.scale())
        return newitem


class MmLogRect(QGraphicsRectItem):

    MM, LOG = range(2)

    def __init__(self, length, typ):
        super().__init__()
        self.setPen(Qt.NoPen)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setData(1, True)
        self._length = length
        self._typ = typ
        self._pen = QPen(QColor('orange'))
        self._pen.setCosmetic(True)
        if self._typ == MmLogRect.LOG:
            self.createLogLines()
        else:
            self.createMmLines()
        self.setTransformOriginPoint(length/2, length/2)

    def createMmLines(self):
        max = 100
        for n in range(max+1):
            line = self.createLine(n*self._length/max, 0, n*self._length/max, self._length)
            if n%10 == 0:
                self._pen.setWidthF(3)
            elif n%5 == 0:
                self._pen.setWidthF(2)
            else:
                self._pen.setWidthF(1)
            line.setPen(self._pen)

    def createLogLines(self):
        for n in range(0,90,2):
            line = self.createLine(log10(1+n/10)*self._length, 0, log10(1+n/10)*self._length, self._length)
            if n%10 == 0:
                self._pen.setWidthF(3)
            else:
                self._pen.setWidthF(1)
            line.setPen(self._pen)

        # Letzte Linie muss Extra gezogen werden:
        line = self.createLine(self._length, 0, self._length, self._length)
        self._pen.setWidthF(3)
        line.setPen(self._pen)

    def createLine(self, x1, y1, x2, y2):
        line = QGraphicsLineItem(x1, y1, x2, y2)
        line.setFlag(QGraphicsItem.ItemIsMovable, False)
        line.setFlag(QGraphicsItem.ItemIsSelectable, False)
        line.setData(1, True)
        line.setParentItem(self)
        return line


class Pixelbild(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap):
        super().__init__(pixmap)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._oldpos = None

    def oldPos(self):
        return self._oldpos

    def clone(self):
        pixmap = Pixelbild(self.pixmap())
        pixmap.setPos(self.pos())
        pixmap.setScale(self.scale())
        return pixmap

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange:
            if not self._oldpos:
                self._oldpos = self.pos()
        return super().itemChange(change, value)

    def registerPosition(self, undostack):
        if self._oldpos:
            undostack.push(MoveItem(self, QPointF(self._oldpos), QPointF(self.pos())))
            self._oldpos = None


class SVGBild(QGraphicsSvgItem):
    def __init__(self, svgfilename: str):
        super().__init__(svgfilename)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._oldpos = None

    def oldPos(self):
        return self._oldpos

    def clone(self):
        newitem = QGraphicsSvgItem()
        newitem.setSharedRenderer(self.renderer())
        newitem.setTransformOriginPoint(newitem.boundingRect().center())
        newitem.setScale(self.scale())
        newitem.setPos(self.pos())
        newitem.setFlag(QGraphicsItem.ItemIsMovable, True)
        newitem.setFlag(QGraphicsItem.ItemIsSelectable, True)
        newitem.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        return newitem

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange:
            if not self._oldpos:
                self._oldpos = self.pos()
        return super().itemChange(change, value)

    def registerPosition(self, undostack):
        if self._oldpos:
            undostack.push(MoveItem(self, QPointF(self._oldpos), QPointF(self.pos())))
            self._oldpos = None

class TextItem(QGraphicsTextItem):
    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._oldpos = None

    def oldPos(self):
        return self._oldpos

    def clone(self):
        newitem = TextItem()
        newitem.setHtml(self.toHtml())
        newitem.setScale(self.scale())
        newitem.setPos(self.pos())
        return newitem

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.ItemPositionChange:
            if not self._oldpos:
                self._oldpos = self.pos()
        return super().itemChange(change, value)

    def registerPosition(self, undostack):
        if self._oldpos:
            undostack.push(MoveItem(self, QPointF(self._oldpos), QPointF(self.pos())))
            self._oldpos = None
