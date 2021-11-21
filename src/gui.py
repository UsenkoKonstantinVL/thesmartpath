import PySide2
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt, QMargins
from PySide2.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFormLayout, QLineEdit, QLabel, QFileDialog, QSizePolicy,
                               QGridLayout)
from PySide2.QtGui import QPalette, QColor
import shapefile
from core import Model
from map import Map
from functools import partial
import os

stylesheetPath = os.path.join(os.path.dirname(__file__), "darkStyle.qss")

class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.model = Model()
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)
        self.dataFields = tuple()

        # CREATE WIDGETS
        self.map = Map(self.model)
        # self.map.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)

        contolBoxLayout = QVBoxLayout()

        self.mapBox = QGroupBox("Path Details")
        self.mapBox.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        mapBoxLayout = QVBoxLayout()
        self.mapBox.setLayout(mapBoxLayout)

        # File loading group
        self.fileGroup = QGroupBox("Source") # we'll create this second layer GBs without text
        self.fileGroup.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        fileGroupLayout = QVBoxLayout()
        self.fileGroup.setLayout(fileGroupLayout)

        self.fileName = QLabel(Text="Open field file to begin...")
        self.fileName.setWordWrap(True)
        self.openButton = QPushButton(text="Open file")
        self.openButton.clicked.connect(self.openFileButtonCallback)
        self.calcButton = QPushButton(text="Calculate")
        self.calcButton.setEnabled(False)

        # Parameters group
        self.paramsGroup = QGroupBox("Calc parameters")
        self.paramsGroup.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        paramsGroupLayout = QFormLayout()
        self.paramsGroup.setLayout(paramsGroupLayout)
        self.tractorWidthEdit = QLineEdit("2.25")
        self.tractorWheelBaseEdit = QLineEdit("2.45")
        self.seederWidthEdit = QLineEdit("8")
        self.sprinklerWidthEdit = QLineEdit("17")
        self.rowWidthEdit = QLineEdit("0.7")
        self.turnRadiusEdit = QLineEdit("5")
        self.dataFields += (self.tractorWidthEdit, self.tractorWheelBaseEdit, self.seederWidthEdit,
                            self.sprinklerWidthEdit, self.rowWidthEdit, self.turnRadiusEdit)
        print(self.dataFields)
        # entry and end points
        entryPointCoordLayout = QVBoxLayout()
        entryPointCoordLayout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.entryPointXEdit = QLineEdit()
        self.entryPointYEdit = QLineEdit()
        self.entryPointClear = QPushButton("Clear")

        entryPointCoordLayout.addWidget(self.entryPointXEdit)
        entryPointCoordLayout.addWidget(self.entryPointYEdit)
        entryPointCoordLayout.addWidget(self.entryPointClear)

        endPointCoordLayout = QVBoxLayout()
        endPointCoordLayout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.endPointXEdit = QLineEdit()
        self.endPointYEdit = QLineEdit()
        self.endPointClear = QPushButton("Clear")

        for textEdit in (self.endPointXEdit, self.endPointYEdit, self.entryPointYEdit, self.entryPointXEdit):
            textEdit.setEnabled(False)
            self.dataFields += (textEdit,)


        endPointCoordLayout.addWidget(self.endPointXEdit)
        endPointCoordLayout.addWidget(self.endPointYEdit)
        endPointCoordLayout.addWidget(self.endPointClear)

        paramsGroupLayout.addRow("Tractor Width, m", self.tractorWidthEdit)
        paramsGroupLayout.addRow("Tractor Wheelbase, m", self.tractorWheelBaseEdit)
        paramsGroupLayout.addRow("Seeder Width, rows", self.seederWidthEdit)
        paramsGroupLayout.addRow("Sprinkler Width, rows", self.sprinklerWidthEdit)
        paramsGroupLayout.addRow("Row Width, m", self.rowWidthEdit)
        paramsGroupLayout.addRow("Turn Radius, m", self.turnRadiusEdit)
        paramsGroupLayout.addRow("Entry Point", entryPointCoordLayout)
        paramsGroupLayout.addRow("End Point", endPointCoordLayout)

        # WIRING
        self.endPointClear.clicked.connect(partial(self.model.setEndPoint, None))
        self.entryPointClear.clicked.connect(partial(self.model.setEntryPoint, None))
        self.model.pointsChanged.connect(self.writeInPoints)
        for textEdit in self.dataFields:
            textEdit.textChanged.connect(self.checkIfAllRight)

        self.calcButton.clicked.connect(self.calculateGeometry)

        # COMPOSING

        mainLayout.addLayout(contolBoxLayout, 3)
        mainLayout.addWidget(self.mapBox, 8)

        contolBoxLayout.addWidget(self.fileGroup, 3)
        contolBoxLayout.addWidget(self.paramsGroup, 10)

        fileGroupLayout.addWidget(self.fileName)
        fileGroupLayout.addWidget(self.openButton)
        fileGroupLayout.addWidget(self.calcButton)

        mapBoxLayout.addWidget(self.map)
        # STYLING
        contolBoxLayout.setContentsMargins(QMargins(0, 0, 0, 0))
        mainLayout.setSpacing(4)
        buttonPallette = self.calcButton.palette()
        buttonPallette.setColor(QPalette.Button, QColor(Qt.green))
        self.calcButton.setPalette(buttonPallette)
        # self.calcButton.setAutoFillBackground(True)

    def writeInPoints(self):
        if self.model.entryPoint is not None:
            self.entryPointXEdit.setText(str(self.model.entryPoint[0]))
            self.entryPointYEdit.setText(str(self.model.entryPoint[1]))
        else:
            self.entryPointXEdit.setText("")
            self.entryPointYEdit.setText("")

        if self.model.endPoint is not None:
            self.endPointXEdit.setText(str(self.model.endPoint[0]))
            self.endPointYEdit.setText(str(self.model.endPoint[1]))
        else:
            self.endPointXEdit.setText("")
            self.endPointYEdit.setText("")

    def keyPressEvent(self, event:PySide2.QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            print("Bye!")
            exit()

    def openFileButtonCallback(self):
        dialog = QFileDialog()
        if dialog.exec_():
            fileNames = dialog.selectedFiles()

        print('Result of dialog is:')
        print(fileNames)
        self.model.pullGeometryFromFile(fileNames[0])
        self.fileName.setText(fileNames[0])

    def checkIfAllRight(self):
        check = True
        for textEdit in self.dataFields:
            if textEdit.text() == "":
                check = False
        self.calcButton.setEnabled(check)

    def calculateGeometry(self):
        print("SHOW MUST GO ON!")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    with open(stylesheetPath, 'r') as file:
        app.setStyleSheet(file.read())

    form = Form()
    form.setWindowTitle("TheSmartPath")
    form.setMinimumSize(1000, 600)
    form.show()
    app.exec_()
