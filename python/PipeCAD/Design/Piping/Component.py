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
# Date: 13:06 2026-11-15

from PythonQt.QtCore import *
from PythonQt.QtGui import *

from PipeCAD.Geometry import *
from PipeCAD.Database import *
from PipeCAD.GUI import MainWindow

class ComponentWidget(QDockWidget):
    def __init__(self, parent = None):
        QDockWidget.__init__(self, parent)

        self.branch = None
        self.component = None

        self.setupUi()
    # __init__

    def tr(self, text, comment = None):
        return QCoreApplication.translate(self.__class__.__name__, text, comment)
    # tr

    def hideDockWidget(self, visibility):
        if not visibility:
            # Dock hide.
            pass
        # if
    # hideDockWidget

    def setupUi(self):
        self.setWindowTitle(self.tr("Create Component"))
        self.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.visibilityChanged.connect(self.hideDockWidget)

        self.dockContext = QWidget()
        self.verticalLayout = QVBoxLayout(self.dockContext)

        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Branch name
        self.horizontalLayout = QHBoxLayout()
        self.labelBranch = QLabel(self.tr("Branch:"))
        self.labelBranch.setSizePolicy(sizePolicy)

        self.textBranch = QLabel("")
        self.textBranch.setStyleSheet('color:purple;')
        self.buttonBranch = QPushButton(self.tr("Set Branch"))
        self.buttonBranch.setSizePolicy(sizePolicy)
        self.buttonBranch.clicked.connect(self.setBranch)

        self.horizontalLayout.addWidget(self.labelBranch)
        self.horizontalLayout.addWidget(self.textBranch)
        self.horizontalLayout.addWidget(self.buttonBranch)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape(QFrame.HLine)
        self.separatorLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.separatorLine)

        # Branch spec
        self.horizontalLayout = QHBoxLayout()

        self.labelSpec = QLabel(self.tr("Spec:"))
        self.labelSpec.setSizePolicy(sizePolicy)
        self.textSpec = QLabel("")
        self.textSpec.setStyleSheet('color:purple;')

        self.labelBore = QLabel(self.tr('Bore:'))
        self.labelBore.setSizePolicy(sizePolicy)
        self.textBore = QLabel('')
        self.textBore.setStyleSheet('color:purple;')

        self.horizontalLayout.addWidget(self.labelSpec)
        self.horizontalLayout.addWidget(self.textSpec)
        self.horizontalLayout.addWidget(self.labelBore)
        self.horizontalLayout.addWidget(self.textBore)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape(QFrame.HLine)
        self.separatorLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.separatorLine)

        # Type and Sub-Type Filter.
        self.formLayout = QFormLayout()

        self.comboType = QComboBox()
        self.comboType.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
        self.comboType.currentTextChanged.connect(self.typeChanged)

        self.comboFilter = QComboBox()
        self.comboFilter.currentTextChanged.connect(self.subTypeChanged)

        self.formLayout.addRow(self.tr("Type"), self.comboType)
        self.formLayout.addRow(self.tr("SType"), self.comboFilter)

        self.verticalLayout.addLayout(self.formLayout)

        # Component Table.
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels([self.tr('Bore'), self.tr('SType'), self.tr('Description')])
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setGridStyle(Qt.SolidLine)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.verticalHeader().setMinimumSectionSize(16)
        self.tableWidget.verticalHeader().setDefaultSectionSize(18)
        self.tableWidget.verticalHeader().hide()

        self.verticalLayout.addWidget(self.tableWidget)

        # Reducer Info.
        self.reducerInfo = QGroupBox(self.tr("Reducer Infomation"))

        self.horizontalLayout = QHBoxLayout(self.reducerInfo)
        self.labelLeaveBore = QLabel(self.tr("Leave Bore"))
        self.comboLeaveBore = QComboBox()
        self.buttonReducer12 = QPushButton()
        self.buttonReducer21 = QPushButton()

        self.buttonGroup = QButtonGroup(self.reducerInfo)
        self.buttonGroup.addButton(self.buttonReducer12)
        self.buttonGroup.addButton(self.buttonReducer21)

        self.buttonReducer12.setCheckable(True)
        self.buttonReducer21.setCheckable(True)

        self.buttonReducer12.setChecked(True)

        self.buttonReducer12.setMaximumWidth(24)
        self.buttonReducer21.setMaximumWidth(24)

        self.buttonReducer12.setToolTip(self.tr("Arrive major bore, leave minor bore"))
        self.buttonReducer21.setToolTip(self.tr("Arrive minor bore, leave major bore"))

        self.buttonReducer12.setIcon(QIcon(":/icons/redu21.svg"))
        self.buttonReducer21.setIcon(QIcon(":/icons/redu12.svg"))

        #self.buttonReducer12.clicked.connect(lambda: self.setArriveLeave(1, 2))
        #self.buttonReducer21.clicked.connect(lambda: self.setArriveLeave(2, 1))

        self.horizontalSpacer = QSpacerItem(16, 16, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addWidget(self.labelLeaveBore)
        self.horizontalLayout.addWidget(self.comboLeaveBore)
        self.horizontalLayout.addWidget(self.buttonReducer12)
        self.horizontalLayout.addWidget(self.buttonReducer21)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout.addWidget(self.reducerInfo)

        # Tee Info.
        self.connectionInfo = QGroupBox(self.tr("Connection Infomation"))
        self.horizontalLayout = QHBoxLayout(self.connectionInfo)
        self.labelConnectBore = QLabel(self.tr("Conn. Bore"))
        self.comboConnectBore = QComboBox()
        self.buttonConnect1 = QPushButton()
        self.buttonConnect2 = QPushButton()
        self.buttonConnect3 = QPushButton()

        self.buttonGroup = QButtonGroup(self.connectionInfo)
        self.buttonGroup.addButton(self.buttonConnect1)
        self.buttonGroup.addButton(self.buttonConnect2)
        self.buttonGroup.addButton(self.buttonConnect3)

        self.buttonConnect1.setCheckable(True)
        self.buttonConnect2.setCheckable(True)
        self.buttonConnect3.setCheckable(True)

        self.buttonConnect1.setChecked(True)

        self.buttonConnect1.setMaximumWidth(24)
        self.buttonConnect2.setMaximumWidth(24)
        self.buttonConnect3.setMaximumWidth(24)

        self.buttonConnect1.setToolTip(self.tr("Flow through tee"))
        self.buttonConnect2.setToolTip(self.tr("Leave by connection"))
        self.buttonConnect3.setToolTip(self.tr("Arrive by connection"))

        self.buttonConnect1.setIcon(QIcon(":/icons/tee12.svg"))
        self.buttonConnect2.setIcon(QIcon(":/icons/tee13.svg"))
        self.buttonConnect3.setIcon(QIcon(":/icons/tee32.svg"))

        #self.buttonConnect1.clicked.connect(lambda: self.setArriveLeave(1, 2))
        #self.buttonConnect2.clicked.connect(lambda: self.setArriveLeave(1, 3))
        #self.buttonConnect3.clicked.connect(lambda: self.setArriveLeave(3, 1))

        self.horizontalSpacer = QSpacerItem(16, 16, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addWidget(self.labelConnectBore)
        self.horizontalLayout.addWidget(self.comboConnectBore)
        self.horizontalLayout.addWidget(self.buttonConnect1)
        self.horizontalLayout.addWidget(self.buttonConnect2)
        self.horizontalLayout.addWidget(self.buttonConnect3)
        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout.addWidget(self.connectionInfo)

        # Creation from
        self.horizontalLayout = QHBoxLayout()
        self.labelCreation = QLabel(self.tr("Creation from "))
        self.labelCreation.setSizePolicy(sizePolicy)
        self.textCreation = QLabel()
        self.horizontalLayout.addWidget(self.labelCreation)
        self.horizontalLayout.addWidget(self.textCreation)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLine = QFrame()
        self.horizontalLine.setFrameShape(QFrame.HLine)
        self.horizontalLine.setFrameShadow(QFrame.Sunken)
        self.verticalLayout.addWidget(self.horizontalLine)

        self.horizontalLayout = QHBoxLayout()
        self.radioForwards = QRadioButton(self.tr("Forwards"))
        self.radioBackwards = QRadioButton(self.tr("Backwards"))
        self.radioForwards.setChecked(True)

        #self.radioForwards.toggled.connect(self.currentItemChanged)
        #self.radioBackwards.toggled.connect(self.currentItemChanged)

        self.horizontalLayout.addWidget(self.radioForwards)
        self.horizontalLayout.addWidget(self.radioBackwards)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.buttonConnect = QPushButton(self.tr("Connect"))
        self.buttonPlace = QPushButton(self.tr("Place"))
        self.buttonPlace.setToolTip(self.tr("Place component in tube line"))
        self.buttonFlip = QPushButton(self.tr("Flip"))

        #self.buttonConnect.clicked.connect(self.connectComponent)
        #self.buttonPlace.clicked.connect(self.placeComponent)
        #self.buttonFlip.clicked.connect(self.flipComponent)

        self.horizontalLayout.addWidget(self.buttonConnect)
        self.horizontalLayout.addWidget(self.buttonPlace)
        self.horizontalLayout.addWidget(self.buttonFlip)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Location Tool.
        self.groupBox = QGroupBox(self.tr("Location"))
        self.formLayout = QFormLayout(self.groupBox)

        self.comboRotate = QComboBox()
        self.comboThrough = QComboBox()
        self.comboDistance = QComboBox()
        self.textDistance = QLineEdit("0")

        self.comboRotate.addItem(self.tr("Rotate 30"), 30)
        self.comboRotate.addItem(self.tr("Rotate 45"), 45)
        self.comboRotate.addItem(self.tr("Rotate 90"), 90)
        self.comboRotate.addItem(self.tr("Rotate 180"), 180)
        self.comboRotate.setMinimumWidth(100)
        #self.comboRotate.activated.connect(self.rotateComponent)

        self.comboThrough.addItem(self.tr("Thro CE"))
        self.comboThrough.addItem(self.tr("Thro Cursor"))
        self.comboThrough.addItem(self.tr("Thro Arrive"))
        self.comboThrough.addItem(self.tr("Thro Leave"))
        #self.comboThrough.activated.connect(self.throughComponent)

        # Select Spool - input an offset distance between opposing faces.
        # Select Distance - input an offset distance between component origins
        self.comboDistance.addItem(self.tr("Spool"))
        self.comboDistance.addItem(self.tr("Distance"))
        self.comboDistance.setMinimumWidth(100)
        #self.comboDistance.activated.connect(self.moveComponent)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.comboRotate)
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.comboThrough)

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.comboDistance)
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.textDistance)

        self.verticalLayout.addWidget(self.groupBox)

        # Set dock widget.
        self.setWidget(self.dockContext)

    # setupUi

    def setBranch(self):
        self.branch = None
        self.component = None

        ce = DbElement.Current
        if ce.Type == 'BRAN':
            self.branch = ce
        elif ce.Owner.Type == 'BRAN':
            self.branch = ce.Owner
            self.component = ce
        # if

        if self.branch is None:
            QMessageBox.warning(self, '', self.tr('This command can only be used at a Branch or piping component!'))
            return
        # if

        # Branch 
        self.textBranch.text = self.branch.Name
        self.textBore.text = int(self.branch.Hbore)

        # Component Type.
        self.comboType.clear()

        pspec = self.branch.Pspec
        if pspec.IsValid:
            # Branch spec.
            self.textSpec.text = pspec.Name

            # Component type in spec.
            for sele in pspec.Members:
                if sele.Type == 'SELE':
                    answer = sele.Tanswer
                    if len(answer) > 0:
                        self.comboType.addItem(answer, sele)
                    # if
                # if
            # for
        # if
    # setBranch

    def typeChanged(self):
        self.reducerInfo.hide()
        self.connectionInfo.hide()

        self.comboFilter.clear()

        sele = self.comboType.currentData
        if sele is None:
            return
        # if

        typelist = list()

        typeFilter = TypeFilter('SELE')
        collection = DbElementCollection(sele, typeFilter)
        seleList = collection.Perform()
        for elem in seleList:
            if elem.Question == 'STYP':
                for child in elem.Members:
                    # Check bore before add subtype.
                    hasSpco = False

                    spcoFilter = TypeFilter('SPCO')
                    collection = DbElementCollection(child, spcoFilter)
                    spcoList = collection.Perform()
                    for spco in spcoList:
                        catref = spco.Catref
                        if catref.IsValid:
                            param = catref.Param
                            if len(param) > 0:
                                # Check bore 
                                if param[0] == self.branch.Hbore:
                                    hasSpco = True
                                    break
                                # if
                            # if
                        # if
                    # for

                    if hasSpco:
                        typelist.append(child.Tanswer)
                    # if
                # for
            # if
        # for

        stypes = list(dict.fromkeys(typelist))
        self.comboFilter.addItem(self.tr('unset'))
        self.comboFilter.addItems(stypes)

        ctype = self.comboType.currentText
        if ctype == 'REDU':
            self.reducerInfo.show()
        elif ctype in ('TEE', 'OLET'):
            self.connectionInfo.show()
        # if
    # typeChanged

    def subTypeChanged(self):
        self.tableWidget.setRowCount(0)

        typeSele = self.comboType.currentData
        if typeSele is None:
            return
        # if

        subIndex = self.comboFilter.currentIndex
        stype = self.comboFilter.currentText

        stypeFilter = TypeFilter('SELE')
        collection = DbElementCollection(typeSele, stypeFilter)
        seleList = collection.Perform()
        for sele in seleList:
            if sele.Question == 'STYP':
                for child in sele.Members:
                    # Check bore before add subtype.
                    spcoFilter = TypeFilter('SPCO')
                    collection = DbElementCollection(child, spcoFilter)
                    spcoList = collection.Perform()
                    for spco in spcoList:
                        catref = spco.Catref
                        if catref.IsValid:
                            param = catref.Param
                            if len(param) > 0:
                                # Check bore 
                                if param[0] == self.branch.Hbore:
                                    if subIndex == 0 or child.Tanswer == stype:
                                        row = self.tableWidget.rowCount
                                        self.tableWidget.insertRow(row)

                                        desc = ''
                                        detref = spco.Detref
                                        if detref.IsValid:
                                            desc = detref.Rtext
                                        # if

                                        matxt = spco.Matxt
                                        if matxt.IsValid:
                                            desc = f'{desc} {matxt.Xtext}'
                                        # if

                                        boreItem = QTableWidgetItem(str(int(param[0])))
                                        boreItem.setData(Qt.UserRole, spco)

                                        self.tableWidget.setItem(row, 0, boreItem)
                                        self.tableWidget.setItem(row, 1, QTableWidgetItem(child.Tanswer))
                                        self.tableWidget.setItem(row, 2, QTableWidgetItem(desc))
                                    # if
                                # if
                            # if
                        # if
                    # for
                # for
            # if
        # for

    # subTypeChanged

# ComponentWidget

componentWidget = ComponentWidget(MainWindow)

def Create():
    MainWindow.addDockWidget(Qt.RightDockWidgetArea, componentWidget)

    componentWidget.show()
# Create

def Modify():
    pass
# Modify
