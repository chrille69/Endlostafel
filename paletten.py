
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

light = QApplication.palette()
light.setColor(QPalette.PlaceholderText, QColor('#404040'))
light.setColor(QPalette.Disabled, QPalette.PlaceholderText, QColor('#A0A0A0'))

dark = QPalette()
dark.setColor(QPalette.Window, QColor(80, 80, 80))
dark.setColor(QPalette.WindowText, Qt.white)
dark.setColor(QPalette.Base, QColor(50, 50, 50))
dark.setColor(QPalette.AlternateBase, QColor(60,60,60))
dark.setColor(QPalette.ToolTipBase, Qt.black)
dark.setColor(QPalette.ToolTipText, Qt.white)
dark.setColor(QPalette.Text, Qt.white)
dark.setColor(QPalette.PlaceholderText, QColor('#D0D0D0'))
dark.setColor(QPalette.Disabled, QPalette.PlaceholderText, QColor('#707070'))
dark.setColor(QPalette.Button, QColor(53, 53, 53))
dark.setColor(QPalette.ButtonText, Qt.white)
dark.setColor(QPalette.BrightText, Qt.red)
dark.setColor(QPalette.Link, QColor(42, 130, 218))
dark.setColor(QPalette.Highlight, QColor(42, 130, 218))
dark.setColor(QPalette.HighlightedText, Qt.black)

