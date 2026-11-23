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

            # Set pipe data for current pipe.
            pipe = DbElement.Current
            if pipe.Type != 'PIPE':
                QMessageBox.warning(self, '', self.tr('Please select PIPE to modify!'))
                return
            # if

            self.comboName.setItemData(index, pipe)
            self.setPipeData(pipe)
        # if
    # activateName

    def setPipeData(self, pipe):
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

    # setPipeData

    def setPipe(self, pipe):
        self.setWindowTitle(self.tr('Modify Pipe'))

        self.comboName.activated.disconnect(self.activateName)
        self.comboName.setEnabled(False)
        self.comboName.currentIndex = 1
        self.comboName.setItemData(1, pipe)

        self.setPipeData(pipe)
    # setPipe

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

        self.branch = None

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Modify Branch"))

        self.horizontalLayout = QHBoxLayout(self)
        self.verticalLayout = QVBoxLayout()

        self.formLayout = QFormLayout()

        # Name
        self.labelName = QLabel(self.tr('Name'))
        self.textName = QLineEdit()
        self.textName.setMinimumWidth(150)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelName)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textName)

        self.verticalLayout.addLayout(self.formLayout)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        # Branch spec.
        self.labelSpec = QLabel(self.tr("Select Branch Specification"))
        self.verticalLayout.addWidget(self.labelSpec)

        self.listSpec = QListWidget()
        self.listSpec.setAlternatingRowColors(True)
        self.verticalLayout.addWidget(self.listSpec)

        # Basic Branch Process Data.
        self.labelSpec = QLabel(self.tr("Basic Process Data"))
        self.verticalLayout.addWidget(self.labelSpec)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        self.formLayout = QFormLayout()

        self.labelInsu = QLabel(self.tr("Insulation"))
        self.comboInsu = QComboBox()

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelInsu)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.comboInsu)

        self.labelTracing = QLabel(self.tr("Tracing"))
        self.comboTracing = QComboBox()

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelTracing)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.comboTracing)

        self.labelTemp = QLabel(self.tr("Temperature"))
        self.textTemp = QLineEdit("-10000.00")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelTemp)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.textTemp)

        self.labelPressure = QLabel(self.tr("Pressure"))
        self.textPressure = QLineEdit("0.00")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.labelPressure)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.textPressure)

        self.verticalLayout.addLayout(self.formLayout)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttonBox)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.initData()
    # setupUi

    def initData(self):
        # First clear all.
        self.listSpec.clear()
        self.comboInsu.clear()
        self.comboTracing.clear()

        self.comboInsu.addItem(self.tr('None'))
        self.comboTracing.addItem(self.tr('None'))

        # Set branch spec/insulation/tracing.
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
    # initData

    def setBranch(self, branch):
        # Set name.
        self.textName.text = branch.Name

        # Set spec.
        pspec = branch.Pspec
        if pspec.IsValid:
            specItems = self.listSpec.findItems(pspec.Name, Qt.MatchExactly)
            if len(specItems) == 1:
                self.listSpec.setCurrentItem(specItems[0])
            # if
        # if

        # Set insulation spec.
        ispec = branch.Ispec
        if ispec.IsValid:
            self.comboInsu.currentIndex = self.comboInsu.findText(ispec.Name)
        # if

        # Set tracing spec.
        tspec = branch.Tspec
        if tspec.IsValid:
            self.comboTracing.currentIndex = self.comboTracing.findText(tspec.Name)
        # if

        self.textTemp.text = str(branch.Temperature)
        self.textPressure.text = str(branch.Pressure)

        self.branch = branch

    # setBranch

    def modifyBranch(self):
        if self.branch is None:
            QMessageBox.warning(self, '', self.tr('Please select BRAN to modify!'))
            return
        # if

        try:
            Project.Current.OpenTransaction()

            self.branch.Name = self.textName.text
            self.branch.Pspec = self.listSpec.currentItem().data(Qt.UserRole)
            self.branch.Ispec = self.comboInsu.currentData
            self.branch.Tspec = self.comboTracing.currentData
            self.branch.Temperature = float(self.textTemp.text)
            self.branch.Pressure = float(self.textPressure.text)

            Project.Current.CommitTransaction()
        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # modifyBranch

    def accept(self):
        self.modifyBranch()

        QDialog.accept(self)
    # accept

