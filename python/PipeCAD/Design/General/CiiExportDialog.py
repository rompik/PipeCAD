"""Dialog for exporting straight PipeCAD tubing to a CII candidate."""

import os

from PythonQt.QtCore import QCoreApplication, Qt
from PythonQt.QtGui import (
    QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
)

from PipeCAD.Database import Project
from PipeCAD.GUI import MainWindow
from PipeCAD.Design.General.CiiExporter import CiiExporter


class CiiExportDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(self.tr("CAESAR II CII Export"))
        self.resize(520, 400)
        self._build()

    def tr(self, text, comment=None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)

    def _build(self):
        root = QVBoxLayout(self)
        group = QGroupBox(self.tr("Branch List"), self)
        layout = QVBoxLayout(group)
        self.listWidget = QListWidget(group)
        layout.addWidget(self.listWidget)
        buttons = QHBoxLayout()
        add = QPushButton(self.tr("Add"), self)
        remove = QPushButton(self.tr("Remove"), self)
        clear = QPushButton(self.tr("Clear"), self)
        add.clicked.connect(self.addElement)
        remove.clicked.connect(self.removeElement)
        clear.clicked.connect(self.clearList)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addWidget(clear)
        layout.addLayout(buttons)
        root.addWidget(group)

        root.addWidget(QLabel(self.tr("Output CII file"), self))
        self.textPath = QLineEdit(QCoreApplication.applicationDirPath() + "/pipe.cii")
        root.addWidget(self.textPath)
        root.addWidget(QLabel(self.tr("Settings JSON file"), self))
        self.textSettings = QLineEdit(os.path.join(os.path.dirname(__file__), "cii_settings.example.json"))
        root.addWidget(self.textSettings)
        self.testSettings = QCheckBox(self.tr("Allow illustrative test settings"), self)
        root.addWidget(self.testSettings)
        root.addWidget(QLabel(self.tr("Candidate only: review the model in CAESAR II before use."), self))

        actions = QDialogButtonBox()
        actions.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        root.addWidget(actions)

    def addBranch(self, name):
        if not self.listWidget.findItems(name, Qt.MatchExactly):
            item = QListWidgetItem(name, self.listWidget)
            self.listWidget.setCurrentItem(item)

    def addElement(self, *args):
        element = Project.CurrentElement
        if element.Type == "PIPE":
            for branch in element.Members:
                self.addBranch(branch.Name)
        elif element.Type == "BRAN":
            self.addBranch(element.Name)
        else:
            QMessageBox.warning(self, "", self.tr("Please select PIPE or BRANCH to export!"))

    def removeElement(self, *args):
        self.listWidget.takeItem(self.listWidget.currentRow)

    def clearList(self, *args):
        self.listWidget.clear()

    def accept(self):
        try:
            branches = []
            for row in range(self.listWidget.count):
                item = self.listWidget.item(row)
                branch = Project.GetElement(item.text())
                if not branch.IsValid or branch.Type != "BRAN":
                    raise ValueError("Branch {!r} is no longer available".format(item.text()))
                branches.append(branch)
            exporter = CiiExporter.from_file(str(self.textSettings.text), bool(self.testSettings.checked))
            exporter.export(branches, str(self.textPath.text))
        except (ValueError, TypeError, AttributeError, OSError) as exc:
            QMessageBox.critical(self, self.tr("CII Export"), str(exc))
            return
        QMessageBox.warning(
            self, self.tr("CII Export"),
            self.tr("CII candidate created. Check geometry, properties and restraints in CAESAR II before use."),
        )
        QDialog.accept(self)


ciiExportDialog = CiiExportDialog(MainWindow)


def Show():
    ciiExportDialog.show()
