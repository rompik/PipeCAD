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
# Date: 13:06 2026-11-22

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow

class PipeDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Pipe"))

        self.horizontalLayout = QHBoxLayout(self)
        self.verticalLayout = QVBoxLayout()

        self.formLayout = QFormLayout()

        # Name
        self.comboName = QComboBox()
        self.textName = QLineEdit()
        self.textName.setMinimumWidth(150)

        self.comboName.addItem(self.tr("Create"))
        self.comboName.addItem(self.tr("Modify"))
        self.comboName.activated.connect(self.activateName)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.comboName)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textName)

        self.verticalLayout.addLayout(self.formLayout)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        # Pipe spec.
        self.labelSpec = QLabel(self.tr("Select Pipe Specification"))
        self.verticalLayout.addWidget(self.labelSpec)

        self.listSpec = QListWidget()
        self.listSpec.setAlternatingRowColors(True)
        self.listSpec.currentRowChanged.connect(self.specChanged)
        self.verticalLayout.addWidget(self.listSpec)

        # Basic Pipe Process Data.
        self.labelSpec = QLabel(self.tr("Basic Pipe Process Data"))
        self.verticalLayout.addWidget(self.labelSpec)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        self.formLayout = QFormLayout()

        self.labelBore = QLabel(self.tr("Bore"))
        self.comboBore = QComboBox()

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelBore)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.comboBore)

        self.labelInsu = QLabel(self.tr("Insulation"))
        self.comboInsu = QComboBox()

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelInsu)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.comboInsu)

        self.labelTracing = QLabel(self.tr("Tracing"))
        self.comboTracing = QComboBox()

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelTracing)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.comboTracing)

        self.labelTemp = QLabel(self.tr("Temperature"))
        self.textTemp = QLineEdit("-10000.00")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.labelTemp)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.textTemp)

        self.labelPressure = QLabel(self.tr("Pressure"))
        self.textPressure = QLineEdit("0.00")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.labelPressure)
        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.textPressure)

        self.verticalLayout.addLayout(self.formLayout)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttonBox)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.initPipeData()
    # setupUi

    def initPipeData(self):
        # First clear all.
        self.listSpec.clear()
        self.comboInsu.clear()
        self.comboTracing.clear()

        # Set pipe spec/insulation/tracing.
        typeFilter = TypeFilter('SPEC')
        collection = DbElementCollection(Project.World, typeFilter)
        specList = collection.Perform()
        for specElement in specList:
            purpose = specElement.Purpose
            if purpose == 'PIPE':
                listItem = QListWidgetItem(specElement.Name)
                listItem.setData(Qt.UserRole, specElement)
                self.listSpec.addItem(listItem)
            elif purpose == 'INSU':
                self.comboInsu.addItem(specElement.Name, specElement)
            elif purpose == 'TRAC':
                self.comboTracing.addItem(specElement.Name, specElement)
            # if
        # for

        if self.listSpec.count > 0:
            self.listSpec.setCurrentRow(0)
        # if
    # initPipeData

    def specChanged(self):
        self.comboBore.clear()

        specElement = self.listSpec.currentItem().data(Qt.UserRole)
        if specElement is None:
            return
        # if

        boreDict = dict()

        typeFilter = TypeFilter('SPCO')
        collection = DbElementCollection(specElement, typeFilter)
        spcoList = collection.Perform()
        for spco in spcoList:
            catref = spco.Catref
            if catref.IsValid and catref.Gtype == 'TUBE':
                param = catref.Param
                if len(param) > 0:
                    boreDict[int(param[0])] = spco
                # if
            # if
        # for

        for bore in sorted(boreDict):
            self.comboBore.addItem(bore, boreDict[bore])
        # for
    # specChanged

    def activateName(self):
        index = self.comboName.currentIndex
        if index == 0:
            self.setWindowTitle(self.tr('Create Pipe'))
        else:
            self.setWindowTitle(self.tr('Modify Pipe'))
            self.setPipeData()
        # if
    # activateName

    def setPipeData(self):
        index = self.comboName.currentIndex

        # Set pipe data for current pipe.
        pipe = DbElement.Current
        if pipe.Type != 'PIPE':
            QMessageBox.warning(self, '', self.tr('Please select PIPE to modify!'))
            return
        # if

        # Set pipe name.
        self.textName.text = pipe.Name

        # Set pipe spec.
        pspec = pipe.Pspec
        if pspec.IsValid:
            specItems = self.listSpec.findItems(pspec.Name, Qt.MatchExactly)
            if len(specItems) == 1:
                self.listSpec.setCurrentItem(specItems[0])
            # if
        # if

        # Set insulation spec.
        ispec = pipe.Ispec
        if ispec.IsValid:
            self.comboInsu.currentIndex = self.comboInsu.findText(ispec.Name)
        # if

        # Set tracing spec.
        tspec = pipe.Tspec
        if tspec.IsValid:
            self.comboTracing.currentIndex = self.comboTracing.findText(tspec.Name)
        # if

        self.comboBore.currentText = str(int(pipe.Bore))

        self.textTemp.text = str(pipe.Temperature)
        self.textPressure.text = str(pipe.Pressure)

        self.comboName.setItemData(index, pipe)
    # setPipeData

    def createPipe(self):
        try:
            Project.Current.OpenTransaction()

            pipe = DbElement.Current.Create(0, 'PIPE')
            pipe.Name = self.textName.text
            pipe.Bore = float(self.comboBore.currentText)
            pipe.Pspec = self.listSpec.currentItem().data(Qt.UserRole)
            pipe.Ispec = self.comboInsu.currentData
            pipe.Tspec = self.comboTracing.currentData
            pipe.Temperature = float(self.textTemp.text)
            pipe.Pressure = float(self.textPressure.text)

            Project.Current.CommitTransaction()
        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # createPipe

    def modifyPipe(self):
        pipe = self.comboName.currentData
        if pipe is None or not pipe.IsValid:
            QMessageBox.warning(self, '', self.tr('Please select PIPE to modify!'))
            return
        # if

        try:
            Project.Current.OpenTransaction()

            pipe.Name = self.textName.text
            pipe.Bore = float(self.comboBore.currentText)
            pipe.Pspec = self.listSpec.currentItem().data(Qt.UserRole)
            pipe.Ispec = self.comboInsu.currentData
            pipe.Tspec = self.comboTracing.currentData
            pipe.Temperature = float(self.textTemp.text)
            pipe.Pressure = float(self.textPressure.text)

            Project.Current.CommitTransaction()
        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # modifyPipe

    def accept(self):
        index = self.comboName.currentIndex
        if index == 0:
            self.createPipe()
        else:
            self.modifyPipe()
        # if

        QDialog.accept(self)
    # accept

# PipeDialog

pipeDialog = PipeDialog(MainWindow)

def CreatePipe():
    pipeDialog.show()
# CreatePipe

class BranchDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Branch"))

        self.verticalLayout = QVBoxLayout(self)

        self.labelHello = QLabel(self.tr("Hello PipeCAD!"))

        self.verticalLayout.addWidget(self.labelHello)

    # setupUi

# BranchDialog

branchDialog = BranchDialog(MainWindow)

def CreateBranch():
    branchDialog.show()
# CreateBranch
