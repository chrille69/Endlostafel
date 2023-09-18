
import logging
from PySide6.QtWidgets import QWidget, QTextEdit, QDialog, QGridLayout

class LogWindowHandler(logging.Handler):
    def __init__(self, logwindow) -> None:
        logging.Handler.__init__(self)
        self._logwindow = logwindow

    def emit(self, record):
        self._logwindow.append(self.format(record))

class LogWindow(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self._text_edit = QTextEdit(self)
        self._text_edit.setLineWrapMode(QTextEdit.NoWrap)
        self._text_edit.setReadOnly(True)
        layout = QGridLayout()
        layout.addWidget(self._text_edit)
        self.setLayout(layout)

    def append(self, text):
        self._text_edit.append(text)