# BranchDialog

# Branch head detail.
class HeadDetailDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Modify Head Detail"))

        self.verticalLayout = QVBoxLayout(self)

        self.formLayout = QFormLayout()

        # Name
        self.labelName = QLabel(self.tr('Name:'))
        self.textName = QLineEdit()
        self.textName.setMinimumWidth(180)
        self.textName.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelName)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textName)

        # Bore
        self.labelBore = QLabel(self.tr('Bore:'))
        self.comboBore = QComboBox()

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelBore)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.comboBore)

        # Connection
        self.labelConnection = QLabel(self.tr('Connection:'))
        self.comboConnection = QComboBox()

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelConnection)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.comboConnection)

        # Direction
        self.labelDirection = QLabel(self.tr('Direction:'))
        self.textDirection = QLineEdit()

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.labelDirection)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.textDirection)

        self.verticalLayout.addLayout(self.formLayout)

        self.labelPosition = QLabel(self.tr('Position Wrt World:'))
        self.verticalLayout.addWidget(self.labelPosition)

        self.linePosition = QFrame()
        self.linePosition.setFrameShape(QFrame.HLine)
        self.linePosition.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.linePosition)

        # Position
        self.formLayout = QFormLayout()

        self.labelPx = QLabel(self.tr('X'))
        self.textPx = QLineEdit()
        
        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelPx)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textPx)

        self.labelPy = QLabel(self.tr('Y'))
        self.textPy = QLineEdit()
        
        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelPy)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.textPy)

        self.labelPz = QLabel(self.tr('Z'))
        self.textPz = QLineEdit()
        
        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelPz)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.textPz)

        self.verticalLayout.addLayout(self.formLayout)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.initData()
    # setupUi

    def initData(self):
        pass
    # initData

    def setBranch(self, branch):
        self.textName.text = branch.Name
        self.textDirection.text = branch.Hdirection.ToString()

        pos = branch.Hposition
        self.textPx.text = str(pos.X)
        self.textPy.text = str(pos.Y)
        self.textPz.text = str(pos.Z)
    # setBranch

    def accept(self):
        QDialog.accept(self)
    # accept
# HeadDetailDialog

# Branch head connection.
class HeadConnectionDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Modify Head Connection"))
        #self.resize(500, 360)

        self.verticalLayout = QVBoxLayout(self)

        self.formLayout = QFormLayout()

        # Name
        self.labelName = QLabel(self.tr('Name:'))
        self.textName = QLineEdit()

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelName)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textName)

        self.verticalLayout.addLayout(self.formLayout)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
    # setupUi

    def setBranch(self, branch):
        pass
    # setBranch

    def accept(self):
        QDialog.accept(self)
    # accept
# HeadConnectionDialog

# Branch tail detail.

# Branch tail connection.


