# main code
import sys
import time
import numpy as np
from datetime import datetime

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTableWidget
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import pyqtSlot
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

# my libraries
import db
from psuedoSensor import PseudoSensor

# init database
session = db.init_session()

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(static_canvas)
        self.addToolBar(NavigationToolbar(static_canvas, self))

        dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(dynamic_canvas)
        self.addToolBar(QtCore.Qt.BottomToolBarArea,
                        NavigationToolbar(dynamic_canvas, self))

        self._static_ax = static_canvas.figure.subplots()
        t = np.linspace(0, 10, 501)
        self._static_ax.plot(t, np.tan(t), ".")

        self._dynamic_ax = dynamic_canvas.figure.subplots()
        self._timer = dynamic_canvas.new_timer(
            100, [(self._update_canvas, (), {})])
        self._timer.start()

        self.current_table = QTableWidget()
        self.current_table.setRowCount(1)
        self.current_table.setColumnCount(2)
        self.current_table.setHorizontalHeaderLabels(["F", "H"])
        layout.addWidget(self.current_table)

        button = QPushButton('Sample Data (single)', self)
        layout.addWidget(button)
        button.setToolTip('Samples one data point')
        button.move(100,70)
        button.clicked.connect(self.single_sample)

        

    def _update_canvas(self):
        self._dynamic_ax.clear()
        t = np.linspace(0, 10, 101)
        # Shift the sinusoid as a function of time.
        self._dynamic_ax.plot(t, np.sin(t + time.time()))
        self._dynamic_ax.figure.canvas.draw()

    @pyqtSlot()
    def single_sample(self):
        h,t = self.sample_data()
        self.current_table.item(1, 1).setText(t)
        self.current_table.item(1, 2).setText(h)
        print('PyQt5 button click')

    def sample_data(self):
        ps = PseudoSensor()
        h,temp_f = ps.generate_values()
        temp_c = (temp_f - 32) * 5.0/9.0
        now = datetime.now()
        db.add_temp(session, temp_f, temp_c, now)
        db.add_humidity(session, h, now)
        return h, temp_f


if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = ApplicationWindow()
    app.show()
    qapp.exec_()
    # close db connection
    db.close(session)