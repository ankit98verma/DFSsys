from datetime import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import *


# Disabling the warnings
# def handler(msg_type, msg_log_context, msg_string):
#     pass
# qInstallMessageHandler(handler)


class DFSsysGUIHandle:

    def __init__(self, log_data, onlines_data, duplicate_packets, lock):
        self.main_gui = main_gui(log_data, lock)
        self.onlines_gui = onlines_gui(onlines_data, lock)
        self.dup_gui = duplicates_gui(duplicate_packets, lock)

    def trigger_guis(self, w):
        if '-a' in w:
            self.main_gui.thread.start()
            self.onlines_gui.thread.start()
            self.dup_gui.thread.start()
        elif '-m' in w:
            self.main_gui.thread.start()
        elif '-o' in w:
            self.onlines_gui.thread.start()
        elif '-d' in w:
            self.dup_gui.thread.start()

    def show_guis(self, w):
        if '-a' in w:
            self.main_gui.show()
            self.onlines_gui.show()
            self.dup_gui.show()
        elif '-m' in w:
            self.main_gui.show()
        elif '-o' in w:
            self.onlines_gui.show()
        elif '-d' in w:
            self.dup_gui.show()

    def close_guis(self):

        self.main_gui.do_close = True
        self.onlines_gui.do_close = True
        self.dup_gui.do_close = True

        self.main_gui.close()
        self.onlines_gui.close()
        self.dup_gui.close()


class gui_base(QWidget):

    def __init__(self, title, lock, parent=None):
        QWidget.__init__(self, parent)
        self.do_close = False
        self.allow_update = True
        self.thread = Worker()
        self.layout = QGridLayout()
        self.lock = lock

        self.layout.setContentsMargins(10, 10, 10, 10)
        self.thread.finished.connect(self.updateUi)
        self.setLayout(self.layout)
        self.setWindowTitle(self.tr(title))

    def updateUi(self):
        if not self.allow_update:
            return
        with self.lock:
            self.drawUI()

    def drawUI(self):
        pass

    def closeEvent(self, event):
        self.allow_update = False
        if self.do_close:
            super().closeEvent(event)
        else:
            event.ignore()
            self.hide()

    def show(self):
        super().show()
        self.allow_update = True


class Worker(QThread):
    output = pyqtSignal()

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False

    def __del__(self):
        self.exiting = True
        self.wait()

    def run(self):
        pass


class main_gui(gui_base):

    def __init__(self, data, lock, parent=None):
        super().__init__("Log information", lock, parent)
        self.data = data
        self.labels = []
        self.prev_data = data.copy()
        self.table = QTableWidget(len(self.data.items()), 2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        r = 0
        for k, _ in self.data.items():
            self.table.setItem(r, 0, QTableWidgetItem(self.tr(k)))
            r += 1
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.table)
        self.resize(300, 600)

    def drawUI(self):
        r = 0
        for k, v in self.data.items():
            prev_d = self.prev_data[k]
            self.table.setItem(r, 1, QTableWidgetItem(self.tr(str(v))))

            if prev_d != v:
                self.table.item(r, 1).setForeground(QBrush(QColor(255, 0, 0)))
            else:
                self.table.item(r, 1).setForeground(QBrush(QColor(0, 0, 0)))
            r += 1

        self.prev_data = self.data.copy()


class onlines_gui(gui_base):

    def __init__(self, online_data, lock, parent=None):
        super().__init__("Online users", lock, parent)

        self.data = online_data
        self.table = QTableWidget(0, 4)

        self.table.setHorizontalHeaderLabels(["IP Addr", "Alias", "Transmit rate", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
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
                if k == 'timestamp':
                    v = datetime.fromtimestamp(v / 1000)
                    self.table.setItem(r, c, QTableWidgetItem(self.tr("%s" % str(v))))
                else:
                    self.table.setItem(r, c, QTableWidgetItem(self.tr("%s" % str(v))))
                c += 1
            r += 1


class duplicates_gui(gui_base):

    def __init__(self, data, lock, parent=None):
        super().__init__("Duplicate packets", lock, parent)
        self.data = data
        self.table = QTableWidget(0, 2)

        self.table.setHorizontalHeaderLabels(["Originator IP", "Originator Packet counter"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.table)
        self.resize(400, 400)

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
