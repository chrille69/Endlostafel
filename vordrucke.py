
from PySide6.QtWidgets import QButtonGroup, QDialog, QDoubleSpinBox, QGraphicsItem, QGroupBox, QHBoxLayout, QLabel, QPushButton, QRadioButton, QSpinBox, QVBoxLayout, QWidget
from PySide6.QtCore import Signal

from items import MmLogPapier, MmLogRect

class MmLogDialog(QDialog):
    mmPapierCreated = Signal(QGraphicsItem)

    def __init__(self) -> None:
        super().__init__()

        self.xAchse = MmAchseKonfig('x-Achse', MmAchseKonfig.Horizontal, self)
        self.yAchse = MmAchseKonfig('y-Achse', MmAchseKonfig.Vertical, self)

        bt_cancel = QPushButton('Abbrechen')
        bt_ok = QPushButton('Ok')

        w_buttons = QWidget()
        hb_buttons = QHBoxLayout()
        w_buttons.setLayout(hb_buttons)
        hb_buttons.addWidget(bt_cancel)
        hb_buttons.addWidget(bt_ok)

        w_laenge = QWidget()
        hb_laenge = QHBoxLayout()
        w_laenge.setLayout(hb_laenge)
        lb_laenge = QLabel('Länge einer Dekade')
        self.sp_laenge = QDoubleSpinBox()
        self.sp_laenge.setMaximum(2000)
        self.sp_laenge.setValue(500)
        hb_laenge.addWidget(lb_laenge)
        hb_laenge.addWidget(self.sp_laenge)

        vbox = QVBoxLayout(self)
        self.setLayout(vbox)
        vbox.addWidget(self.xAchse)
        vbox.addWidget(self.yAchse)
        vbox.addWidget(w_laenge)
        vbox.addWidget(w_buttons)

        bt_cancel.clicked.connect(self.close)
        bt_ok.clicked.connect(self.getMmPapier)

    def getMmPapier(self):
        xanz = self.xAchse.getDekadeAnzahl()
        xtyp = self.xAchse.getTyp()
        yanz = self.yAchse.getDekadeAnzahl()
        ytyp = self.yAchse.getTyp()
        length = self.sp_laenge.value()
        papier = MmLogPapier(length, xanz, xtyp, yanz, ytyp)
        self.mmPapierCreated.emit(papier)
        self.close()


class MmAchseKonfig(QGroupBox):
    
    Horizontal, Vertical = range(2)

    def __init__(self, text, orientation, parent):
        super().__init__(text, parent)
        self._orientation = orientation

        lb_dekaden = QLabel('Dekaden:')
        self.sp_dekaden = QSpinBox()
        self.sp_dekaden.setValue(2)
        self.rb_typMm = QRadioButton('mm')
        self.rb_typLog = QRadioButton('log')
        bg_typ = QButtonGroup()
        bg_typ.addButton(self.rb_typMm)
        bg_typ.addButton(self.rb_typLog)
        self.rb_typMm.setChecked(True)

        hbox = QHBoxLayout(self)
        hbox.addWidget(self.rb_typMm)
        hbox.addWidget(self.rb_typLog)
        hbox.addWidget(lb_dekaden)
        hbox.addWidget(self.sp_dekaden)
        self.setLayout(hbox)

    def getDekadeAnzahl(self):
        return self.sp_dekaden.value()

    def getTyp(self):
        if self.rb_typMm.isChecked():
            return MmLogRect.MM
        else:
            return MmLogRect.LOG
