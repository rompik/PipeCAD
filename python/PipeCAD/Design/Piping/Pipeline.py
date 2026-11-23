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

class BranchDialog(QDockWidget):
    def __init__(self, parent = None):
        QDockWidget.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Branch"))
        self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)

        MainWindow.addDockWidget(Qt.RightDockWidgetArea, self)

        self.dockContext = QWidget()
        self.verticalLayout = QVBoxLayout(self.dockContext)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Pipe name
        self.horizontalLayout = QHBoxLayout()
        self.labelPipe = QLabel(self.tr("Pipe: "))
        self.labelPipe.setSizePolicy(sizePolicy)

        self.textPipe = QLabel("pipe")
        self.textPipe.setStyleSheet('color:red;')
        self.buttonPipe = QPushButton(self.tr("Set Pipe"))
        self.buttonPipe.setSizePolicy(sizePolicy)
        #self.buttonPipe.clicked.connect(self.setPipe)

        self.horizontalLayout.addWidget(self.labelPipe)
        self.horizontalLayout.addWidget(self.textPipe)
        self.horizontalLayout.addWidget(self.buttonPipe)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.linePipeDetail = QFrame()
        self.linePipeDetail.setFrameShape(QFrame.HLine)
        self.linePipeDetail.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.linePipeDetail)

        # Pipe spec
        self.horizontalLayout = QHBoxLayout()
        self.labelSpec = QLabel(self.tr("Spec: "))
        self.labelSpec.setSizePolicy(sizePolicy)
        self.textSpec = QLabel("")
        self.buttonSpec = QPushButton(self.tr("Set Detail"))
        self.buttonSpec.setSizePolicy(sizePolicy)
        #self.buttonSpec.clicked.connect(self.modifyPipe)

        self.horizontalLayout.addWidget(self.labelSpec)
        self.horizontalLayout.addWidget(self.textSpec)
        self.horizontalLayout.addWidget(self.buttonSpec)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Branch Table.
        self.tableWidgetBranch = QTableWidget()
        self.tableWidgetBranch.setColumnCount(3)
        self.tableWidgetBranch.setHorizontalHeaderLabels([self.tr('Branch'), self.tr('Head'), self.tr('Tail')])
        self.tableWidgetBranch.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidgetBranch.setAlternatingRowColors(True)
        self.tableWidgetBranch.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableWidgetBranch.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidgetBranch.setGridStyle(Qt.SolidLine)
        self.tableWidgetBranch.horizontalHeader().setStretchLastSection(True)
        self.tableWidgetBranch.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidgetBranch.verticalHeader().setMinimumSectionSize(16)
        self.tableWidgetBranch.verticalHeader().setDefaultSectionSize(18)
        self.tableWidgetBranch.verticalHeader().hide() 
        #self.tableWidgetBranch.itemSelectionChanged.connect(self.currentBranchChanged)
        self.verticalLayout.addWidget(self.tableWidgetBranch)

        # New Branch.
        self.horizontalLayout = QHBoxLayout()
        self.buttonBranch = QPushButton(self.tr("New Branch"))
        #self.buttonBranch.clicked.connect(self.createBranch)
        self.horizontalLayout.addWidget(self.buttonBranch)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Current Branch
        self.horizontalLayout = QHBoxLayout()
        self.labelBranch = QLabel(self.tr("Branch: "))
        self.labelBranch.setSizePolicy(sizePolicy)
        self.textBranch = QLabel()
        self.horizontalLayout.addWidget(self.labelBranch)
        self.horizontalLayout.addWidget(self.textBranch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lineBranchDetail = QFrame()
        self.lineBranchDetail.setFrameShape(QFrame.HLine)
        self.lineBranchDetail.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.lineBranchDetail)

        # Branch spec
        self.horizontalLayout = QHBoxLayout()
        self.labelBranchSpec = QLabel(self.tr("Spec: "))
        self.labelBranchSpec.setSizePolicy(sizePolicy)
        self.textBranchSpec = QLabel()
        self.buttonBranchSpec = QPushButton(self.tr("Set Detail"))
        self.buttonBranchSpec.setSizePolicy(sizePolicy)
        #self.buttonBranchSpec.clicked.connect(self.setBranchSpec)

        self.horizontalLayout.addWidget(self.labelBranchSpec)
        self.horizontalLayout.addWidget(self.textBranchSpec)
        self.horizontalLayout.addWidget(self.buttonBranchSpec)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Head Detail
        self.lableHeadDetail = QLabel(self.tr("Head Detail: "))
        self.lineHeadDetail = QFrame()
        self.lineHeadDetail.setFrameShape(QFrame.HLine)
        self.lineHeadDetail.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.lableHeadDetail)
        self.verticalLayout.addWidget(self.lineHeadDetail)

        self.horizontalLayout = QHBoxLayout()
        self.labelHeadBore = QLabel(self.tr("Bore: "))
        self.labelHeadBore.setSizePolicy(sizePolicy)
        self.textHeadBore = QLabel("")
        self.labelHeadType = QLabel(self.tr("Connection Type: "))
        self.labelHeadType.setSizePolicy(sizePolicy)
        self.textHeadType = QLabel("")
        self.horizontalLayout.addWidget(self.labelHeadBore)
        self.horizontalLayout.addWidget(self.textHeadBore)
        self.horizontalLayout.addWidget(self.labelHeadType)
        self.horizontalLayout.addWidget(self.textHeadType)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelHeadDirection = QLabel(self.tr("Direction: "))
        self.labelHeadDirection.setSizePolicy(sizePolicy)
        self.textHeadDirection = QLabel("")
        self.horizontalLayout.addWidget(self.labelHeadDirection)
        self.horizontalLayout.addWidget(self.textHeadDirection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelHeadPosition = QLabel(self.tr("Position: "))
        self.labelHeadPosition.setSizePolicy(sizePolicy)
        self.textHeadPosition = QLabel("")
        self.horizontalLayout.addWidget(self.labelHeadPosition)
        self.horizontalLayout.addWidget(self.textHeadPosition)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonChangeHead = QPushButton(self.tr("Change"))
        self.buttonChangeHead.setSizePolicy(sizePolicy)
        #self.buttonChangeHead.clicked.connect(self.changeHeadDetail)
        self.horizontalLayout.addWidget(self.buttonChangeHead)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Head Connection
        self.labelHeadConnection = QLabel(self.tr("Head Connection:"))
        self.lineHeadConnection = QFrame()
        self.lineHeadConnection.setFrameShape(QFrame.HLine)
        self.lineHeadConnection.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.labelHeadConnection)
        self.verticalLayout.addWidget(self.lineHeadConnection)

        self.horizontalLayout = QHBoxLayout()
        self.textHeadConnection = QLabel(self.tr("Undefined"))
        self.buttonHeadConnection = QPushButton(self.tr("Change"))
        #self.buttonHeadConnection.clicked.connect(self.changeHeadConnection)
        self.buttonHeadConnection.setSizePolicy(sizePolicy)
        self.horizontalLayout.addWidget(self.textHeadConnection)
        self.horizontalLayout.addWidget(self.buttonHeadConnection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Tail Detail
        self.lableTailDetail = QLabel(self.tr("Tail Detail: "))
        self.lineTailDetail = QFrame()
        self.lineTailDetail.setFrameShape(QFrame.HLine)
        self.lineTailDetail.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.lableTailDetail)
        self.verticalLayout.addWidget(self.lineTailDetail)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailBore = QLabel(self.tr("Bore: "))
        self.textTailBore = QLabel("")
        self.labelTailType = QLabel(self.tr("Connection Type: "))
        self.textTailType = QLabel("")
        self.horizontalLayout.addWidget(self.labelTailBore)
        self.horizontalLayout.addWidget(self.textTailBore)
        self.horizontalLayout.addWidget(self.labelTailType)
        self.horizontalLayout.addWidget(self.textTailType)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailDirection = QLabel(self.tr("Direction: "))
        self.labelTailDirection.setSizePolicy(sizePolicy)
        self.textTailDirection = QLabel("")
        self.horizontalLayout.addWidget(self.labelTailDirection)
        self.horizontalLayout.addWidget(self.textTailDirection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailPosition = QLabel(self.tr("Position: "))
        self.labelTailPosition.setSizePolicy(sizePolicy)
        self.textTailPosition = QLabel("")
        self.horizontalLayout.addWidget(self.labelTailPosition)
        self.horizontalLayout.addWidget(self.textTailPosition)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonChangeTail = QPushButton(self.tr("Change"))
        self.buttonChangeTail.setSizePolicy(sizePolicy)
        #self.buttonChangeTail.clicked.connect(self.changeTailDetail)
        self.horizontalLayout.addWidget(self.buttonChangeTail)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Tail Connection
        self.labelTailConnection = QLabel(self.tr("Tail Connection:"))
        self.lineTailConnection = QFrame()
        self.lineTailConnection.setFrameShape(QFrame.HLine)
        self.lineTailConnection.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.labelTailConnection)
        self.verticalLayout.addWidget(self.lineTailConnection)

        self.horizontalLayout = QHBoxLayout()
        self.textTailConnection = QLabel(self.tr("Undefined"))
        self.buttonTailConnection = QPushButton(self.tr("Change"))
        self.buttonTailConnection.setSizePolicy(sizePolicy)
        #self.buttonTailConnection.clicked.connect(self.changeTailConnection)
        self.horizontalLayout.addWidget(self.textTailConnection)
        self.horizontalLayout.addWidget(self.buttonTailConnection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Set dock widget.
        self.setWidget(self.dockContext)

    # setupUi

# BranchDialog

branchDialog = BranchDialog(MainWindow)

def CreateBranch():
    branchDialog.show()
# CreateBranch
