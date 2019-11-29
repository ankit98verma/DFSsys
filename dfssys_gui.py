from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class Window(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.thread = Worker()
        self.i = 0
        self.label = QLabel(self.tr("Number of stars: %d" % self.i))
        self.thread.finished.connect(self.updateUi)
        layout = QGridLayout()
        layout.addWidget(self.label, 0, 0)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Simple Threading Example"))

    def updateUi(self):
        self.i += 1
        self.label.setText(self.tr("Number of stars: %d" % self.i))


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

# def fun(threadq):
#     i = 2
#     while i > 0:
#         threadq.start()
#         print("done %d" % i)
#         time.sleep(1)
#         i -= 1
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = Window()
#     th = threading.Thread(target=fun, args=(window.thread,))
#     th.start()
#     window.show()
#     window.resize(300, 300)
#     app.exec_()
#     th.join()
