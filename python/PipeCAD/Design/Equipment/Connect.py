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
# Date: 11:20 2026-11-18

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.Graphics import *
from PipeCAD.GUI import MainWindow


class ExplicitDialog(QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)

        self.fromElement = None
        self.fromTag = Aid.NextNumber()

        self.toElement = None
        self.toTag = Aid.NextNumber()

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def setupUi(self):
        self.setWindowTitle(self.tr("Explicit P-Point Connection"))

        self.verticalLayout = QVBoxLayout(self)

        # Grid layout.
        self.gridLayout = QGridLayout()

        self.buttonCE1 = QPushButton(self.tr('CE'))
        self.buttonCE1.clicked.connect(self.setElement1)
        self.labelPoint1 = QLabel(self.tr("Connect Point"))
        self.comboPoint1 = QComboBox()
        self.comboPoint1.setMinimumWidth(60)
        self.comboPoint1.currentIndexChanged.connect(self.point1Changed)
        self.labelItem1 = QLabel(self.tr('Unset'))
        self.labelItem1.setMinimumWidth(160)

        self.gridLayout.addWidget(self.buttonCE1, 0, 0)
        self.gridLayout.addWidget(self.labelPoint1, 0, 1)
        self.gridLayout.addWidget(self.comboPoint1, 0, 2)
        self.gridLayout.addWidget(self.labelItem1, 0, 3)

        self.buttonCE2 = QPushButton(self.tr('CE'))
        self.buttonCE2.clicked.connect(self.setElement2)
        self.labelPoint2 = QLabel(self.tr("To Point"))
        self.comboPoint2 = QComboBox()
        self.comboPoint2.currentIndexChanged.connect(self.point2Changed)
        self.labelItem2 = QLabel(self.tr('Unset'))

        self.gridLayout.addWidget(self.buttonCE2, 1, 0)
        self.gridLayout.addWidget(self.labelPoint2, 1, 1)
        self.gridLayout.addWidget(self.comboPoint2, 1, 2)
        self.gridLayout.addWidget(self.labelItem2, 1, 3)

        self.verticalLayout.addLayout(self.gridLayout)

        # Action buttons.
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.verticalLayout.addWidget(self.buttonBox)
    # setupUi

    def setElement1(self):
        ce = DbElement.Current
        if not ce.IsValid:
            return
        # if

        self.fromElement = ce

        id = ce.Id
        name = ce.Name
        type = ce.Type

        if not name:
            self.labelItem1.text = '%s %d' % (type, id)
        else:
            self.labelItem1.text = '%s %s' % (type, name)
        # if

        self.comboPoint1.clear()
        for i in range(7):
            key = 'P%d' % i
            try:
                ce.GetPosition('PPosition', i)
                self.comboPoint1.addItem(key)
            except Exception as ex:
                pass
            # try
        # for
    # setElement1

    def setElement2(self):
        ce = DbElement.Current
        if not ce.IsValid:
            return
        # if

        self.toElement = ce

        id = ce.Id
        name = ce.Name
        type = ce.Type

        if not name:
            self.labelItem2.text = '%s %d' % (type, id)
        else:
            self.labelItem2.text = '%s %s' % (type, name)
        # if

        self.comboPoint2.clear()
        for i in range(7):
            key = 'P%d' % i
            try:
                ce.GetPosition('PPosition', i)
                self.comboPoint2.addItem(key)
            except Exception as ex:
                pass
            # try
        # for
    # setElement2

    def point1Changed(self):
        idx = self.comboPoint1.currentIndex
        if idx < 0:
            return
        # if

        pos = self.fromElement.GetPosition('Pposition', idx, Project.World)
        dir = self.fromElement.GetDirection('Pdirection', idx, Project.World)

        Aid.AddAxis(pos, dir, self.fromTag)
        Aid.Update()
    # point1Changed

    def point2Changed(self):
        idx = self.comboPoint2.currentIndex
        if idx < 0:
            return
        # if

        pos = self.toElement.GetPosition('Pposition', idx, Project.World)
        dir = self.toElement.GetDirection('Pdirection', idx, Project.World)

        Aid.AddAxis(pos, dir, self.toTag)
        Aid.Update()
    # point2Changed

    def reject(self):
        Aid.Remove(self.fromTag)
        Aid.Remove(self.toTag)
        Aid.Update()

        QDialog.reject(self)
    # reject

    def accept(self):

        if self.fromElement is None or self.toElement is None:
            QMessageBox.warning(self, '', self.tr('Please set the element you want to connect!'))
            return
        # if

        fromIndex = self.comboPoint1.currentIndex
        toIndex = self.comboPoint2.currentIndex

        try:
            self.fromElement.Connect(self.toElement, fromIndex, toIndex)
        except Exception as ex:
            QMessageBox.warning(self, '', ex)
            return
        # try

        Aid.Remove(self.fromTag)
        Aid.Remove(self.toTag)
        Aid.Update()

        QDialog.accept(self)
    # accept

# ExplicitDialog

def ConnectExplicit():
    explicitDialog = ExplicitDialog(MainWindow)
    explicitDialog.show()
# ConnectExplicit
