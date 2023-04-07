import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import QtWidgets, QtCore
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class C3dView(QMainWindow):

    def __init__(self, dicom_folder, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Volume Rendering Viewer')
        self.setFixedSize(1000, 600)

        self.dicom_folder = dicom_folder

        self.init_ui()

    def init_ui(self):
        self.frame = QtWidgets.QFrame(self)
        self.setCentralWidget(self.frame)
        self.frame.setLayout(QtWidgets.QVBoxLayout())

        self.vtk_widget = QVTKRenderWindowInteractor(self.frame)
        self.frame.layout().addWidget(self.vtk_widget)

        self.ren = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)

        self.iren = self.vtk_widget.GetRenderWindow().GetInteractor()

        self.volume = self.load_volume(self.dicom_folder)
        self.ren.AddVolume(self.volume)

        self.iren.Initialize()

        self.create_controls()

    def load_volume(self, dicom_folder):
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName(dicom_folder)
        reader.Update()

        self.volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        self.volume_mapper.SetInputConnection(reader.GetOutputPort())

        self.color_func = vtk.vtkColorTransferFunction()
        self.color_func.AddRGBPoint(0, 0, 0, 0)
        self.color_func.AddRGBPoint(500, 1, 0, 0)
        self.color_func.AddRGBPoint(1000, 0, 1, 0)
        self.color_func.AddRGBPoint(1500, 0, 0, 1)

        self.opacity_func = vtk.vtkPiecewiseFunction()
        self.opacity_func.AddPoint(0, 0)
        self.opacity_func.AddPoint(500, 0)
        self.opacity_func.AddPoint(1000, 0.3)
        self.opacity_func.AddPoint(1500, 0.6)

        self.volume_property = vtk.vtkVolumeProperty()
        self.volume_property.SetColor(self.color_func)
        self.volume_property.SetScalarOpacity(self.opacity_func)
        self.volume_property.ShadeOn()

        volume = vtk.vtkVolume()
        volume.SetMapper(self.volume_mapper)
        volume.SetProperty(self.volume_property)

        return volume

    def create_controls(self):
        self.slider_frame = QtWidgets.QFrame(self.frame)
        self.slider_frame.setLayout(QtWidgets.QHBoxLayout())
        self.frame.layout().addWidget(self.slider_frame)

        self.opacity_label = QtWidgets.QLabel("Opacity: ")
        self.slider_frame.layout().addWidget(self.opacity_label)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(30)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        self.slider_frame.layout().addWidget(self.opacity_slider)

        self.opacity_label = QtWidgets.QLabel("Color: ")
        self.slider_frame.layout().addWidget(self.opacity_label)
        self.color_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.color_slider.setMinimum(0)
        self.color_slider.setMaximum(100)
        self.color_slider.setValue(50)
        self.color_slider.valueChanged.connect(self.update_color)
        self.slider_frame.layout().addWidget(self.color_slider)

        self.opacity_label = QtWidgets.QLabel("Thresholding: ")
        self.slider_frame.layout().addWidget(self.opacity_label)
        self.threshold_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(2000)
        self.threshold_slider.setValue(500)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        self.slider_frame.layout().addWidget(self.threshold_slider)

    def update_opacity(self, value):
        opacity = value / 100
        self.opacity_func.RemoveAllPoints()
        self.opacity_func.AddPoint(0, 0)
        self.opacity_func.AddPoint(500, 0)
        self.opacity_func.AddPoint(1000, opacity)
        self.opacity_func.AddPoint(1500, opacity * 2)
        self.volume_property.SetScalarOpacity(self.opacity_func)
        self.iren.Render()

    def update_color(self, value):
        color = value / 100
        self.color_func.RemoveAllPoints()
        self.color_func.AddRGBPoint(0, 0, 0, 0)
        self.color_func.AddRGBPoint(500, 1 - color, 0, color)
        self.color_func.AddRGBPoint(1000, 0, 1 - color, color)
        self.color_func.AddRGBPoint(1500, color, color, 1 - color)
        self.volume_property.SetColor(self.color_func)
        self.iren.Render()

    def update_threshold(self, value):
        threshold = value
        self.opacity_func.RemoveAllPoints()
        self.opacity_func.AddPoint(0, 0)
        self.opacity_func.AddPoint(threshold, 0)
        self.opacity_func.AddPoint(threshold + 500, self.opacity_slider.value() / 100)
        self.opacity_func.AddPoint(1500, (self.opacity_slider.value() / 100) * 2)
        self.volume_property.SetScalarOpacity(self.opacity_func)
        self.iren.Render()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = C3dView()
    ex.show()
    sys.exit(app.exec_())
