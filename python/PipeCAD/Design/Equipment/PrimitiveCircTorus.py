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
# Date: 21:00 2026-11-21

from PythonQt.QtCore import *
from PythonQt.QtGui import *
from PythonQt.QtSvg import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow

class CircTorusDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Circular Torus"))

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

        self.labelNegative = QLabel(self.tr("Negative"))
        self.checkNegative = QCheckBox()

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelNegative)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.checkNegative)

        self.verticalLayout.addLayout(self.formLayout)

        # Horizontal Line
        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        # Dimensions.
        self.formLayout = QFormLayout()

        self.labelRinside = QLabel(self.tr("Inside Radius"))
        self.textRinside = QLineEdit("0.0")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.labelRinside)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.textRinside)

        self.labelRoutside = QLabel(self.tr("Outside Radius"))
        self.textRoutside = QLineEdit("0.0")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.labelRoutside)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.textRoutside)

        self.labelAngle = QLabel(self.tr("Angle"))
        self.textAngle = QLineEdit("0.0")

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.labelAngle)
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.textAngle)

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
        self.svgDiagram = QSvgWidget(':/icons/diagram_torus.svg')
        self.horizontalLayout.addWidget(self.svgDiagram)
    # setupUi

    def activateName(self):
        index = self.comboName.currentIndex
        if index != 0:
            torus = DbElement.Current
            if torus.Type != 'CTOR':
                QMessageBox.warning(self, '', self.tr('Please select circular torus to modify!'))
                return
            # if
            
            pos = torus.Position
            self.textPx.text = str(pos.X)
            self.textPy.text = str(pos.Y)
            self.textPz.text = str(pos.Z)
            
            self.textRinside.text = str(torus.Rinside)
            self.textRoutside.text = str(torus.Routside)
            self.textAngle.text = str(torus.Angle)
        # if
    # activateName

    def create(self):

        try:
            px = float(self.textPx.text)
            py = float(self.textPy.text)
            pz = float(self.textPz.text)

            ri = float(self.textRinside.text)
            ro = float(self.textRoutside.text)
            a = float(self.textAngle.text)

            Project.Current.OpenTransaction()

            torus = DbElement.Current.Create(0, 'CTOR')
            torus.Name = self.textName.text
            torus.Position = Position(px, py, pz)
            torus.Routside = ro
            torus.Rinside = ri
            torus.Angle = a

            Project.Current.CommitTransaction()

        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # create

    def modify(self):

        try:
            px = float(self.textPx.text)
            py = float(self.textPy.text)
            pz = float(self.textPz.text)

            ri = float(self.textRinside.text)
            ro = float(self.textRoutside.text)
            a = float(self.textAngle.text)

            Project.Current.OpenTransaction()

            torus = DbElement.Current
            torus.Name = self.textName.text
            torus.Position = Position(px, py, pz)
            torus.Routside = ro
            torus.Rinside = ri
            torus.Angle = a

            Project.Current.CommitTransaction()

        except Exception as ex:
            QMessageBox.critical(self, '', ex)
            Project.Current.AbortTransaction()
        # try
    # modify

    def accept(self):
        index = self.comboName.currentIndex
        if index == 0:
            self.create()
        else:
            self.modify()
        # if

        QDialog.accept(self)
    # accept

# CircTorusDialog

torusDialog = CircTorusDialog(MainWindow)

def Create():
    torusDialog.show()
# Create
