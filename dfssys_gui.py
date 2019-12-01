from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


# Disabling the warnings
# def handler(msg_type, msg_log_context, msg_string):
#     pass


# qInstallMessageHandler(handler)


class DFSsysGUI:

    def __init__(self, log_data, onlines_data):
        self.main_gui = main_gui(log_data)
        self.onlines_gui = onlines_gui(onlines_data)

    def trigger_guis(self, w):
        if w == 'all':
            self.main_gui.thread.start()
            self.onlines_gui.thread.start()
        else:
            if '-m' in w:
                self.main_gui.thread.start()
            if '-o' in w:
                self.onlines_gui.thread.start()

    def show_guis(self, w):
        if w == 'all':
            self.main_gui.show()
            self.onlines_gui.show()
        else:
            if '-m' in w:
                self.main_gui.show()
            if '-o' in w:
                self.onlines_gui.show()

    def close_guis(self):
        self.main_gui.do_close = True
        self.onlines_gui.do_close = True

        self.main_gui.close()
        self.onlines_gui.close()


class main_gui(QWidget):
    def __init__(self, data, parent=None):
        QWidget.__init__(self, parent)
        self.do_close = False
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
        self.setWindowTitle(self.tr("Log information"))

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

    def closeEvent(self, event):
        if self.do_close:
            super().closeEvent(event)
        else:
            event.ignore()
            self.hide()


class onlines_gui(QWidget):

    def __init__(self, online_data, parent=None):
        QWidget.__init__(self, parent)
        self.do_close = False
        self.data = online_data
        self.thread = Worker()
        self.i = 0
        self.labels = []
        self.layout = QGridLayout()
        label = QLabel(self.tr("IP Addr"))
        self.layout.addWidget(label, 0, 0)
        label = QLabel(self.tr("Alias"))
        self.layout.addWidget(label, 0, 1)
        label = QLabel(self.tr("Transmit rate"))
        self.layout.addWidget(label, 0, 2)
        label = QLabel(self.tr("Timestamp"))
        self.layout.addWidget(label, 0, 3)

        self.layout.setContentsMargins(10, 10, 10, 10)
        self.thread.finished.connect(self.updateUi)
        self.setLayout(self.layout)
        self.setWindowTitle(self.tr("Online users"))

    def updateUi(self):
        # first remove all the labels:
        for i in reversed(range(len(self.labels))):
            la = self.labels[i]
            la.setParent(None)
        self.labels = []
        r = 1
        for i in self.data:
            c = 0
            for k, v in i.items():
                label = QLabel(self.tr("%s" % str(v)))
                # print(len(self.data))
                self.labels.append(label)
                self.layout.addWidget(label, r, c)
                c += 1
            r += 1

    def closeEvent(self, event):
        if self.do_close:
            super().closeEvent(event)
        else:
            event.ignore()
            self.hide()


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

# TODO: Implement a gui for
