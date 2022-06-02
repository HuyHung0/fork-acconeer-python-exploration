import sys

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from acconeer.exptool.app.new.backend import Backend


class MainWindow(QMainWindow):
    def __init__(self, backend: Backend) -> None:
        super().__init__()
        self.backend = backend
        self.setup_ui()

    def setup_ui(self) -> None:
        main_layout = QHBoxLayout()

        self.rhs_layout = QVBoxLayout()
        rhs_dummy = QWidget()
        rhs_dummy.setProperty("acc_type", "rhs")
        rhs_dummy.setLayout(self.rhs_layout)

        self.lhs_layout = QVBoxLayout()
        lhs_dummy = QWidget()
        lhs_dummy.setProperty("acc_type", "lhs")
        lhs_dummy.setLayout(self.rhs_layout)

        main_layout.addWidget(lhs_dummy)
        main_layout.addWidget(rhs_dummy)

        dummy = QWidget()
        dummy.setLayout(main_layout)
        self.setCentralWidget(dummy)


def run_with_backend(backend: Backend) -> None:
    app = QApplication(sys.argv)

    app.setStyleSheet(
        """
        *[acc_type="rhs"] { background-color: #e6a595 }
        *[acc_type="lhs"] { background-color: #a3c9ad }
        """
    )
    mw = MainWindow(backend)
    mw.rhs_layout.addWidget(QPushButton("Hello"))
    mw.show()

    app.exec()