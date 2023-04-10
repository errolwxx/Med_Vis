from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
import numpy as np
from shapely.geometry import Polygon
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class QPaintLabel3(QLabel):

    mpsignal = pyqtSignal(str)

    def __init__(self, parent):
        super(QLabel, self).__init__(parent)

        self.setMinimumSize(1, 1)
        self.setMouseTracking(False)
        self.image = None
        self.processedImage = None
        self.imgr, self.imgc = None, None
        self.imgpos_x, self.imgpos_y = None, None
        self.pos_x = 20
        self.pos_y = 20
        self.imgr, self.imgc = None, None
        self.pos_xy = []
        self.crosscenter = [0, 0]
        self.mouseclicked = None
        self.sliceclick = False
        self.type = 'general'
        self.slice_loc = [0, 0, 0]
        self.slice_loc_restore = [0, 0, 0]
        self.mousein = False
        self.points = QPolygon()
        self.resolution = []
        self.paintMode = "normal"
        self.ROI = QPainterPath()
        self.path = QPainterPath()
        self.closedPath = QPainterPath()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.paintMode == "m_ROI": super().mouseMoveEvent(event)
        if not self.mousein:
            self.slice_loc_restore = self.slice_loc.copy()
            self.mousein = True

        self.imgpos_x = int(event.x() * self.imgc / self.width())
        self.imgpos_y = int(event.y() * self.imgr / self.height())

        if self.type == 'axial':
            self.slice_loc[0:2] = self.imgpos_x, self.imgpos_y
        elif self.type == 'sagittal':
            self.slice_loc[1:3] = self.imgpos_x, self.imgr - self.imgpos_y
        elif self.type == 'coronal':
            self.slice_loc[0] = self.imgpos_x
            self.slice_loc[2] = self.imgr - self.imgpos_y
        else:
            pass
        if self.paintMode == "m_ROI":
            if event.buttons() & Qt.LeftButton:
                self.path.lineTo(event.pos())
                # self.ROIVertices.append((self.imgpos_x, self.imgpos_y))
        self.update()

    def leaveEvent(self, event):
        self.mousein = False
        self.slice_loc = self.slice_loc_restore
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if self.paintMode == "normal":
            self.crosscenter[0] = event.x()
            self.crosscenter[1] = event.y()
            self.mpsignal.emit(self.type)
            self.slice_loc_restore = self.slice_loc.copy()
        elif self.paintMode == "m_length":
            if self.points.count() > 1: self.points, self.pos_xy = QPolygon(), []
            self.points << event.pos()
            if self.type == 'axial':
                # x, y, resx, resy = self.slice_loc[0], self.slice_loc[1], self.resolution[0], self.resolution[1]
                x, y = self.slice_loc[0], self.slice_loc[1]
            if self.type == 'sagittal':
                x, y = self.slice_loc[1], self.slice_loc[2]
            if self.type == 'coronal':
                x, y = self.slice_loc[0], self.slice_loc[2]
            self.pos_xy.append((x, y))
        else:
            if event.button() == Qt.LeftButton:
                self.path = QPainterPath()
                self.ROI = QPainterPath()
                self.path.moveTo(event.pos())
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.paintMode in ["normal", "m_length"]:
            pass
        else:
            if event.button() == Qt.LeftButton:
                self.path.lineTo(event.pos())
                # self.path.closeSubpath()
                self.closedPath = QPainterPath(self.path)
                self.closedPath.closeSubpath()
                self.split_polygon(self.closedPath)
                self.path = QPainterPath()
                self.update()
                # self.split_polygon(self.closedPath)

    def split_polygon(self, path):
        polygon = Polygon([(p.x(), p.y()) for p in self.closedPath.toFillPolygon()])
        if not polygon.is_valid:
            parts = polygon.buffer(1)
            try: parts = list(parts.geoms)
            except: parts = [polygon]
        else: parts = [polygon]
        areas = [p.area for p in parts]
        part = parts[areas.index(max(areas))]
        points = [QPointF(x, y) for x, y in part.exterior.coords]
        self.ROI.addPolygon(QPolygonF(points))

    def display_image(self, window=1):
        self.imgr, self.imgc = self.processedImage.shape[0:2]
        qformat = QImage.Format_Indexed8
        if len(self.processedImage.shape) == 3:  # rows[0], cols[1], channels[2]
            if (self.processedImage.shape[2]) == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        img = QImage(self.processedImage, self.processedImage.shape[1], self.processedImage.shape[0],
                     self.processedImage.strides[0], qformat)
        img = img.rgbSwapped()
        w, h = self.width(), self.height()
        if window == 1:
            self.setScaledContents(True)
            backlash = self.lineWidth() * 2
            self.setPixmap(QPixmap.fromImage(img).scaled(w - backlash, h - backlash, Qt.IgnoreAspectRatio))
            self.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        loc = QFont()
        loc.setPixelSize(10)
        loc.setBold(True)
        loc.setItalic(True)
        loc.setPointSize(15)
        if self.pixmap():
            painter = QPainter(self)
            pixmap = self.pixmap()
            painter.drawPixmap(self.rect(), pixmap)

            painter.setPen(QPen(Qt.magenta, 10))
            painter.setFont(loc)
            painter.drawText(5, self.height() - 5, 'x = %3d  ,  y = %3d  ,  z = %3d'
                             % (self.slice_loc[0], self.slice_loc[1], self.slice_loc[2]))

            if self.paintMode == 'normal':
                if self.type == 'axial':
                    painter.setPen(QPen(Qt.red, 3))
                    painter.drawLine(self.crosscenter[0], 0, self.crosscenter[0], self.height())
                    painter.setPen(QPen(Qt.cyan, 3))
                    painter.drawLine(0, self.crosscenter[1], self.width(), self.crosscenter[1])
                    painter.setPen(QPen(Qt.yellow, 3))
                    painter.drawPoint(self.crosscenter[0], self.crosscenter[1])

                elif self.type == 'sagittal':
                    painter.setPen(QPen(Qt.cyan, 3))
                    painter.drawLine(self.crosscenter[0], 0, self.crosscenter[0], self.height())
                    painter.setPen(QPen(Qt.yellow, 3))
                    painter.drawLine(0, self.crosscenter[1], self.width(), self.crosscenter[1])
                    painter.setPen(QPen(Qt.red, 3))
                    painter.drawPoint(self.crosscenter[0], self.crosscenter[1])

                elif self.type == 'coronal':
                    painter.setPen(QPen(Qt.red, 3))
                    painter.drawLine(self.crosscenter[0], 0, self.crosscenter[0], self.height())
                    painter.setPen(QPen(Qt.yellow, 3))
                    painter.drawLine(0, self.crosscenter[1], self.width(), self.crosscenter[1])
                    painter.setPen(QPen(Qt.cyan, 3))
                    painter.drawPoint(self.crosscenter[0], self.crosscenter[1])
                else: pass
            elif self.paintMode == "m_length":
                for i in range(self.points.count()):
                # painter.drawEllipse(self.points.point(i), 5, 5)
                    painter.setPen(QPen(Qt.magenta, 10))
                    painter.drawPoint(self.points.point(i))
                    if i: 
                        # painter.setPen(QPen(Qt.white, 3))
                        painter.setPen(QPen(Qt.white, 1, Qt.DotLine))
                        painter.drawText(5, self.height() - 40, 'b: (%3d, %3d)'
                                        % (self.pos_xy[1][0], self.pos_xy[1][1]))
                        # print(self.resolution, type(self.resolution[0]))
                        painter.drawText(5, self.height() - 20, 'Length: %3d mm' % self.cal_dist(self.pos_xy[0], self.pos_xy[1]))
                        painter.drawLine(self.points.point(0), self.points.point(1))
                    else:
                        painter.setPen(QPen(Qt.white, 3))
                        painter.drawText(5, self.height() - 60, 'a: (%3d, %3d)'
                                        % (self.pos_xy[0][0], self.pos_xy[0][1]))
            else:
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.drawPath(self.path)
                painter.setPen(QPen(QColor(0, 255, 0), 2, Qt.DotLine))
                if not self.ROI.isEmpty():
                    painter.drawText(5, self.height() - 20, 'Area: %3d mm\u00B2' % self.cal_area(self.ROI))
                painter.drawPolygon(self.ROI.toFillPolygon())
                    
    def cal_dist(self, a, b):
        return np.sqrt(((a[0]-b[0])*self.resolution[0])**2 + ((a[1]-b[1])*self.resolution[1])**2)

    def cal_area(self, roi):
        return Polygon([(p.x() * self.resolution[0] * self.imgc / self.width(),
                         p.y() * self.resolution[1] * self.imgr / self.height()) for p in roi.toFillPolygon()]).area

def linear_convert(img):
    convert_scale = 255.0 / (np.max(img) - np.min(img))
    converted_img = convert_scale*img-(convert_scale*np.min(img))
    return converted_img