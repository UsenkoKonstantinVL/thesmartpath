import PySide2
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt, QMargins
from PySide2.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFormLayout, QLineEdit, QLabel, QFileDialog)
import shapefile
from core import Model
from map import Map
import os

stylesheetPath = os.path.join(os.path.dirname(__file__), "darkStyle.qss")

class Form(QWidget):
    def __init__(self):
        super().__init__()
        self.model = Model()
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        # CREATE WIDGETS
        self.map = Map(self.model)


        self.controlBox = QGroupBox("Planning Controls")
        contolBoxLayout = QVBoxLayout()
        # self.controlBox.setLayout(contolBoxLayout)

        self.mapBox = QGroupBox("Path Details")
        mapBoxLayout = QVBoxLayout()
        self.mapBox.setLayout(mapBoxLayout)

        # File loading group
        self.fileGroup = QGroupBox("Source") # we'll create this second layer GBs without text
        fileGroupLayout = QVBoxLayout()
        self.fileGroup.setLayout(fileGroupLayout)

        self.fileName = QLabel(Text="Open field file to begin...")
        self.openButton = QPushButton(text="Open file")
        self.openButton.clicked.connect(self.openFileButtonCallback)
        self.calcButton = QPushButton(text="Calculate")
        self.calcButton.setEnabled(False)

        # Parameters group
        self.paramsGroup = QGroupBox("Calc parameters")
        paramsGroupLayout = QFormLayout()
        self.paramsGroup.setLayout(paramsGroupLayout)
        self.tractorWidthEdit = QLineEdit("2.25")
        self.tractorWheelBaseEdit = QLineEdit("2.45")
        self.seederWidthEdit = QLineEdit("8")
        self.sprinklerWidthEdit = QLineEdit("17")
        self.rowWidthEdit = QLineEdit("0.7")

        paramsGroupLayout.addRow("Tractor Width, m", self.tractorWidthEdit)
        paramsGroupLayout.addRow("Tractor Wheelbase, m", self.tractorWheelBaseEdit)
        paramsGroupLayout.addRow("Seeder Width, rows", self.seederWidthEdit)
        paramsGroupLayout.addRow("Sprinkler Width, rows", self.sprinklerWidthEdit)
        paramsGroupLayout.addRow("Row Width, m", self.rowWidthEdit)


        # COMPOSING

        mainLayout.addLayout(contolBoxLayout, 3)
        mainLayout.addWidget(self.mapBox, 7)

        contolBoxLayout.addWidget(self.fileGroup, 3)
        contolBoxLayout.addWidget(self.paramsGroup, 10)

        fileGroupLayout.addWidget(self.fileName)
        fileGroupLayout.addWidget(self.openButton)
        fileGroupLayout.addWidget(self.calcButton)

        mapBoxLayout.addWidget(self.map)
        # STYLING
        contolBoxLayout.setContentsMargins(QMargins(0, 0, 0, 0))

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

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    with open(stylesheetPath, 'r') as file:
        app.setStyleSheet(file.read())

    form = Form()
    form.setWindowTitle("TheSmartPath")
    form.setMinimumSize(1000, 600)
    form.show()
    app.exec_()