class BranchWidget(QDockWidget):
    def __init__(self, parent = None):
        QDockWidget.__init__(self, parent)

        self.pipe = None

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def hideWidgets(self, visibility):
        if not visibility:
            self.dlgHeadDetail.hide()
            self.dlgHeadConnection.hide()
        # if
    # hideWidgets

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Branch"))
        self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.visibilityChanged.connect(self.hideWidgets)

        self.dlgHeadDetail = HeadDetailDialog(self)
        self.dlgHeadConnection = HeadConnectionDialog(self)

        self.dockContext = QWidget()
        self.verticalLayout = QVBoxLayout(self.dockContext)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Pipe name
        self.horizontalLayout = QHBoxLayout()
        self.labelPipe = QLabel(self.tr("Pipe:"))
        self.labelPipe.setSizePolicy(sizePolicy)

        self.textPipe = QLabel("")
        self.textPipe.setStyleSheet('color:purple;')
        self.buttonPipe = QPushButton(self.tr("Set Pipe"))
        self.buttonPipe.setSizePolicy(sizePolicy)
        self.buttonPipe.clicked.connect(self.setPipe)

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
        self.labelSpec = QLabel(self.tr("Spec:"))
        self.labelSpec.setSizePolicy(sizePolicy)
        self.textSpec = QLabel("")
        self.textSpec.setStyleSheet('color:purple;')
        self.buttonSpec = QPushButton(self.tr("Set Detail"))
        self.buttonSpec.setSizePolicy(sizePolicy)
        self.buttonSpec.clicked.connect(self.modifyPipe)

        self.horizontalLayout.addWidget(self.labelSpec)
        self.horizontalLayout.addWidget(self.textSpec)
        self.horizontalLayout.addWidget(self.buttonSpec)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Branch Table.
        self.tableBranch = QTableWidget()
        self.tableBranch.setColumnCount(3)
        self.tableBranch.setHorizontalHeaderLabels([self.tr('Branch'), self.tr('Head'), self.tr('Tail')])
        self.tableBranch.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableBranch.setAlternatingRowColors(True)
        self.tableBranch.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableBranch.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableBranch.setGridStyle(Qt.SolidLine)
        self.tableBranch.horizontalHeader().setStretchLastSection(True)
        self.tableBranch.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableBranch.verticalHeader().setMinimumSectionSize(16)
        self.tableBranch.verticalHeader().setDefaultSectionSize(18)
        self.tableBranch.verticalHeader().hide() 
        self.tableBranch.itemSelectionChanged.connect(self.currentBranchChanged)
        self.verticalLayout.addWidget(self.tableBranch)

        # New Branch.
        self.horizontalLayout = QHBoxLayout()
        self.buttonBranch = QPushButton(self.tr("New Branch"))
        self.buttonBranch.clicked.connect(self.createBranch)
        self.horizontalLayout.addWidget(self.buttonBranch)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Current Branch
        self.horizontalLayout = QHBoxLayout()
        self.labelBranch = QLabel(self.tr("Branch:"))
        self.labelBranch.setSizePolicy(sizePolicy)
        self.textBranch = QLabel()
        self.textBranch.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelBranch)
        self.horizontalLayout.addWidget(self.textBranch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.lineBranchDetail = QFrame()
        self.lineBranchDetail.setFrameShape(QFrame.HLine)
        self.lineBranchDetail.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.lineBranchDetail)

        # Branch spec
        self.horizontalLayout = QHBoxLayout()
        self.labelBranchSpec = QLabel(self.tr("Spec:"))
        self.labelBranchSpec.setSizePolicy(sizePolicy)
        self.textBranchSpec = QLabel()
        self.textBranchSpec.setStyleSheet('color:purple;')
        self.buttonBranchSpec = QPushButton(self.tr("Set Detail"))
        self.buttonBranchSpec.setSizePolicy(sizePolicy)
        self.buttonBranchSpec.clicked.connect(self.modifyBranch)

        self.horizontalLayout.addWidget(self.labelBranchSpec)
        self.horizontalLayout.addWidget(self.textBranchSpec)
        self.horizontalLayout.addWidget(self.buttonBranchSpec)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Head Detail
        self.lableHeadDetail = QLabel(self.tr("Head Detail:"))
        self.lineHeadDetail = QFrame()
        self.lineHeadDetail.setFrameShape(QFrame.HLine)
        self.lineHeadDetail.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.lableHeadDetail)
        self.verticalLayout.addWidget(self.lineHeadDetail)

        self.horizontalLayout = QHBoxLayout()
        self.labelHeadBore = QLabel(self.tr("Bore:"))
        self.labelHeadBore.setSizePolicy(sizePolicy)
        self.textHeadBore = QLabel()
        self.textHeadBore.setStyleSheet('color:purple;')
        self.labelHeadType = QLabel(self.tr("Connection:"))
        self.labelHeadType.setSizePolicy(sizePolicy)
        self.textHeadType = QLabel()
        self.textHeadType.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelHeadBore)
        self.horizontalLayout.addWidget(self.textHeadBore)
        self.horizontalLayout.addWidget(self.labelHeadType)
        self.horizontalLayout.addWidget(self.textHeadType)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()

        self.labelHeadDirection = QLabel(self.tr("Direction:"))
        self.labelHeadDirection.setSizePolicy(sizePolicy)
        self.textHeadDirection = QLabel()
        self.textHeadDirection.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelHeadDirection)
        self.horizontalLayout.addWidget(self.textHeadDirection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelHeadPosition = QLabel(self.tr("Position:"))
        self.labelHeadPosition.setSizePolicy(sizePolicy)
        self.textHeadPosition = QLabel()
        self.textHeadPosition.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelHeadPosition)
        self.horizontalLayout.addWidget(self.textHeadPosition)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonChangeHead = QPushButton(self.tr("Change"))
        self.buttonChangeHead.setSizePolicy(sizePolicy)
        self.buttonChangeHead.clicked.connect(self.changeHeadDetail)
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
        self.textHeadConnection.setStyleSheet('color:purple;')
        self.buttonHeadConnection = QPushButton(self.tr("Change"))
        self.buttonHeadConnection.clicked.connect(self.changeHeadConnection)
        self.buttonHeadConnection.setSizePolicy(sizePolicy)
        self.horizontalLayout.addWidget(self.textHeadConnection)
        self.horizontalLayout.addWidget(self.buttonHeadConnection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Tail Detail
        self.lableTailDetail = QLabel(self.tr("Tail Detail:"))
        self.lineTailDetail = QFrame()
        self.lineTailDetail.setFrameShape(QFrame.HLine)
        self.lineTailDetail.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.lableTailDetail)
        self.verticalLayout.addWidget(self.lineTailDetail)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailBore = QLabel(self.tr("Bore:"))
        self.labelTailBore.setSizePolicy(sizePolicy)
        self.textTailBore = QLabel()
        self.textTailBore.setStyleSheet('color:purple;')
        self.labelTailType = QLabel(self.tr("Connection:"))
        self.labelTailType.setSizePolicy(sizePolicy)
        self.textTailType = QLabel()
        self.textTailType.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelTailBore)
        self.horizontalLayout.addWidget(self.textTailBore)
        self.horizontalLayout.addWidget(self.labelTailType)
        self.horizontalLayout.addWidget(self.textTailType)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailDirection = QLabel(self.tr("Direction:"))
        self.labelTailDirection.setSizePolicy(sizePolicy)
        self.textTailDirection = QLabel()
        self.textTailDirection.setStyleSheet('color:purple;')
        self.horizontalLayout.addWidget(self.labelTailDirection)
        self.horizontalLayout.addWidget(self.textTailDirection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.labelTailPosition = QLabel(self.tr("Position:"))
        self.labelTailPosition.setSizePolicy(sizePolicy)
        self.textTailPosition = QLabel()
        self.textTailPosition.setStyleSheet('color:purple;')
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
        self.textTailConnection.setStyleSheet('color:purple;')
        self.buttonTailConnection = QPushButton(self.tr("Change"))
        self.buttonTailConnection.setSizePolicy(sizePolicy)
        #self.buttonTailConnection.clicked.connect(self.changeTailConnection)
        self.horizontalLayout.addWidget(self.textTailConnection)
        self.horizontalLayout.addWidget(self.buttonTailConnection)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Set dock widget.
        self.setWidget(self.dockContext)

    # setupUi

    def initPipe(self, pipe):

        self.textPipe.text = pipe.Name

        pspec = pipe.Pspec
        if pspec.IsValid:
            self.textSpec.text = pspec.Name
        # if

        self.pipe = pipe
    # initPipe

    def initBranch(self, isFirst = True):
        if self.pipe is None:
            return
        # if

        self.textBranch.text = ''
        self.textBranchSpec.text = ''

        self.textHeadBore.text = ''
        self.textHeadType.text = ''
        self.textHeadDirection.text = ''
        self.textHeadPosition.text = ''
        self.textHeadConnection.text = ''

        self.textTailBore.text = ''
        self.textTailType.text = ''
        self.textTailDirection.text = ''
        self.textTailPosition.text = ''
        self.textTailConnection.text = ''

        branches = self.pipe.Members
        size = len(branches)
        self.tableBranch.setRowCount(size)

        for i in range (size):
            branch = branches[i]
            name = branch.Name
            href = branch.Href
            tref = branch.Tref

            if name == '':
                name = f'[{i + 1}]'
            # if
            self.tableBranch.setItem(i, 0, QTableWidgetItem(name))

            if href.IsValid:
                self.tableBranch.setItem(i, 1, QTableWidgetItem(href.Name))
            else:
                self.tableBranch.setItem(i, 1, QTableWidgetItem(self.tr('Undefined')))
            # if

            if tref.IsValid:
                self.tableBranch.setItem(i, 2, QTableWidgetItem(tref.Name))
            else:
                self.tableBranch.setItem(i, 2, QTableWidgetItem(self.tr('Undefined')))
            # if
        # for

        if size > 0:
            if isFirst:
                self.setCurrentBranch(branches[0])
            else:
                self.setCurrentBranch(branches[size])
            # if
        # if
    # initBranch

    def setCurrentBranch(self, branch):
        self.textBranch.text = branch.Name

        pspec = branch.Pspec
        if pspec.IsValid:
            self.textBranchSpec.text = pspec.Name
        # if

        # Head detail
        self.setHeadDetail(branch)

        # Tail detail
        self.setTailDetail(branch)

    # setCurrentBranch

    def setPipe(self):
        self.pipe = None

        ce = DbElement.Current
        if ce.Type != 'PIPE':
            QMessageBox.warning(self, '', self.tr('Please select PIPE to modify!'))
            return
        # if

        self.initPipe(ce)
        self.initBranch()

    # setPipe

    def resetPipe(self, pipe):
        self.initPipe(pipe)
        self.initBranch()
    # resetPipe

    def modifyPipe(self):
        if self.pipe is None:
            QMessageBox.warning(self, '', self.tr('Please set pipe to change detail!'))
        # if

        pipeDlg = PipeDialog(self)
        pipeDlg.setPipe(self.pipe)
        if pipeDlg.exec() == QDialog.Accepted:
            self.setPipe(self.pipe)
        # if
    # modifyPipe

    def createBranch(self):
        if self.pipe is None:
            return
        # if

        branch = self.pipe.CreateLast('BRAN')

        self.initBranch(False)
    # createBranch

    def currentBranchChanged(self):
        index = self.tableBranch.currentRow()
        if index < 0:
            return
        # if
        branch = self.pipe.Members[index]
        self.setCurrentBranch(branch)
    # currentBranchChanged

    def modifyBranch(self):
        index = self.tableBranch.currentRow()
        if index < 0:
            return
        # if
        branch = self.pipe.Members[index]

        branchDlg = BranchDialog(self)
        branchDlg.setBranch(branch)
        branchDlg.exec()
    # modifyBranch

    def setHeadDetail(self, branch):
        self.textHeadBore.text = str(branch.Hbore)
        self.textHeadType.text = branch.Hconnect
        self.textHeadDirection.text = branch.Hdirection.ToString()
        self.textHeadPosition.text = branch.Hposition.ToString()

        href = branch.Href
        if href.IsValid:
            self.textHeadConnection.text = href.Name
        else:
            self.textHeadConnection.text = self.tr('Undefined')
        # if
    # setHeadDetail

    def setTailDetail(self, branch):
        self.textTailBore.text = str(branch.Tbore)
        self.textTailType.text = branch.Tconnect
        self.textTailDirection.text = branch.Tdirection.ToString()
        self.textTailPosition.text = branch.Tposition.ToString()

        tref = branch.Tref
        if tref.IsValid:
            self.textTailConnection.text = tref.Name
        else:
            self.textTailConnection.text = self.tr('Undefined')
        # if
    # setTailDetail

    def changeHeadDetail(self):
        index = self.tableBranch.currentRow()
        if index < 0:
            return
        # if
        
        branch = self.pipe.Members[index]

        self.dlgHeadDetail.setBranch(branch)
        self.dlgHeadDetail.show()
    # changeHeadDetail

    def changeHeadConnection(self):
        self.dlgHeadConnection.show()
    # changeHeadConnection

    def changeTailDetail(self):
        pass
    # changeTailDetail

    def changeTailConnection(self):
        pass
    # changeTailConnection

# BranchWidget

branchWidget = BranchWidget(MainWindow)

def CreateBranch():
    MainWindow.addDockWidget(Qt.RightDockWidgetArea, branchWidget)

    ce = DbElement.Current
    if ce.Type == 'PIPE':
        branchWidget.resetPipe(ce)
    # if

    branchWidget.show()
# CreateBranch
