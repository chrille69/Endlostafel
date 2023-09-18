
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
from PySide6.QtCore import QEvent, QPointF, QRect, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPalette, QPen, QResizeEvent, QTransform
from PySide6.QtWidgets import QApplication, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem, QGraphicsScene, QGraphicsView, QMessageBox, QToolButton, QWidget, QGestureEvent, QPinchGesture, QPanGesture

class Radiergummi(QGraphicsRectItem):
    def __init__(self, view: QGraphicsView, width: float, height: float, pos: QPointF = QPointF(0,0)):
        super().__init__()
        view.parent().paletteChanged.connect(self.newPalette)
        self.setRect(QRectF(-width/2, -height/2, width, height))
        self.setPos(pos)

        color = QApplication.instance().palette().color(QPalette.PlaceholderText)
        pen = QPen(color, 3, Qt.DashLine, c=Qt.RoundCap, j=Qt.RoundJoin)
        self.setPen(pen)

    def setSize(self, width: float, height: float):
        self.setRect(QRectF(-width/2, -height/2, width, height))

    def newPalette(self):
        newfgcolor = QApplication.instance().palette().color(QPalette.PlaceholderText)
        pen = self.pen()
        pen.setColor(newfgcolor)
