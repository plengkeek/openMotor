from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHeaderView
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSignal

from threading import Thread

from motorlib import simAlertLevel, simAlertType, alertLevelNames, alertTypeNames

class simulationProgressDialog(QDialog):

    simulationCanceled = pyqtSignal()

    def __init__(self):
        QDialog.__init__(self)
        loadUi("resources/SimulatingDialog.ui", self)

        self.buttonBox.rejected.connect(self.closeEvent)

    def show(self):
        self.progressBar.setValue(0)
        super().show()

    def closeEvent(self, event = None):
        self.simulationCanceled.emit()
        self.close()

    def progressUpdate(self, progress):
        self.progressBar.setValue(int(progress * 100))

class simulationAlertsDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        loadUi("resources/SimulationAlertsDialog.ui", self)

        header = self.tableWidgetAlerts.horizontalHeader()       
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.hide()

    def displayAlerts(self, simRes):
        self.tableWidgetAlerts.setRowCount(0) # Clear the table
        if len(simRes.alerts) > 0:
            self.tableWidgetAlerts.setRowCount(len(simRes.alerts))
            for row, alert in enumerate(simRes.alerts):
                self.tableWidgetAlerts.setItem(row, 0, QTableWidgetItem(alertLevelNames[alert.level]))
                self.tableWidgetAlerts.setItem(row, 1, QTableWidgetItem(alertTypeNames[alert.type]))
                self.tableWidgetAlerts.setItem(row, 2, QTableWidgetItem(alert.location))
                self.tableWidgetAlerts.setItem(row, 3, QTableWidgetItem(alert.description))
            self.show()


class simulationManager(QObject):

    simulationDone = pyqtSignal(object)
    newSimulationResult = pyqtSignal(object)
    simProgress = pyqtSignal(float)
    simCanceled = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.progDialog = simulationProgressDialog()
        self.simProgress.connect(self.progDialog.progressUpdate)
        self.simulationDone.connect(self.progDialog.hide)
        self.progDialog.simulationCanceled.connect(self.cancelSim)

        self.alertsDialog = simulationAlertsDialog()
        self.simulationDone.connect(self.alertsDialog.displayAlerts)

        self.motor = None
        self.preferences = None

        self.currentSimThread = None
        self.threadStopped = False # Set to true to stop simulation thread after it finishes the iteration it is on

    def setPreferences(self, preferences):
        self.preferences = preferences

    def runSimulation(self, motor, show = True): # Show sets if the results will be reported on newSimulationResult and shown in UI
        self.motor = motor
        self.threadStopped = False
        self.progDialog.show()
        self.currentSimThread = Thread(target = self._simThread, args = [show])
        self.currentSimThread.start()

    def _simThread(self, show):
        simRes = self.motor.runSimulation(self.preferences, self.updateProgressBar)
        self.simulationDone.emit(simRes)
        if simRes.success and show:
            self.newSimulationResult.emit(simRes)

    def updateProgressBar(self, prog):
        self.simProgress.emit(prog)
        return self.threadStopped

    def cancelSim(self):
        self.threadStopped = True
        self.simCanceled.emit()
