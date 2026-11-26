# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# :: Welcome to PipeCAD!                                      ::
# ::  ____                        ____     ______  ____       ::
# :: /\  _`\   __                /\  _`\  /\  _  \/\  _`\     ::
# :: \ \ \L\ \/\_\  _____      __\ \ \/\_\\ \ \L\ \ \ \/\ \   ::
# ::  \ \ ,__/\/\ \/\ '__`\  /'__`\ \ \/_/_\ \  __ \ \ \ \ \  ::
# ::   \ \ \/  \ \ \ \ \L\ \/\  __/\ \ \L\ \\ \ \/\ \ \ \_\ \ ::
# ::    \ \_\   \ \_\ \ ,__/\ \____\\ \____/ \ \_\ \_\ \____/ ::
# ::     \/_/    \/_/\ \ \/  \/____/ \/___/   \/_/\/_/\/___/  ::
# ::                  \ \_\                                   ::
# ::                   \/_/                                   ::
# ::                                                          ::
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# PipeCAD - Piping Design Software.
# Copyright (C) 2026 Wuhan TUHE Tech Co., Ltd.
# Author: Shing Liu(whtuhe@qq.com)
# Date: 11:20 2026-09-27

import os

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow
from PipeCAD.Design.General.PcfExporterCore import export_file


def Export(branchList, filename):
    export_file(branchList, filename, Project.World)
# Export


class PcfExportDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("PCF Export"))
        self.resize(500, 360)

        self.verticalLayout = QVBoxLayout(self)

        # Branch List
        self.ListGroup = QGroupBox(self.tr("Branch List"), self)

        self.listLayout1 = QVBoxLayout(self.ListGroup)

        self.listWidget = QListWidget(self.ListGroup)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setUniformItemSizes(True)

        self.listLayout1.addWidget(self.listWidget)

        self.listLayout2 = QHBoxLayout()

        self.buttonAdd = QPushButton(self.tr("Add", "Add Pipe/Branch"), self)
        self.buttonRemove = QPushButton(self.tr("Remove"), self)
        self.buttonClear = QPushButton(self.tr("Clear"), self)

        self.buttonAdd.clicked.connect(self.addElement)
        self.buttonRemove.clicked.connect(self.removeElement)
        self.buttonClear.clicked.connect(self.clearList)

        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.listLayout2.addWidget(self.buttonAdd)
        self.listLayout2.addWidget(self.buttonRemove)
        self.listLayout2.addWidget(self.buttonClear)
        self.listLayout2.addSpacerItem(spacer)

        self.listLayout1.addLayout(self.listLayout2)

        self.verticalLayout.addWidget(self.ListGroup)

        # Output option.
        self.outputGroup = QGroupBox(self.tr("Output"), self)

        self.outputLayout = QHBoxLayout(self.outputGroup)

        appPath = QCoreApplication.applicationDirPath()
        self.textPath = QLineEdit(os.path.join(appPath, "pipe.pcf"))
        self.buttonPath = QPushButton("...")
        self.buttonPath.clicked.connect(self.selectOutputFile)

        self.outputLayout.addWidget(self.textPath)
        self.outputLayout.addWidget(self.buttonPath)

        self.verticalLayout.addWidget(self.outputGroup)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    # setupUi

    def addBranch(self, name):
        if len(self.listWidget.findItems(name, Qt.MatchExactly)) == 0:
            aListItem = QListWidgetItem(name, self.listWidget)
            self.listWidget.setCurrentItem(aListItem)
        # if
    # addBranch

    def setOutputPipeName(self, pipe):
        name = str(pipe.Name).replace("/", "").replace("\\", "") if pipe is not None else ""
        filename = (name + ".pcf") if name else "pipe.pcf"
        appPath = QCoreApplication.applicationDirPath()
        self.textPath.text = os.path.join(appPath, filename)

    def addElement(self, *args):
        ce = DbElement.Current

        if not ce.IsValid:
            return

        type = ce.Type
        if type == 'PIPE':
            self.setOutputPipeName(ce)
            memberList = ce.Members
            for member in memberList:
                self.addBranch(member.Name)
            # for
        elif type == 'BRAN':
            self.setOutputPipeName(ce.Owner)
            self.addBranch(ce.Name)
        else:
            QMessageBox.warning(self, "", self.tr("Please select PIPE or BRANCH to export!"))
    # addElement

    def removeElement(self, *args):
        row = self.listWidget.currentRow
        self.listWidget.takeItem(row)
    # removeList

    def clearList(self, *args):
        self.listWidget.clear()
    # clearList

    def selectOutputFile(self, *args):
        filename = QFileDialog.getSaveFileName(
            self,
            self.tr("Export PCF"),
            self.textPath.text,
            self.tr("PCF Files (*.pcf)"),
        )
        if isinstance(filename, (tuple, list)):
            filename = filename[0]
        if filename:
            self.textPath.text = filename

    def accept(self):
        if self.listWidget.count < 1:
            QMessageBox.warning(self, "", self.tr("Please add branch to export PCF!"))
            return
        # if

        branchList = []

        for row in range(self.listWidget.count):
            listItem = self.listWidget.item(row)
            if listItem:
                branch = Project.GetElement(listItem.text())
                if branch.IsValid and branch.Type == "BRAN":
                    branchList.append(branch)
                # if
            # if
        # for

        filename = self.textPath.text

        try:
            Export(branchList, filename)
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as ex:
            QMessageBox.critical(self, self.tr("PCF Export"), str(ex))
            return

        QDialog.accept(self)
    # accept

# PcfExportDialog

pcfExportDialog = PcfExportDialog(MainWindow)

def Show():
    pcfExportDialog.show()
# Show
