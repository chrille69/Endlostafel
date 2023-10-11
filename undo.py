
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

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QWidget, QDialog, QGridLayout, QUndoView

class AddItem(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem):
        super().__init__()
        self._item = item
        self._scene = scene
        self.setText('Element eingefügt')

    def undo(self):
        self._scene.removeItem(self._item)
    
    def redo(self):
        self._scene.addItem(self._item)

class RemoveItem(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem):
        super().__init__()
        self._item = item
        self._scene = scene
        self.setText('Element entfernt')

    def undo(self):
        self._scene.addItem(self._item)
    
    def redo(self):
        self._scene.removeItem(self._item)

class ChangePathItems(QUndoCommand):
    def __init__(self, clonedItems: dict):
        super().__init__()
        self._itemsPaths = {}
        for orig in clonedItems:
            self._itemsPaths[orig] = [orig.path(), clonedItems[orig].path() ]
        self.setText('Elemente geändert')

    def undo(self):
        for orig, paths in self._itemsPaths.items():
            orig.setPath(paths[1])
    
    def redo(self):
        for orig, paths in self._itemsPaths.items():
            orig.setPath(paths[0])

class MoveItem(QUndoCommand):
    def __init__(self, item: QGraphicsItem, oldpos: QPointF, newpos: QPointF):
        super().__init__()
        self._item = item
        self._oldpos = oldpos
        self._newpos = newpos
        self.setText('Element verschoben')

    def undo(self):
        self._item.setPos(self._oldpos)
    
    def redo(self):
        self._item.setPos(self._newpos)

class UndoWindow(QDialog):
    def __init__(self, parent: QWidget, undostack: QUndoStack) -> None:
        super().__init__(parent)
        layout = QGridLayout()
        layout.addWidget(QUndoView(undostack, self))
        self.setLayout(layout)

