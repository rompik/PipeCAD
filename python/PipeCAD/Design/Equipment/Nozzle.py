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
# Date: 11:20 2026-11-03

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow

class NozzleDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Nozzle"))

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

        # Dimensions.
        self.formLayout = QFormLayout()

        self.labelSpec = QLabel(self.tr("Specification"))
        self.comboSpec = QComboBox()
        self.comboSpec.currentIndexChanged.connect(self.specChanged)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelSpec)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.comboSpec)
        
        self.labelGtype = QLabel(self.tr("Generic Type"))
        self.comboGtype = QComboBox()
        self.comboGtype.currentIndexChanged.connect(self.gtypeChanged)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelGtype)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.comboGtype)
        
        self.labelBore = QLabel(self.tr("Bore"))
        self.comboBore = QComboBox()

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelBore)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.comboBore)

        self.labelHeight = QLabel(self.tr("Height"))
        self.textHeight = QLineEdit("100.0")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.labelHeight)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.textHeight)

        self.labelTemp = QLabel(self.tr("Temperature"))
        self.textTemp = QLineEdit("0.0")

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.labelTemp)
        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.textTemp)

        self.labelPressure = QLabel(self.tr("Pressure"))
        self.textPressure = QLineEdit("0.0")

        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.labelPressure)
        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.textPressure)

        self.labelDescription = QLabel(self.tr("Description"))
        self.textDescription = QLineEdit("")

        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.labelDescription)
        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.textDescription)

        self.labelPurpose = QLabel(self.tr("Purpose"))
        self.textPurpose = QLineEdit("")

        self.formLayout.setWidget(7, QFormLayout.LabelRole, self.labelPurpose)
        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.textPurpose)

        self.verticalLayout.addLayout(self.formLayout)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        # Position.
        self.formLayout = QFormLayout()

        self.labelPx = QLabel(self.tr("East"))
        self.textPx = QLineEdit("0.0")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelPx)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textPx)

        self.labelPy = QLabel(self.tr("North"))
        self.textPy = QLineEdit("0.0")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelPy)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.textPy)

        self.labelPz = QLabel(self.tr("Up"))
        self.textPz = QLineEdit("0.0")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelPz)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.textPz)

        self.labelP1 = QLabel(self.tr("P1"))
        self.textP1 = QLineEdit("N")

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.labelP1)
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.textP1)

        self.verticalLayout.addLayout(self.formLayout)

        # Vertical Spacer.
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(self.verticalSpacer)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttonBox)

        self.horizontalLayout.addLayout(self.verticalLayout)

        # Diagram
        self.labelDiagram = QLabel()
        self.labelDiagram.setMinimumSize(QSize(280, 360))
        self.labelDiagram.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.labelDiagram.setPixmap(QPixmap(":/icons/diagram_nozzle.svg"))
        self.horizontalLayout.addWidget(self.labelDiagram)

        # Init nozzle spec.
        self.initNozzleSpec()
    # setupUi

    def initNozzleSpec(self):
        typeFilter = TypeFilter('SPEC')
        
        collection = DbElementCollection(Project.World, typeFilter)
        specList = collection.Collect()
        for specElement in specList:
            if specElement.Purpose == 'NOZZ':
                self.comboSpec.addItem(specElement.Description, specElement)
            #if
        # for

        self.specChanged()
    # initNozzleSpec

    def specChanged(self):
        self.comboGtype.clear()

        specElement = self.comboSpec.currentData
        if specElement is None:
            return
        # if

        typeFilter = TypeFilter('SELE')
        collection = DbElementCollection(specElement, typeFilter)
        seleList = collection.Collect()

        for seleElement in seleList:
            self.comboGtype.addItem(seleElement.Description, seleElement)
        # for

        self.gtypeChanged()
    # specChanged

    def gtypeChanged(self):
        self.comboBore.clear()

        seleElement = self.comboGtype.currentData
        if seleElement is None:
            return
        # if

        typeFilter = TypeFilter('SPCO')

        collection = DbElementCollection(seleElement, typeFilter)
        spcoList = collection.Collect()

        for spcoElement in spcoList:
            scomElement = spcoElement.Catref
            if scomElement.IsValid:
                param = scomElement.Param
                if len(param) > 0:
                    self.comboBore.addItem(str(param[0]), scomElement)
                # if
            # if
        # for
    # gtypeChanged

    def activateName(self):
        index = self.comboName.currentIndex
        if index != 0:
            self.setWindowTitle(self.tr("Modify Nozzle"))

            nozzle = DbElement.Current
            if nozzle.Type != 'NOZZ':
                QMessageBox.warning(self, '', self.tr('Please select Nozzle to modify!'))
                return
            # if

            # Set bore and spec.
            scomElement = nozzle.Catref
            if scomElement.IsValid:
                print(scomElement.Name)
                param = scomElement.Param
                if len(param) > 0:
                    print(str(param[0]))
                    self.comboBore.currentText = str(param[0])
                # if
            # if

            pos = nozzle.Position
            self.textPx.text = str(pos.X)
            self.textPy.text = str(pos.Y)
            self.textPz.text = str(pos.Z)

            self.textHeight.text = str(nozzle.Height)
            self.textTemp.text = str(nozzle.Temperature)
            self.textPressure.text = str(nozzle.Pressure)
            self.textDescription.text = nozzle.Description
            self.textPurpose.text = nozzle.Purpose
        else:
            self.setWindowTitle(self.tr("Create Nozzle"))
        # if
    # activateName

    def setNozzle(self):
        self.comboName.currentIndex = 1
        self.activateName()
    # setNozzle

    def createNozzle(self):

        spcoElement = self.comboBore.currentData
        if spcoElement is None:
            QMessageBox.warning(self, '', self.tr('Please set nozzle Spec!'))
            return
        # if

        try:
            height = float(self.textHeight.text)

            px = float(self.textPx.text)
            py = float(self.textPy.text)
            pz = float(self.textPz.text)

            Project.Current.OpenTransaction()

            nozzle = DbElement.Current.Create(0, 'NOZZ')
            nozzle.Name = self.textName.text
            nozzle.Position = Position(px, py, pz)
            nozzle.Height = height
            nozzle.Catref = spcoElement
            nozzle.Purpose = self.textPurpose.text
            nozzle.Description = self.textDescription.text

            Project.Current.CommitTransaction()

        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # createNozzle

    def modifyNozzle(self):
        nozzle = DbElement.Current

        try:
            height = float(self.textHeight.text)

            px = float(self.textPx.text)
            py = float(self.textPy.text)
            pz = float(self.textPz.text)

            Project.Current.OpenTransaction()

            nozzle = DbElement.Current
            nozzle.Position = Position(px, py, pz)
            nozzle.Height = height

            Project.Current.CommitTransaction()

        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # modifyNozzle

    def accept(self):
        index = self.comboName.currentIndex
        if index == 0:
            self.createNozzle()
        else:
            self.modifyNozzle()
        # if

        QDialog.accept(self)
    # accept

# NozzleDialog

nozzleDialog = NozzleDialog(MainWindow)

def Create():
    nozzleDialog.show()
# Create

def Modify():
    nozzleDialog.setNozzle()
    nozzleDialog.show()
# Modify
