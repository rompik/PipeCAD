# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# :: PipeCAD - Piping Design Software                          ::
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

try:
    from PythonQt.QtCore import QCoreApplication, Qt
    from PythonQt.QtGui import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
except ImportError:
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )

try:
    from PipeCAD.GUI import MainWindow
except ImportError:
    MainWindow = None


_dialog = None


class PipeExtractsDialog(QDialog):
    """Graphical shell for selecting pipes and extraction formats."""

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(self.tr("Pipe Extracts"))
        self.resize(900, 650)
        self._build_ui()

    def tr(self, text, comment=None):
        return QCoreApplication.translate(
            self.__class__.__name__, text, comment
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(self._create_pipe_list())
        root.addWidget(self._create_extraction_types())

        actions = QHBoxLayout()
        self.buttonExtractNow = QPushButton(self.tr("Extract Now"), self)
        self.buttonExtractNow.setMinimumHeight(32)
        actions.addWidget(self.buttonExtractNow)
        root.addLayout(actions)

        status = QHBoxLayout()
        self.labelStatus = QLabel(self.tr("Ready"), self)
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        status.addWidget(self.labelStatus, 1)
        status.addWidget(self.progressBar, 2)
        root.addLayout(status)

    def _create_pipe_list(self):
        group = QGroupBox(self.tr("Pipes List"), self)
        layout = QVBoxLayout(group)

        self.tablePipes = QTableWidget(group)
        self.tablePipes.setColumnCount(4)
        self.tablePipes.setHorizontalHeaderLabels([
            self.tr("Line Name"),
            self.tr("Pipe Name"),
            self.tr("Revision"),
            self.tr("Status"),
        ])
        self.tablePipes.setAlternatingRowColors(True)
        self.tablePipes.setSortingEnabled(True)
        self.tablePipes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tablePipes.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tablePipes.horizontalHeader().setStretchLastSection(True)
        if MainWindow is None:
            self._fill_demo_pipes()
        layout.addWidget(self.tablePipes)

        buttons = QHBoxLayout()
        self.buttonAdd = QPushButton(self.tr("Add Pipe"), group)
        self.buttonRemove = QPushButton(self.tr("Remove"), group)
        self.buttonClear = QPushButton(self.tr("Clear"), group)
        self.buttonSelectAll = QPushButton(self.tr("Select All"), group)
        buttons.addWidget(self.buttonAdd)
        buttons.addWidget(self.buttonRemove)
        buttons.addWidget(self.buttonClear)
        buttons.addStretch(1)
        buttons.addWidget(self.buttonSelectAll)
        layout.addLayout(buttons)
        return group

    def _fill_demo_pipes(self):
        rows = (
            ("LINE-101", "/P-101-A", "A", "Ready"),
            ("LINE-101", "/P-101-B", "A", "Ready"),
            ("LINE-102", "/P-102", "B", "Pending"),
            ("LINE-203", "/P-203-A", "C", "Ready"),
            ("LINE-305", "/P-305", "0", "Warning"),
            ("LINE-410", "/P-410-A", "D", "Ready"),
        )
        self.tablePipes.setSortingEnabled(False)
        self.tablePipes.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                self.tablePipes.setItem(
                    row_index, column, QTableWidgetItem(value)
                )
        self.tablePipes.setSortingEnabled(True)
        self.tablePipes.resizeColumnsToContents()

    def _create_extraction_types(self):
        group = QGroupBox(self.tr("Type of Files for Extraction"), self)
        layout = QGridLayout(group)

        self.checkPdf3D = QCheckBox(self.tr(".PDF (3D)"), group)
        self.checkPdf = QCheckBox(self.tr(".PDF"), group)
        self.checkDxf = QCheckBox(self.tr(".DXF"), group)
        self.checkIdf = QCheckBox(self.tr(".IDF"), group)
        self.checkPcf = QCheckBox(self.tr(".PCF"), group)

        checks = (
            self.checkPdf3D,
            self.checkPdf,
            self.checkDxf,
            self.checkIdf,
            self.checkPcf,
        )
        for index, check in enumerate(checks):
            check.setChecked(check is not self.checkPcf)
            layout.addWidget(check, 0, index)
        return group


def Show():
    global _dialog
    _dialog = PipeExtractsDialog(MainWindow)
    widget_attributes = getattr(Qt, "WidgetAttribute", Qt)
    _dialog.setAttribute(widget_attributes.WA_DeleteOnClose)
    _dialog.show()
    return _dialog


if __name__ == "__main__":
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    Show()
    sys.exit(app.exec())
