# main code
import sys
import time
import numpy as np
from datetime import datetime

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QTableWidget, QTableWidgetItem
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import pyqtSlot
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib import dates

# my libraries
import db
from psuedoSensor import PseudoSensor

# init database
session = db.init_session()

# alarm limits
temp_min_limit = -5.0
temp_max_limit = 80.0
humid_min_limit = 10.0
humid_max_limit = 80.0

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        # graphs of temperature and humidity - refresh on interval
        dynamic_canvas_temps = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(dynamic_canvas_temps)
        # self.addToolBar(QtCore.Qt.BottomToolBarArea,
        #                 NavigationToolbar(dynamic_canvas_temps, self))

        self.dynamic_ax_temps = dynamic_canvas_temps.figure.subplots()
        self.temp_timer = dynamic_canvas_temps.new_timer(
            100, [(self.update_canvas_temps, (), {}),])
        self.temp_timer.start()

        dynamic_canvas_humid = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(dynamic_canvas_humid)
        # self.addToolBar(QtCore.Qt.BottomToolBarArea,
        #                 NavigationToolbar(dynamic_canvas_humid, self))

        self.dynamic_ax_humid = dynamic_canvas_humid.figure.subplots()
        self.humid_timer = dynamic_canvas_humid.new_timer(
            150, [(self.update_canvas_humid, (), {})])
        self.humid_timer.start()

        # table of current temp/humidity
        self.current_table = QTableWidget()
        self.current_table.setRowCount(1)
        self.current_table.setColumnCount(2)
        self.current_table.setHorizontalHeaderLabels(["Temperature (F)", "Humidity (%)"])
        self.current_table.setItem(0,0, QTableWidgetItem("0.0"))
        self.current_table.setItem(0,1, QTableWidgetItem("0.0"))
        layout.addWidget(self.current_table)

        single_button = QPushButton('Sample Data (single)', self)
        layout.addWidget(single_button)
        single_button.setToolTip('Samples one data point')
        single_button.move(100,70)
        single_button.clicked.connect(self.single_sample)

        multi_button = QPushButton('Sample Data (10 Times)', self)
        layout.addWidget(multi_button)
        multi_button.setToolTip('Samples 10 data points')
        multi_button.move(100,70)
        multi_button.clicked.connect(self.multi_sample)

        # table of calculated metrics
        self.metrics_table = QTableWidget()
        self.metrics_table.setRowCount(1)
        self.metrics_table.setColumnCount(7)
        self.metrics_table.setHorizontalHeaderLabels(["Total Samples", "Min Temperature (F)", "Min Humidity (%)", "Max Temperature (F)", "Max Humidity (%)", "Avg Temperature (F)", "Avg Humidity (%)"])
        self.metrics_table.setItem(0,0, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,1, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,2, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,3, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,4, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,5, QTableWidgetItem("0.0"))
        self.metrics_table.setItem(0,6, QTableWidgetItem("0.0"))
        layout.addWidget(self.metrics_table)

        calc_button = QPushButton('Calculate Metrics', self)
        layout.addWidget(calc_button)
        calc_button.setToolTip('Calculates metrics')
        calc_button.move(100,70)
        calc_button.clicked.connect(self.calc_metrics)

    # def _update_canvas(self):
    #     self._dynamic_ax.clear()
    #     t = np.linspace(0, 10, 101)
    #     # Shift the sinusoid as a function of time.
    #     self._dynamic_ax.plot(t, np.sin(t + time.time()))
    #     self._dynamic_ax.figure.canvas.draw()
    #     return

    def update_canvas_temps(self):
        temp_list, temp_times = db.get_all_temps(session, "f")
        humid_list, humid_times = db.get_all_humids(session)
        # t_times = dates.date2num(temp_times)
        # h_times = dates.date2num(humid_times)
        self.dynamic_ax_temps.clear()
        self.dynamic_ax_temps.set_title("Temperature vs Time")
        self.dynamic_ax_temps.set_xlabel("Time")
        self.dynamic_ax_temps.set_ylabel("Temp (F)")
        self.dynamic_ax_temps.plot(temp_times, temp_list, label = "Measured")
        self.dynamic_ax_temps.plot(temp_times, temp_max_limit, '--', label = "Max Temp")
        self.dynamic_ax_temps.plot(temp_times, temp_min_limit, '--', label = "Min Temp")
        self.dynamic_ax_temps.figure.canvas.draw()
        return

    def update_canvas_humid(self):
        humid_list, humid_times = db.get_all_humids(session)
        self.dynamic_ax_humid.clear()
        self.dynamic_ax_humid.set_title("Humidity vs Time")
        self.dynamic_ax_humid.set_xlabel("Time")
        self.dynamic_ax_humid.set_ylabel("Humidity (%)")
        self.dynamic_ax_humid.plot(humid_times, humid_list, label = "Measured")
        self.dynamic_ax_humid.plot(humid_times, humid_max_limit, '--', label = "Max Humidity")
        self.dynamic_ax_humid.plot(humid_times, humid_min_limit, '--', label = "Min Humidity")
        self.dynamic_ax_humid.figure.canvas.draw()
        return

    @pyqtSlot()
    def single_sample(self):
        h,t = self.sample_data()
        self.current_table.setItem(0,0, QTableWidgetItem(str(t)))
        self.current_table.setItem(0,1, QTableWidgetItem(str(h)))
        print('sample', 'temp:', t, 'humidity:', h)
        return

    @pyqtSlot()
    def multi_sample(self):
        max = 10
        for i in range(max):
            h,t = self.sample_data()
            self.current_table.setItem(0,0, QTableWidgetItem(str(t)))
            self.current_table.setItem(0,1, QTableWidgetItem(str(h)))
            print('sample', i, 'temp:', t, 'humidity:', h)
            time.sleep(1)
        return

    @pyqtSlot()
    def calc_metrics(self):
        temp_list, temp_times = db.get_all_temps(session, "f")
        humid_list, humid_times = db.get_all_humids(session)
        # set total samples
        self.metrics_table.setItem(0,0, QTableWidgetItem(str(len(temp_list))))
        # min temp
        self.metrics_table.setItem(0,1, QTableWidgetItem(str(min(temp_list))))
        # min humidity
        self.metrics_table.setItem(0,2, QTableWidgetItem(str(min(humid_list))))
        # max temp
        self.metrics_table.setItem(0,3, QTableWidgetItem(str(max(temp_list))))
        # max humidity
        self.metrics_table.setItem(0,4, QTableWidgetItem(str(max(temp_list))))
        # avg temp
        self.metrics_table.setItem(0,5, QTableWidgetItem(str(sum(temp_list)/len(temp_list))))
        # avg humidity
        self.metrics_table.setItem(0,6, QTableWidgetItem(str(sum(humid_list)/len(humid_list))))
        return

    # get sample of data from pseudo sensor
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