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
# Copyright (C) 2021 Wuhan OCADE IT. Co., Ltd.
# Author: Shing Liu(eryar@163.com)
# Date: 21:16 2021-09-16

from PythonQt.QtCore import *
from PythonQt.QtGui import *
from pipecad import *

class DataManager(QDialog):
    """docstring for DataManager"""
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(QT_TRANSLATE_NOOP("DataManager", "Data Manager"))
        self.verticalLayout = QVBoxLayout(self)

        self.horizontalLayout = QHBoxLayout()

        self.labelType = QLabel(QT_TRANSLATE_NOOP("DataManager", "Type"))
        self.comboType = QComboBox()
        self.comboType.addItems(["ALL", "SITE", "ZONE", "EQUI", "PIPE", "BRAN", "STRU", "FRMW", "SBFR"])
        self.horizontalLayout.addWidget(self.labelType)

        self.labelFilter = QLabel(QT_TRANSLATE_NOOP("DataManager", "Filter"))
        self.lineFilter = QLineEdit()
        self.lineFilter.setPlaceholderText(QT_TRANSLATE_NOOP("DataManager", "Name Filter"))
        self.horizontalLayout.addWidget(self.labelFilter)

        self.buttonRefresh = QPushButton(QT_TRANSLATE_NOOP("DataManager", "Refresh"))
        self.buttonRefresh.clicked.connect(self.refresh)
        self.horizontalLayout.addWidget(self.buttonRefresh)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels([
            QT_TRANSLATE_NOOP("DataManager", "Name (Tag)"),
            QT_TRANSLATE_NOOP("DataManager", "Type"),
            QT_TRANSLATE_NOOP("DataManager", "Description")
        ])
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalLayout.addWidget(self.tableWidget)

        self.actionLayout = QHBoxLayout()

        self.buttonModify = QPushButton(QT_TRANSLATE_NOOP("DataManager", "Modify Tag"))
        self.buttonModify.clicked.connect(self.modifyTag)
        self.actionLayout.addWidget(self.buttonModify)

        self.verticalLayout.addLayout(self.actionLayout)

    def refresh(self):
        self.tableWidget.setRowCount(0)
        aType = self.comboType.currentText
        aFilter = self.lineFilter.text

        aItems = []
        if aType == "ALL":
            for aTypeKey in ["EQUI", "PIPE", "STRU"]:
                aItems.extend(PipeCad.CollectItem(aTypeKey))
        else:
            aItems = PipeCad.CollectItem(aType)

        aRow = 0
        for aItem in aItems:
            if aFilter and aFilter not in aItem.Name:
                continue

            self.tableWidget.insertRow(aRow)

            aNameItem = QTableWidgetItem(aItem.Name)
            aNameItem.setData(Qt.UserRole, aItem)

            self.tableWidget.setItem(aRow, 0, aNameItem)
            self.tableWidget.setItem(aRow, 1, QTableWidgetItem(aItem.Type))
            self.tableWidget.setItem(aRow, 2, QTableWidgetItem(aItem.Description))
            aRow += 1

    def modifyTag(self):
        aRow = self.tableWidget.currentRow()
        if aRow < 0:
            QMessageBox.warning(self, QT_TRANSLATE_NOOP("DataManager", "Warning"), QT_TRANSLATE_NOOP("DataManager", "Please select an item first!"))
            return

        aItem = self.tableWidget.item(aRow, 0).data(Qt.UserRole)
        if aItem is None:
            return

        aNewName, aOk = QInputDialog.getText(self, QT_TRANSLATE_NOOP("DataManager", "Modify Tag"), QT_TRANSLATE_NOOP("DataManager", "New Name:"), QLineEdit.Normal, aItem.Name)
        if aOk and aNewName:
            try:
                PipeCad.StartTransaction("Modify Tag")
                aItem.Name = aNewName
                PipeCad.CommitTransaction()
                # Update table
                self.tableWidget.item(aRow, 0).setText(aNewName)
            except Exception as e:
                print(e)
                QMessageBox.critical(self, QT_TRANSLATE_NOOP("DataManager", "Error"), str(e))

# Singleton Instance.
aDataManager = DataManager(PipeCad)

def show():
    aDataManager.show()

def showDataManager():
    show()


