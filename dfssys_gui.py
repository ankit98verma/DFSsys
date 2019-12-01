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
        if '-a' in w:
            self.main_gui.thread.start()
            self.onlines_gui.thread.start()
        elif '-m' in w:
            self.main_gui.thread.start()
        elif '-o' in w:
            self.onlines_gui.thread.start()

    def show_guis(self, w):
        if '-a' in w:
            self.main_gui.show()
            self.onlines_gui.show()
        elif '-m' in w:
            self.main_gui.show()
        elif '-o' in w:
            self.onlines_gui.show()

    def close_guis(self):
        self.main_gui.do_close = True
        self.onlines_gui.do_close = True

        self.main_gui.close()
        self.onlines_gui.close()


class gui_base(QWidget):

    def __init__(self, title, parent=None):
        QWidget.__init__(self, parent)
        self.do_close = False
        self.allow_update = True
        self.thread = Worker()
        self.layout = QGridLayout()

        self.layout.setContentsMargins(10, 10, 10, 10)
        self.thread.finished.connect(self.updateUi)
        self.setLayout(self.layout)
        self.setWindowTitle(self.tr(title))

    def updateUi(self):
        if not self.allow_update:
            return
        self.drawUI()

    def drawUI(self):
        pass

    def closeEvent(self, event):
        if self.do_close:
            super().closeEvent(event)
        else:
            event.ignore()
            self.allow_update = False
            self.hide()

    def show(self):
        super().show()
        self.allow_update = True


class main_gui(gui_base):

    def __init__(self, data, parent=None):
        super().__init__("Log information", parent)
        self.data = data
        self.labels = []
        self.prev_data = data.copy()
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

            self.layout.addWidget(label, r, 0)
            self.layout.addWidget(labeli, r, 1)
            r += 1
            self.labels.append(labeli)

    def drawUI(self):
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


class onlines_gui(gui_base):

    def __init__(self, online_data, parent=None):
        super().__init__("Online users", parent)

        self.data = online_data
        self.table = QTableWidget(0, 4)

        self.table.setHorizontalHeaderLabels(["IP Addr", "Alias", "Transmit rate", "Timestamp"])
        self.layout.addWidget(self.table)
        self.resize(500, 400)

    def drawUI(self):
        # first remove all the labels:
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
        r = 0
        for i in self.data:
            self.table.insertRow(r)
            c = 0
            for k, v in i.items():
                self.table.setItem(r, c, QTableWidgetItem(self.tr("%s" % str(v))))
                c += 1
            r += 1


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
