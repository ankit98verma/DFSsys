from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class main_gui(QWidget):
    def __init__(self, data, parent=None):
        QWidget.__init__(self, parent)
        self.data = data
        self.prev_data = data.copy()
        self.thread = Worker()
        self.i = 0
        self.labels = []
        layout = QGridLayout()
        r = 0
        for k, v in self.data.items():
            label = QLabel(self.tr("%s:" % k))
            labeli = QLabel(self.tr("%s" % str(v)))
            label.setFrameShape(QFrame.Panel)
            label.setLineWidth(1)
            label.setFont(QtGui.QFont('Times', 10))

            labeli.setFrameShape(QFrame.Panel)
            labeli.setLineWidth(1)
            labeli.setFont(QtGui.QFont('Times', 10))

            layout.addWidget(label, r, 0)
            layout.addWidget(labeli, r, 1)
            r += 1
            self.labels.append(labeli)
        layout.setContentsMargins(10, 10, 10, 10)
        self.thread.finished.connect(self.updateUi)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Simple Threading Example"))

    def updateUi(self):
        i = 0
        for k, v in self.data.items():
            prev_d = self.prev_data[k]
            label = self.labels[i]
            label.setText(self.tr("%s" % str(v)))
            if prev_d != v:
                label.setStyleSheet('color: red')
            else:
                label.setStyleSheet('color: black')
            i += 1
        self.prev_data = self.data.copy()

    def set_data(self, data):
        self.data = data


class Worker(QThread):
    output = pyqtSignal()

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        # Note: This is never called directly. It is called by Qt once the
        # thread environment has been set up.
        pass

