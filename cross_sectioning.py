import sys
import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QAction, QVBoxLayout, QWidget, QSpinBox, QLabel, QHBoxLayout, QPushButton

class STLViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.plane_height = 0  # Default plane height
        self.stl_mesh = None # stl empty before file selection
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Cros Sectioning STL') # App Name

        #3d canvas for 3d object
        self.canvas_3d = FigureCanvas(plt.Figure())
        self.ax_3d = self.canvas_3d.figure.add_subplot(111, projection='3d')
        
        #2d canvas for 2d cros_section
        self.canvas_2d = FigureCanvas(plt.Figure())
        self.ax_2d = self.canvas_2d.figure.add_subplot(111)
        self.ax_2d.set_aspect('equal')
        self.ax_2d.set_xlabel('X')
        self.ax_2d.set_ylabel('Y')

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        control_layout = QHBoxLayout()
        self.height_label = QLabel(f'Plane Height: {self.plane_height}')
        
        #spinbox for z axis (height) selection
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setValue(self.plane_height)
        self.height_spinbox.setRange(0, 100)
        
        #apply the selected height to the object for slicing
        self.apply_button = QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply_plane_height)

        control_layout.addWidget(self.height_label)
        control_layout.addWidget(self.height_spinbox)
        control_layout.addWidget(self.apply_button)

        layout.addLayout(control_layout)
        layout.addWidget(self.canvas_3d)
        layout.addWidget(self.canvas_2d)
        self.setCentralWidget(central_widget)

        #openfile for stl file selection
        openFile = QAction('Open STL File', self)
        openFile.triggered.connect(self.openFileDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        fileMenu.addAction(openFile)

    def apply_plane_height(self):
        self.plane_height = self.height_spinbox.value()
        self.height_label.setText(f'Plane Height: {self.plane_height}')
        if self.stl_mesh is not None:
            self.processSTL()

    def openFileDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open STL File", "", "STL Files (*.stl);;All Files (*)", options=options)
        if file_name:
            self.stl_mesh = mesh.Mesh.from_file(file_name)
            self.plot_3d_mesh()
            self.processSTL()

    def processSTL(self):
        plane_normal = np.array([0, 0, 1])
        plane_origin = np.array([0, 0, self.plane_height])
        cros_section_points = self.cros_section_mesh_for_plot(self.stl_mesh, plane_origin, plane_normal)
        self.visualize_cros_section(cros_section_points)

    def plane_line_intersection(self, plane_origin, plane_normal, point1, point2):
        plane_normal = np.array(plane_normal)
        plane_origin = np.array(plane_origin)
        point1 = np.array(point1)
        point2 = np.array(point2)

        line_vec = point2 - point1
        plane_to_point = plane_origin - point1
        dot = np.dot(plane_normal, line_vec)

        if np.abs(dot) < 1e-6:  # if the line is parallel to the plane
            return None

        t = np.dot(plane_normal, plane_to_point) / dot
        if 0 <= t <= 1:
            intersection_point = point1 + t * line_vec
            return intersection_point

        return None

    def cros_section_mesh_for_plot(self, stl_mesh, plane_origin, plane_normal):
        plane_normal = plane_normal / np.linalg.norm(plane_normal)
        intersection_points = []

        for triangle in stl_mesh.vectors:
            points = []
            for i in range(3):
                point1 = triangle[i]
                point2 = triangle[(i + 1) % 3]
                intersection = self.plane_line_intersection(plane_origin, plane_normal, point1, point2)
                if intersection is not None:
                    points.append(intersection)
            if len(points) == 2:
                intersection_points.append(points)

        return intersection_points

    def plot_3d_mesh(self):
        self.ax_3d.clear()
        self.ax_3d.add_collection3d(Poly3DCollection(self.stl_mesh.vectors, edgecolor='k'))
        scale = self.stl_mesh.points.flatten()
        self.ax_3d.auto_scale_xyz(scale, scale, scale)
        self.ax_3d.set_title('3D View of the STL File')
        self.canvas_3d.draw()

    def visualize_cros_section(self, cros_section_points):
        self.ax_2d.clear()
        self.ax_2d.set_aspect('equal')
        self.ax_2d.set_title('2D Cros Section of the 3D Object')
        self.ax_2d.set_xlabel('X')
        self.ax_2d.set_ylabel('Y')
        for edge in cros_section_points:
            x = [edge[0][0], edge[1][0]]
            y = [edge[0][1], edge[1][1]]
            self.ax_2d.plot(x, y, 'k-')
        self.canvas_2d.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = STLViewer()
    viewer.show()
    sys.exit(app.exec_())
