
from math import sqrt, log10
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPalette, QPen, QPixmap
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QApplication, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsView



class Pfad(QGraphicsPathItem):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__()
        self._view = view
        self._firstpos = pos
        self._fgcolor = view.fgcolor()
        self.setPen(pen)
        self.setBrush(brush)
        self.setPath(QPainterPath(pos))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCacheMode(QGraphicsItem.NoCache)
        view.mousemoved.connect(self.change)
        view.mousereleased.connect(self.disconnect)
        view.parent().paletteChanged.connect(self.newPalette)
        self._shape = None

    def newPalette(self):
        newfgcolor = QApplication.instance().palette().color(QPalette.WindowText)
        pen = self.pen()
        brush = self.brush()
        if pen.color() == self._fgcolor:
            pen.setColor(newfgcolor)
            self.setPen(pen)
        if brush.color() == self._fgcolor:
            brush.setColor(newfgcolor)
            self.setBrush(brush)
        self._fgcolor = newfgcolor
    
    def disconnect(self):
        self._view.mousemoved.disconnect()
        self._view.mousereleased.disconnect()

    def change(self):
        self.setTransformOriginPoint(self.boundingRect().center())

    def shape(self):
        if self._shape:
            return self._shape
        else:
            return super().shape()

    def setShape(self, shape):
        self._shape = shape

    def clone(self):
        clonepfad = Pfad(self._view, self._firstpos, self.pen(), self.brush())
        clonepfad.setPath(self.path())
        clonepfad.setPos(self.pos())
        clonepfad.setScale(self.scale())
        clonepfad.change()
        return clonepfad

    def removeElements(self, ellipse: QGraphicsEllipseItem):
        neupfad = QPainterPath()
        anzahl = self.path().elementCount()
        if anzahl > 1:
            geschnitten = True
            for i in range(anzahl):
                element = self.path().elementAt(i)
                pos = QPointF(element.x, element.y)
                #linienschnitt = False
                #if i > 0:
                #    vorelement = self.path().elementAt(i-1)
                #    vorpos = QPointF(vorelement.x, vorelement.y)
                #    linienschnitt = self.schnittLinieKreis(self.mapToScene(vorpos), self.mapToScene(pos), ellipse.rect().center(), ellipse.rect().height()/2)
                #if not (ellipse.shape().contains(self.mapToScene(pos)) or linienschnitt):
                if not ellipse.shape().contains(self.mapToScene(pos)):
                    if geschnitten:
                        geschnitten=False
                        neupfad.moveTo(pos)
                    else:
                        if element.isLineTo():
                            neupfad.lineTo(pos)
                        else:
                            neupfad.moveTo(pos)
                else:
                    geschnitten=True
        self.setPath(neupfad)
        self.setTransformOriginPoint(self.boundingRect().center())

    def schnittLinieKreis(self, pos1, pos2, m, r):
        n = QPointF(pos2.y()-pos1.y(),pos1.x()-pos2.x())
        d = abs(((m.x()-pos1.x())*n.x()+(m.y()-pos1.y())*n.y()) / sqrt(n.x()*n.x()+n.y()*n.y()))
        return d < r






class Stift(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos: QPointF):
        path = self.path()
        path.lineTo(pos)
        self.setPath(path)
        super().change()


class Line(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos):
        path = QPainterPath(self._firstpos)
        path.lineTo(pos)
        self.setPath(path)
        super().change()


class Pfeil(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos):
        path = QPainterPath(self._firstpos)
        path.lineTo(pos)
        ds = pos - self._firstpos
        ds0 = ds/sqrt(ds.x()*ds.x()+ds.y()*ds.y())
        dl0 = QPointF(ds0.y(), -ds0.x())
        lw = self.pen().widthF()
        path.moveTo(pos)
        path.lineTo(pos-5*lw*ds0+lw*dl0)
        path.lineTo(pos-5*lw*ds0-lw*dl0)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Kreis(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)
    
    def change(self, pos):
        path = QPainterPath(self._firstpos)
        rx = abs(pos.x()-self._firstpos.x())
        ry = abs(pos.y()-self._firstpos.y())
        r = sqrt(rx*rx+ry*ry)
        path.addEllipse(self._firstpos, r, r)
        self.setPath(path)
        super().change()


class Ellipse(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos):
        path = QPainterPath(self._firstpos)
        rx = abs(pos.x()-self._firstpos.x())
        ry = abs(pos.y()-self._firstpos.y())
        path.addEllipse(self._firstpos, rx, ry)
        self.setPath(path)
        super().change()


class Quadrat(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos):
        dx, dy = (pos - self._firstpos).toTuple()
        d = max(dx, dy)
        dx = d if dx > 0 else -d
        dy = d if dy > 0 else -d
        path = QPainterPath(self._firstpos)
        path.lineTo(self._firstpos.x(),    self._firstpos.y()+dy)
        path.lineTo(self._firstpos.x()+dx, self._firstpos.y()+dy)
        path.lineTo(self._firstpos.x()+dx, self._firstpos.y())
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Rechteck(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)

    def change(self, pos):
        (x1, y1), (x2, y2) = self._firstpos.toTuple(), pos.toTuple()
        path = QPainterPath(self._firstpos)
        path.lineTo(x1, y2)
        path.lineTo(x2, y2)
        path.lineTo(x2,y1)
        path.closeSubpath()
        self.setPath(path)
        super().change()


class Punkt(Pfad):
    def __init__(self, view: QGraphicsView, pos: QPointF, pen: QPen, brush: QBrush):
        super().__init__(view, pos, pen, brush)
        path = self.path()
        path.lineTo(pos*1.0001)
        self.setPath(path)
        self.change()


class Karopapier(Pfad):
    def __init__(self, view: QGraphicsView):
        super().__init__(view, QPointF(), Qt.NoPen, Qt.NoBrush)
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

    def clone(self):
        new = super().clone()
        new.setShape(self.shape())
        return new


class Linienpapier(Pfad):
    def __init__(self, view: QGraphicsView):
        super().__init__(view, QPointF(), Qt.NoPen, Qt.NoBrush)
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

    def clone(self):
        new = super().clone()
        new.setShape(self.shape())
        return new


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

    def clone(self):
        pixmap = Pixelbild(self.pixmap())
        pixmap.setPos(self.pos())
        pixmap.setScale(self.scale())
        return pixmap


class SVGBild(QGraphicsSvgItem):
    def __init__(self, svgfilename: str):
        super().__init__(svgfilename)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def clone(self):
        newitem = QGraphicsSvgItem()
        newitem.setSharedRenderer(self.renderer())
        newitem.setTransformOriginPoint(newitem.boundingRect().center())
        newitem.setScale(self.scale())
        newitem.setPos(self.pos())
        newitem.setFlag(QGraphicsItem.ItemIsMovable, True)
        newitem.setFlag(QGraphicsItem.ItemIsSelectable, True)
        return newitem