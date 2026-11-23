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

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow


def Export(branchList, filename):
    branchSize = len(branchList)
    if branchSize == 0:
        return
    # if

    pcfFile = open(filename, "w")

    # PCF HEADER
    pcfFile.write("ISOGEN-FILES ISOGEN.FLS\n")
    pcfFile.write("UNITS-BORE        MM\n")
    pcfFile.write("UNITS-CO-ORDS     MM\n")
    pcfFile.write("UNITS-BOLT-LENGTH MM\n")
    pcfFile.write("UNITS-BOLT-DIA    MM\n")
    pcfFile.write("UNITS-WEIGHT      KGS\n")

    # PIPELINE
    pipeline = branchList[0].Owner
    pspec = pipeline.Pspec
    ispec = pipeline.Ispec
    tspec = pipeline.Tspec

    pcfFile.write("PIPELINE-REFERENCE {}\n".format(pipeline.Name))
    if pspec.IsValid:
        pcfFile.write("    PIPING-SPEC  {}\n".format(pspec.Name))
    # if

    if ispec.IsValid:
        pcfFile.write("    INSULATION-SPEC  {}\n".format(ispec.Name))
    # if 

    if tspec.IsValid:
        pcfFile.write("    TRACING-SPEC  {}\n".format(tspec.Name))
    # if

    # Item code dict.
    itemCodeDict = dict()

    # Branch components.
    for branch in branchList:
        headPoint = branch.Hposition
        tailPoint = branch.Tposition

        members = branch.Members
        for component in members:
            type = component.Type

            if type == "TUBI":
                apos = component.Aposition
                lpos = component.Lposition

                bore = component.Lbore

                spec = ""
                spref = component.Spref
                if spref.IsValid:
                    spec = spref.Name
                # if

                pcfFile.write("PIPE\n")
                pcfFile.write("    COMPONENT-IDENTIFIER  {}\n".format(0))
                pcfFile.write("    END-POINT  {0} {1} {2} {3}\n".format(apos.X, apos.Y, apos.Z, int(bore)))
                pcfFile.write("    END-POINT  {0} {1} {2} {3}\n".format(lpos.X, lpos.Y, lpos.Z, int(bore)))
                pcfFile.write("    PIPING-SPEC  {}\n".format(spec))
                pcfFile.write("    CATEGORY {}\n".format(""))
                pcfFile.write("    ITEM-CODE  {}\n".format(spec))
                pcfFile.write("    ITEM-DESCRIPTION  {}\n".format(""))
                pcfFile.write("    CUT-PIECE-LENGTH {}\n".format(component.Itlength))

                if len(spec) > 0:
                    itemCodeDict[spec] = ""
                # if
            else:
                arrive = component.Arrive
                leave = component.Leave

                apos = Position()
                lpos = Position()

                abore = 0
                lbore = 0

                skey = ""

                pcfFile.write("{}\n".format(type))
                pcfFile.write("    COMPONENT-IDENTIFIER  {}\n".format(0))
                pcfFile.write("    END-POINT  {0} {1} {2} {3}\n".format(apos.X, apos.Y, apos.Z, int(abore)))
                pcfFile.write("    END-POINT  {0} {1} {2} {3}\n".format(lpos.X, lpos.Y, lpos.Z, int(lbore)))
                pcfFile.write("    SKEY  {}\n".format(skey))
                pcfFile.write("    CATEGORY {}\n".format(""))
                pcfFile.write("    ITEM-CODE  {}\n".format(""))
                pcfFile.write("    ITEM-DESCRIPTION  {}\n".format(""))
            #
        # for
    # for

    # ITEM-CODE
    pcfFile.write("MATERIALS\n")
    for (key, value) in itemCodeDict.items():
        pcfFile.write("ITEM-CODE {}\n".format(key))
        pcfFile.write("    DESCRIPTION  {}\n".format(value))
    # for

    pcfFile.close()
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

        #
        appPath = QCoreApplication.applicationDirPath()
        self.textPath = QLineEdit(appPath + "/pipe.pcf")
        self.buttonPath = QPushButton("...")

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

    def addElement(self):
        ce = Project.CurrentElement

        type = ce.Type
        if type == 'PIPE':
            memberList = ce.Members
            for member in memberList:
                self.addBranch(member.Name)
            # for
        elif type == 'BRAN':
            self.addBranch(ce.Name)
        else:
            QMessageBox.warning(self, "", self.tr("Please select PIPE or BRANCH to export!"))
    # addElement

    def removeElement(self):
        row = self.listWidget.currentRow
        self.listWidget.takeItem(row)
    # removeList

    def clearList(self):
        self.listWidget.clear()
    # clearList

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
                if branch.IsValid:
                    branchList.append(branch)
                # if
            # if
        # for

        filename = self.textPath.text

        Export(branchList, filename)

        QDialog.accept(self)
    # accept

# PcfExportDialog

pcfExportDialog = PcfExportDialog(MainWindow)

def Show():
    pcfExportDialog.show()
# Show
