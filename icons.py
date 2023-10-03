
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

from PySide6.QtCore import QByteArray, QSize
from PySide6.QtGui import QColor, QCursor, QImage, QPainter, QPalette, QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QGraphicsItem, QStyleOptionGraphicsItem

logger = logging.getLogger('GUI')


class SVGImage(QImage):
    def __init__(self, name: str, width: int, htmlcolor: str):
        super().__init__(QSize(width, width), QImage.Format_ARGB32)
        svgstr = iconssvg[name if name in iconssvg else 'help']
        svg = QSvgRenderer(QByteArray(svgstr.format(htmlcolor=htmlcolor)))
        self.fill(0)
        painter = QPainter()
        painter.begin(self)
        svg.render(painter)
        painter.end()


class ItemCursor(QCursor):
    def __init__(self, item: QGraphicsItem, scale: float, hotx: int, hoty: int):
        img = QImage(item.boundingRect().size().toSize()*scale, QImage.Format_ARGB32)
        img.fill(0)
        painter = QPainter()
        painter.begin(img)
        painter.scale(scale,scale)
        painter.translate(-item.boundingRect().topLeft())
        item.paint(painter, QStyleOptionGraphicsItem())
        painter.end()
        super().__init__(QPixmap(img), hotx, hoty)


class SVGCursor(QCursor):
    def __init__(self, name: str, width: float=32):
        name2hotspot = {
            'stift'    : [0, 32],
            'linie'    : [5, 5],
            'pfeil'    : [5, 5],
            'quadrat'  : [4, 4],
            'rechteck' : [4, 10],
            'ellipse'  : [-1, -1],
            'kreis'    : [-1, -1],
            'quadratf' : [4, 4],
            'rechteckf': [4, 10],
            'ellipsef' : [-1, -1],
            'kreisf'   : [-1, -1],
            'radierer' : [11.5, 32],
            'ereaser'  : [-1,-1],
            'edit'     : [3, 3]
        }

        if name in name2hotspot:
            x, y = name2hotspot[name]
        else:
            name, x, y = 'help', -1, -1 # Fragezeichen als SVG-String

        palette = QApplication.instance().palette()
        color = palette.color(QPalette.PlaceholderText)
        htmlcolor = color.name()
        super().__init__(QPixmap(SVGImage(name, width, htmlcolor)), x, y)


class ColorIcon(QIcon):
    def __init__(self, qcolor: QColor):
        pixmap=QPixmap(32,32)
        pixmap.fill(qcolor)
        super().__init__(pixmap)


class SVGIcon(QIcon):
    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self._svgstr = iconssvg[name if name in iconssvg else 'help']
        self.addPixmap(self.paintPixmap(QIcon.Normal), QIcon.Normal)
        self.addPixmap(self.paintPixmap(QIcon.Disabled), QIcon.Disabled)

    def newPalette(self):
        logger.debug(QApplication.instance().palette().color(QPalette.PlaceholderText))
        self.swap(SVGIcon(self._name))

    def paintPixmap(self, mode: QIcon.Mode):
        palette = QApplication.instance().palette()
        if mode == QIcon.Disabled:
            color = palette.color(QPalette.Disabled, QPalette.PlaceholderText)
        else:
            color = palette.color(QPalette.PlaceholderText)
        htmlcolor = color.name()
        return QPixmap(SVGImage(self._name, 32, htmlcolor))





