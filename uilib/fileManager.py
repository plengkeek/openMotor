from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from . import defaults
import motorlib
import yaml

class fileManager(QObject):

    fileNameChanged = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()

        self.fileHistory = []
        self.currentVersion = 0
        self.savedVersion = 0

        self.fileName = None

    def newFile(self):
        if self.unsavedCheck():
            self.fileHistory = [defaults.defaultMotor().getDict()]
            self.currentVersion = 0
            self.savedVersion = 0
            self.fileName = None

    def save(self):
        if self.fileName is None:
            self.saveAs()
        else:
            with open(self.fileName, 'w') as saveFile:
                yaml.dump(self.fileHistory[self.currentVersion], saveFile)
                self.savedVersion = self.currentVersion
                self.sendTitleUpdate()

    def saveAs(self):
        self.fileName = self.showSaveDialog()
        self.save()

    def load(self):
        if self.unsavedCheck():
            path = QFileDialog.getOpenFileName(None, 'Load motor', '', 'Motor Files (*.ric)')[0]
            with open(path, 'r') as loadFile:
                motorData = yaml.load(loadFile)
                self.fileHistory = [motorData]
                self.currentVersion = 0
                self.savedVersion = 0
                self.fileName = path
                self.sendTitleUpdate()

    def getCurrentMotor(self):
        nm = motorlib.motor()
        nm.loadDict(self.fileHistory[self.currentVersion])
        return nm

    def addNewMotorHistory(self, motor):
        if self.canRedo():
            del self.fileHistory[self.currentVersion + 1:]
        self.fileHistory.append(motor.getDict())
        self.currentVersion += 1
        self.sendTitleUpdate()

    def canUndo(self):
        return self.currentVersion > 0

    def undo(self):
        if self.canUndo():
            self.currentVersion -= 1
            self.sendTitleUpdate()

    def canRedo(self):
        return self.currentVersion < len(self.fileHistory) - 1

    def redo(self):
        if self.canRedo():
            self.currentVersion += 1
            self.sendTitleUpdate()

    def unsavedCheck(self):
        if self.savedVersion != self.currentVersion:
            msg = QMessageBox()

            msg.setText("The current file has unsaved changes. Close without saving?")
            msg.setWindowTitle("Close without saving?")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            res = msg.exec_()
            if res == QMessageBox.Save:
                self.save()
                return True
            elif res == QMessageBox.Discard:
                return True
            else:
                return False

        return True

    def sendTitleUpdate(self):
        self.fileNameChanged.emit(self.fileName, self.savedVersion == self.currentVersion)

    def showSaveDialog(self):
        path = QFileDialog.getSaveFileName(None, 'Save motor', '', 'Motor Files (*.ric)')[0]
        if path[-4:] != '.ric':
            path += '.ric'
        return path
