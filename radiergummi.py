
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
from PySide6.QtCore import QPointF, QRectF, Qt, QSizeF
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsView

logger = logging.getLogger('GUI')

class Radiergummi(QGraphicsRectItem):
    def __init__(self, size: QSizeF, pos: QPointF = QPointF(0,0)):
        super().__init__()
        rect = QRectF(QPointF(-size.width()/2, -size.height()/2), size)
        self.setRect(rect)
        self.setPos(pos)

        pen = QPen(QColor("red"), 3, Qt.DashLine, c=Qt.RoundCap, j=Qt.RoundJoin)
        pen.setCosmetic(True)
        pen.setDashPattern([2,2])
        pen.setDashOffset(7)
        self.setPen(pen)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'Radiergummi erzeugt {rect}')

    def setSize(self, size: QSizeF):
        rect = QRectF(QPointF(-size.width()/2, -size.height()/2), size)
        self.setRect(rect)

    def size(self) -> QSizeF:
        return self.rect().size()