iconssvg = {
    'exit': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m6 2.5742c-2.5064.84091-4.3242 3.2102-4.3242 5.9922 2e-7 3.4807 2.8435 6.3242 6.3242 6.3242 3.4807 0 6.3242-2.8435 6.3242-6.3242 0-2.782-1.8178-5.1513-4.3242-5.9922v2.1758c1.3787.71968 2.3242 2.1441 2.3242 3.8164 0 2.3998-1.9244 4.3242-4.3242 4.3242-2.3998 0-4.3242-1.9244-4.3242-4.3242 0-1.6723.94552-3.0967 2.3242-3.8164z"/>
            <path style="fill:{htmlcolor}" d="m7 1v6h2v-6z"/>
        </svg>''',
    'fullscreen': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:none;stroke-width:1px;stroke:{htmlcolor}" d="m14 9v4h-4m-8-4v4h4m8-6v-4h-4m-8 4v-4h4"/>
        </svg>''',
    'go-bottom': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 10,14 A 2,2 0 0 1 8,16 2,2 0 0 1 6,14 2,2 0 0 1 8,12 2,2 0 0 1 10,14 Z"/>
            <path style="fill:{htmlcolor}" d="M 7,0 V 7 L 3.5,3.5 2,5 8,11 14,5 12.5,3.5 9,7 V 0 Z"/>
        </svg>''',
    'go-top': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m10 2c.016981-.92278-.68916-1.7893-1.5964-1.9588-.87657-.196-1.8429.28571-2.2122 1.1051-.41778.84258-.12868 1.951.64746 2.4822.75513.56094 1.8972.47283 2.5577-.19676.38304-.37067.60558-.89864.60345-1.4317z"/>
            <path style="fill:{htmlcolor}" d="m7 16v-7l-3.5 3.5-1.5-1.5 6-6 6 6-1.5 1.5-3.5-3.5v7z"/>
        </svg>''',
    'go-right': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m13.999 9.9988c.92278.016981 1.7893-.68916 1.9588-1.5964.196-.87657-.28571-1.8429-1.1051-2.2122-.84258-.41778-1.951-.12868-2.4822.64746-.56094.75513-.47283 1.8972.19676 2.5577.37067.38304.89864.60558 1.4317.60345z"/>
            <path style="fill:{htmlcolor}" d="m-.001225 6.9988h7l-3.5-3.5 1.5-1.5 6 6-6 6-1.5-1.5 3.5-3.5h-7z"/>
        </svg>''',
    'go-left': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m2.0012 5.9988c-.92278-.016981-1.7893.68916-1.9588 1.5964-.196.87657.28571 1.8429 1.1051 2.2122.84258.41778 1.951.12868 2.4822-.64746.56094-.75513.47283-1.8972-.19676-2.5577-.37067-.38304-.89864-.60558-1.4317-.60345z"/>
            <path style="fill:{htmlcolor}" d="m16.001 8.9988h-7l3.5 3.5-1.5 1.5-6-6 6-6 1.5 1.5-3.5 3.5h7z"/>
        </svg>''',
    'pensize-1px': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9903 6.9428c.5837 0 1.0569.47334 1.0569 1.0572 0 .5839-.47318 1.0572-1.0569 1.0572s-1.0569-.47334-1.0569-1.0572c0-.5839.47318-1.0572 1.0569-1.0572z"/>
        </svg>''',
    'pensize-3px': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9903 5.3319c1.4731 0 2.6672 1.1946 2.6672 2.6681 0 1.4736-1.1942 2.6681-2.6672 2.6681s-2.6672-1.1946-2.6672-2.6681c0-1.4736 1.1942-2.6681 2.6672-2.6681z"/>
        </svg>''',
    'pensize-5px': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9903 3.8081c2.3144 0 4.1905 1.8768 4.1905 4.1919 0 2.3151-1.8762 4.1919-4.1905 4.1919-2.3144 0-4.1905-1.8768-4.1905-4.1919 0-2.3151 1.8762-4.1919 4.1905-4.1919z"/>
        </svg>''',
    'pensize-20px': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9903 1.6095c3.5282 0 6.3884 2.8612 6.3884 6.3906 0 3.5294-2.8602 6.3906-6.3884 6.3906-3.5282 0-6.3884-2.8612-6.3884-6.3906 0-3.5294 2.8602-6.3906 6.3884-6.3906z"/>
        </svg>''',
    'stift': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m0 13v2.999l3 .001 8-8-3-3zm14-8c.3-.3.3-.7 0-1l-2-2c-.3-.3-.7-.3-1 0l-2 2 3 3z"/>
        </svg>''',
    'linie': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 12.778,13.778 C 12.778,13.778 13.278,14.278 13.778,13.778 14.278,13.278 13.778,12.778 13.778,12.778 L 3.2237,2.2237 C 3.2237,2.2237 2.7237,1.7237 2.2237,2.2237 1.7237,2.7237 2.2237,3.2237 2.2237,3.2237 Z"/>
        </svg>''',
    'linies':'''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m2 14s0 .56841.70711.56841.70711-.56841.70711-.56841v-11.998s0-.56841-.70711-.56841-.70711.56841-.70711.56841z" style="fill:{htmlcolor}"/>
            <path d="m5 8s-.44599 0-.44599.70711c0 .70711.44599.70711.44599.70711h9.4142s.44599 0 .44599-.70711-.44599-.70711-.44599-.70711z" style="fill:{htmlcolor}"/>
        </svg>''',
    'pfeil': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m5.5929 3.0962-3.5912-1.0943 1.0943 3.5912.74849-.74848 8.7115 8.7115s.5.5 1 0 0-1 0-1l-8.7115-8.7115.74848-.74849z"/>
        </svg>''',
    'pfeils': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m4.4726 5-1.7656-3.3131-1.7656 3.3131 1.0585 7.1e-6v8.9675s0 .70711.70711.70711c.70711 0 .70711-.70711.70711-.70711v-8.9675l1.0585-7.1e-6z" style="fill:{htmlcolor}"/>
            <path d="m11.687 11.766 3.3131-1.7656-3.3131-1.7656-7e-6 1.0585h-6.856s-.70711 0-.70711.70711c0 .70711.70711.70711.70711.70711h6.856l7e-6 1.0585z" style="fill:{htmlcolor}"/>
        </svg>''',
    'quadrat': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 1,1 V 15 H 15 V 1 Z M 3,3 H 13 V 13 H 3 Z"/>
        </svg>''',
    'quadratf': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <rect style="fill:{htmlcolor};stroke-width:2" x="2" y="2" width="12" height="12"/>
        </svg>''',
    'rechteck': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m1 4v8h14v-8zm2 2h10v4h-10z"/>
        </svg>''',
    'rechteckf': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <rect style="fill:{htmlcolor};stroke-width:2" x="2" y="5" width="12" height="6"/>
        </svg>''',
    'kreis': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <circle style="fill:none;stroke-width:2;stroke:{htmlcolor}" cx="8" cy="8" r="7"/>
            <path style="fill:none;stroke-width:1px;stroke:{htmlcolor}" d="m10 6-4 4m0-4 4 4"/>
        </svg>''',
    'kreisf': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9062 1a7 7 0 00-6.9062 7 7 7 0 007 7 7 7 0 007-7 7 7 0 00-7-7 7 7 0 00-.09375 0zm-1.5527 4.6465 1.6465 1.6465 1.6465-1.6465.70703.70703-1.6465 1.6465 1.6465 1.6465-.70703.70703-1.6465-1.6465-1.6465 1.6465-.70703-.70703 1.6465-1.6465-1.6465-1.6465.70703-.70703z"/>
        </svg>''',
    'ellipse': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <ellipse style="fill:none;stroke-width:2;stroke:{htmlcolor}" cx="8" cy="8" rx="7" ry="5"/>
            <path style="fill:none;stroke-width:1px;stroke:{htmlcolor}" d="m10 6-4 4m0-4 4 4"/>
        </svg>''',
    'ellipsef': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m7.9824 3a7 5 0 00-6.9824 5 7 5 0 007 5 7 5 0 007-5 7 5 0 00-7-5 7 5 0 00-.017578 0zm-1.6289 2.6465 1.6465 1.6465 1.6465-1.6465.70703.70703-1.6465 1.6465 1.6465 1.6465-.70703.70703-1.6465-1.6465-1.6465 1.6465-.70703-.70703 1.6465-1.6465-1.6465-1.6465.70703-.70703z"/>
        </svg>''',
    'ereaser': '''
        <svg width="13.652" height="13.679" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <rect x=".32455" y=".33192" width="13.004" height="13.019" ry="0" style="fill:none;stroke-dasharray:2.4738, 0.651;stroke-width:.651;stroke:{htmlcolor}"/>
        </svg>''',
    'ereaser2': '''
        <svg width="13.652" height="13.679" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:none;stroke-dasharray:2.60539, 1.3027;stroke-width:.65135;stroke:{htmlcolor}" d="m6.8132.32568c3.5973 0 6.5135 2.9162 6.5135 6.5135s-2.9162 6.5135-6.5135 6.5135c-3.5973 0-6.5135-2.9162-6.5135-6.5135s2.9162-6.5135 6.5135-6.5135z"/>
        </svg>''',
    'radierer': '''
        <svg width="19.963" height="17" version="1.1" viewBox="0 -960 798.51 680" xmlns="http://www.w3.org/2000/svg" fill="{htmlcolor}">
            <path d="m608.51-360h190v80h-270zm-500 80-85-85c-15.333-15.333-23.167-34.333-23.5-57s7.1667-42 22.5-58l440-456c15.333-16 34.167-24 56.5-24s41.167 7.6667 56.5 23l199 199c15.333 15.333 23 34.333 23 57s-7.6667 41.667-23 57l-336 344zm296-80 227.75-235.75-198-198-355.75 369.75 64 64z"/>
        </svg>''',
    'radierer-kalibrieren': '''
        <svg width="22.494" height="21.081" version="1.1" xml:space="preserve" xmlns="http://www.w3.org/2000/svg">
            <g transform="matrix(1.5451 0 0 1.5451 -12.361 -12.659)" style="stroke-width:.71191;stroke:{htmlcolor}">
                <path
                    d="m13.979 11.935a2.2371 2.2371 0 01-2.2371 2.2371 2.2371 2.2371 0 01-2.2371-2.2371 2.2371 2.2371 0 012.2371-2.2371 2.2371 2.2371 0 012.2371 2.2371z"
                    style="fill:none;opacity:.992;stroke-width:.71191;stroke:{htmlcolor}" />
                <g style="stroke-width:.71191;stroke:{htmlcolor}">
                    <path d="M 9.5049,11.935 H 8" style="fill:none;stroke-width:.71191;stroke:{htmlcolor}" />
                    <path d="m15.484 11.935h-1.5049" style="fill:none;stroke-width:.71191;stroke:{htmlcolor}" />
                    <path d="m11.742 9.6979v-1.5049" style="fill:none;stroke-width:.71191;stroke:{htmlcolor}" />
                    <path d="m11.742 15.677v-1.5049" style="fill:none;stroke-width:.71191;stroke:{htmlcolor}" />
                </g>
                <path
                    d="m12.932 11.935a1.19 1.19 0 01-1.19 1.19 1.19 1.19 0 01-1.19-1.19 1.19 1.19 0 011.19-1.19 1.19 1.19 0 011.19 1.19z"
                    style="fill:{htmlcolor};opacity:.992;stroke:none" />
            </g>
            <path
                d="m17.744 19.081h4.75v2h-6.75zm-12.5 2-2.125-2.125c-.38332-.38332-.57918-.85832-.5875-1.425-.0083-.56668.17917-1.05.5625-1.45l11-11.4c.38332-.4.85418-.6 1.4125-.6s1.0292.19167 1.4125.575l4.975 4.975c.38332.38332.575.85832.575 1.425s-.19167 1.0417-.575 1.425l-8.4 8.6zm7.4-2 5.6938-5.8938-4.95-4.95-8.8938 9.2438 1.6 1.6z"
                style="stroke-width:.025" fill="{htmlcolor}"/>
        </svg>''',
    'undo': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 7,2 2,5 7,8 V 6 H 10 C 11.68,6 13,7.321 13,9 13,10.679 11.68,12 10,12 H 5 V 14 H 10 C 12.75,14 15,11.753 15,9 15,6.247 12.75,4 10,4 H 7 Z"/>
        </svg>''',
    'redo': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 9,2 14,5 9,8 V 6 H 6 C 4.32,6 3,7.321 3,9 3,10.679 4.32,12 6,12 H 11 V 14 H 6 C 3.25,14 1,11.753 1,9 1,6.247 3.25,4 6,4 H 9 Z"/>
        </svg>''',
    'save': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="{htmlcolor}">
            <path d="M0 0h24v24H0V0z" fill="none" />
            <path
                d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm2 16H5V5h11.17L19 7.83V19zm-7-7c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3zM6 6h9v4H6z" />
        </svg>''',
    'open': '''
        <svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="{htmlcolor}">
            <rect fill="none" height="24" width="24" />
            <path d="M15,22H6c-1.1,0-2-0.9-2-2V4c0-1.1,0.9-2,2-2h8l6,6v6h-2V9h-5V4H6v16h9V22z M19,21.66l0-2.24l2.95,2.95l1.41-1.41L20.41,18 h2.24v-2H17v5.66H19z" />
        </svg>''',
    'prefs': '''
        <svg width="24px" height="24px" fill="{htmlcolor}" version="1.1" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 0h24v24H0V0z" fill="none"/>
            <path d="m19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.09-.16-.26-.25-.44-.25-.06 0-.12.01-.17.03l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65c-.03-.24-.24-.42-.49-.42h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.06-.02-.12-.03-.18-.03-.17 0-.34.09-.43.25l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.09.16.26.25.44.25.06 0 .12-.01.17-.03l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.06.02.12.03.18.03.17 0 .34-.09.43-.25l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zm-1.98-1.71c.04.31.05.52.05.73s-.02.43-.05.73l-.14 1.13.89.7 1.08.84-.7 1.21-1.27-.51-1.04-.42-.9.68c-.43.32-.84.56-1.25.73l-1.06.43-.16 1.13-.2 1.35h-1.4l-.19-1.35-.16-1.13-1.06-.43c-.43-.18-.83-.41-1.23-.71l-.91-.7-1.06.43-1.27.51-.7-1.21 1.08-.84.89-.7-.14-1.13c-.03-.31-.05-.54-.05-.74s.02-.43.05-.73l.14-1.13-.89-.7-1.08-.84.7-1.21 1.27.51 1.04.42.9-.68c.43-.32.84-.56 1.25-.73l1.06-.43.16-1.13.2-1.35h1.39l.19 1.35.16 1.13 1.06.43c.43.18.83.41 1.23.71l.91.7 1.06-.43 1.27-.51.7 1.21-1.07.85-.89.7.14 1.13zm-5.45-3.27c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>
        </svg>''',
    'zoom-in': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 3,2 C 2.45,2 2,2.446 2,3 V 13 C 2,13.554 2.45,14 3,14 H 13 C 13.55,14 14,13.554 14,13 V 3 C 14,2.446 13.55,2 13,2 Z M 7,5 H 9 V 7 H 11 V 9 H 9 V 11 H 7 V 9 H 5 V 7 H 7 Z"/>
        </svg>''',
    'zoom-out': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 3,2 C 2.45,2 2,2.446 2,3 V 13 C 2,13.554 2.45,14 3,14 H 13 C 13.55,14 14,13.554 14,13 V 3 C 14,2.446 13.55,2 13,2 Z M 5,7 H 11 V 9 H 5 Z"/>
        </svg>''',
    'zoom-original': '''
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" version="1.1">
            <path style="fill:{htmlcolor}" d="M 3,2 C 2.45,2 2,2.446 2,3 V 13 C 2,13.554 2.45,14 3,14 H 13 C 13.55,14 14,13.554 14,13 V 3 C 14,2.446 13.55,2 13,2 Z M 7,5 H 9 V 11 H 7 V 7 H 6 V 6 C 6,6 7,6 7,5 Z"/>
        </svg>''',
    'edit': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="m11.899 13.314-4.2426-4.2426-1.4142 2.8284-4.2426-9.8995 9.8995 4.2426-2.8284 1.4142 4.2426 4.2426z"/>
        </svg>''',
    'delete': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor}" d="M 3.5,2 2,3.5 6.5,8 2,12.5 3.5,14 8,9.5 12.5,14 14,12.5 9.5000001,8 14,3.5 12.5,2 8,6.5 Z"/>
        </svg>''',
    'copy': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:{htmlcolor};opacity:.992;stroke-dasharray:2.6054, 1.3027;stroke-dashoffset:.45594;stroke-linejoin:round;stroke-width:.65135" d="m2.0762.61816v11.193h3.375v3.5703h8.4727v-11.193h-3.375v-3.5703zm1.3184 1.3184h5.8359v2.252h-3.7793v6.3047h-2.0566zm3.375 3.5703h5.8359v8.5566h-5.8359z"/>
        </svg>''',
    'trash': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:none;stroke-width:1px;stroke:{htmlcolor}" d="m10 7.5-.5 5m-2-5v5m-2.5-5 .5 5m-3-7.5 1 10h8l1-10z"/>
            <path style="fill:none;stroke-width:1px;stroke:{htmlcolor}" d="m5 3.5.5-2h4l.5 2m-8 0h11"/>
        </svg>''',
    'geodreieck': '''
        <svg id="svg6" width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path style="fill:none;stroke-width:1.0352px;stroke:{htmlcolor}" id="halbkreis" d="m11.13 4.908a4.3996 4.3996 0 01-.0125 6.2213 4.3996 4.3996 0 01-6.2213-.01135"/>
            <path style="fill:none;stroke-width:1.0352px;stroke:{htmlcolor}" id="dreieck" d="m1.5425 14.482h12.94v-12.94z"/>
        </svg>''',
    'doublearrow': '''<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 -960 960 960" width="24" fill="{htmlcolor}">
            <path d="m242-200 200-280-200-280h98l200 280-200 280h-98Zm238 0 200-280-200-280h98l200 280-200 280h-98Z" />
        </svg>''',
    'toolbarbutton': '''<svg width="11.213mm" height="11.213mm" version="1.1" viewBox="0 0 11.213 11.213" xml:space="preserve"
            xmlns="http://www.w3.org/2000/svg" fill="{htmlcolor}">
            <g transform="translate(-6.6934 -6.3154)">
                <path
                    d="m7.7856 6.3154-1.0922.98974 4.184 4.6164-4.184 4.6176 1.0922.98974 5.0809-5.6073zm5.04 0-1.0922.98974 4.184 4.6164-4.184 4.6176 1.0922.98974 5.0809-5.6073z"
                    style="fill-rule:evenodd;opacity:.992;stroke-width:.29104" />
            </g>
        </svg>''',
    'oszli': '''
        <svg width="281" height="291" version="1.1" viewBox="0 0 281 291" xmlns="http://www.w3.org/2000/svg">
            <path d="m281 0v291h-281v-291z" style="fill:#f9b200"/>
            <g transform="translate(0,-2)" style="fill:#004171">
                <path d="m226 161v90h31v-90z"/>
                <path d="m131 130v121h82v-23h-50v-98z"/>
                <path d="m226 123v23h31v-23z"/>
            </g>
            <g transform="translate(0,-2)" style="fill:#ffffff">
                <path transform="scale(5.2083)" d="m28.992 5.4336c-1.1789.2208-2.2012.51865-2.998 1.4863-1.8317 2.2272-1.5977 7.9252 3.3828 8.2305 5.1014.31296 5.8765-5.9562 3.584-8.3965-.98112-1.0445-2.5806-1.4278-3.9688-1.3203zm.51758 1.4961c1.9444-.04557 2.7929 1.5729 2.7441 3.6309-.0288 1.1213-.38511 2.4473-1.5371 2.9004-.38016.14976-.93088.18131-1.3398.16211-3.1968-.144-3.2655-5.234-.76953-6.5684.32304-.078.62457-.11849.90234-.125z"/>
                <path d="m225 29v8h22l-12.72 18c-6.58 9.4-10.24 11.17-10.28 23h34v-7h-23l21.15-33 .85-9z"/>
                <path d="m213.01 30.72c-3.06-3.93-20.33-4.23-24.94 5.32-.77 1.6-1.38 4.19-1.62 5.96-1.99 14.62 16.18 13.98 19.47 21.1 1.52 3.29-1.11 6.01-3.94 7.29-4.35 1.97-9.72-.01-13.97-1.39-.55 2.27-1.51 5.33 0 7.44 1.68 2.3 6.4 2.49 8.99 2.54 7.91.16 16.98-1.3 19.67-9.98 2.78-8.98-1.93-14.56-9.67-18.36-3.47-1.7-11.16-4.48-10.04-9.55 1.58-7.08 12.22-4.48 17.04-4.09-.02-1.84.18-4.77-.99-6.28z"/>
            </g>
        </svg>''',
    'help': '''
        <svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" width="24px" height="24px" viewBox="0 0 24 24" style="enable-background:new 0 0 24 24;" xml:space="preserve">
            <g id="Icons" style="fill:{htmlcolor}">
                <g id="help">
                    <path id="circle" style="fill-rule:evenodd;clip-rule:evenodd;" d="M12.001,2.085c-5.478,0-9.916,4.438-9.916,9.916
                        c0,5.476,4.438,9.914,9.916,9.914c5.476,0,9.914-4.438,9.914-9.914C21.915,6.523,17.477,2.085,12.001,2.085z M12.002,20.085
                        c-4.465,0-8.084-3.619-8.084-8.083c0-4.465,3.619-8.084,8.084-8.084c4.464,0,8.083,3.619,8.083,8.084
                        C20.085,16.466,16.466,20.085,12.002,20.085z"/>
                    <g id="question_mark">
                        <path id="top" style="fill-rule:evenodd;clip-rule:evenodd;" d="M11.766,6.688c-2.5,0-3.219,2.188-3.219,2.188l1.411,0.854
                            c0,0,0.298-0.791,0.901-1.229c0.516-0.375,1.625-0.625,2.219,0.125c0.701,0.885-0.17,1.587-1.078,2.719
                            C11.047,12.531,11,15,11,15h1.969c0,0,0.135-2.318,1.041-3.381c0.603-0.707,1.443-1.338,1.443-2.494S14.266,6.688,11.766,6.688z"
                            />
                        <rect id="bottom" x="11" y="16" style="fill-rule:evenodd;clip-rule:evenodd;" width="2" height="2"/>
                    </g>
                </g>
            </g>
        </svg>''',
    'dark': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m10 9h-8v-6h8z" style="fill:none;stroke:{htmlcolor}"/>
            <path d="m14 13h-8v-6h8z" style="fill:{htmlcolor};stroke-width:1px;stroke:{htmlcolor}"/>
        </svg>''',
    'linienpapier': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m2  2h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  6h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2 10h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2 14h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
        </svg>''',
    'karopapier': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m2  2h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  6h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2 10h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2 14h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m6  2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m10 2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m14 2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
        </svg>''',
    'logpapier': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m2  2h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  4h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  8h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2 14h12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m14 2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m12 2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m8  2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m2  2v12" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
        </svg>''',
    'fromclipboard': '''
        <svg width="16" height="16" version="1.1" xmlns="http://www.w3.org/2000/svg">
            <path d="m1 1h9v10h-9v-10" style="fill:none;stroke-linecap:square;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m1 7 3-3 6 4" style="fill:none;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m13 15v-4" style="fill:none;stroke-width:1px;stroke:{htmlcolor}"/>
            <path d="m11 13h4" style="fill:none;stroke-width:1px;stroke:{htmlcolor}"/>
        </svg>''',
    'customcolor': '''
        <svg
           width="16"
           height="16"
           version="1.1"
           xmlns="http://www.w3.org/2000/svg"
           xmlns:svg="http://www.w3.org/2000/svg">
          <defs
             id="defs8" />
          <rect
             style="fill:#ffcc00;stroke-width:2.923;stroke-linejoin:round;stroke-opacity:0"
             width="6"
             height="5"
             x="1.5"
             y="2.5" />
          <rect
             style="fill:#ff00cc;stroke-width:2.923;stroke-linejoin:round;stroke-opacity:0"
             width="5.9934287"
             height="5"
             x="8.5065708"
             y="2.5" />
          <rect
             style="fill:#2ad4ff;stroke-width:2.923;stroke-linejoin:round;stroke-opacity:0"
             width="6"
             height="4.9934287"
             x="1.5"
             y="8.5065708" />
          <rect
             style="fill:#8dd35f;stroke-width:2.923;stroke-linejoin:round;stroke-opacity:0"
             width="5.9934292"
             height="4.9934292"
             x="8.5065708"
             y="8.5065708" />
        </svg>
    '''
}
