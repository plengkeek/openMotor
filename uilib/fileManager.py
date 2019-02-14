from PyQt5.QtCore import QObject
from . import defaults

class fileManager(QObject):
    def __init__(self):
        super().__init__()

        self.fileHistory = []
        self.currentVersion = 0

        self.saved = True
        self.fileName = ""

    def newFile(self):
        # ask if they are sure
        self.fileHistory = [defaults.defaultMotor()]
        self.currentVersion = 0
        self.saved = True

    def save(self):
        
        self.saved = True

    def load(self):

        self.saved = True

    def getCurrentMotor(self):
        return self.fileHistory[self.currentVersion]

    def addNewMotorHistory(self, motor):
        if self.canRedo():
            del self.getCurrentMotor[self.currentVersion:]
        self.fileHistory.append(motor)
        self.currentVersion += 1

    def canUndo(self):
        return self.currentVersion > 0

    def undo(self):
        if self.canUndo():
            self.currentVersion -= 1

    def canRedo(self):
        return self.currentVersion < len(self.fileHistory)

    def redo(self):
        if self.canRedo():
            self.currentVersion += 1

    def checkUnsaved(self):
        return not self.saved

    def showUnsavedDialog(self):
        msg = QMessageBox()

        msg.setText("The current file has unsaved changes. Close without saving?")
        msg.setWindowTitle("Close without saving?")
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)

        return msg.exec_() == QMessageBox.Save
        