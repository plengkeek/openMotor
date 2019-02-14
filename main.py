from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSlot
from PyQt5.uic import loadUi
import sys
import yaml

import motorlib
import uilib

class Window(QMainWindow):
    def __init__(self):
        QWidget.__init__(self)
        loadUi("MainWindow.ui", self)

        self.editing = None

        self.preferences = uilib.preferences()
        self.preferences.loadDefault()
        self.loadPreferences()
        self.preferencesWindow = uilib.PreferencesWindow()
        self.preferencesWindow.preferencesApplied.connect(self.applyPreferences)

        self.propManager = uilib.propellantManager()
        self.propManager.updated.connect(self.propListChanged)
        self.propManager.setPreferences(self.preferences)

        self.motorStatLabels = [self.labelMotorDesignation, self.labelImpulse, self.labelDeliveredISP, self.labelBurnTime,
                                self.labelAveragePressure, self.labelPeakPressure, self.labelInitialKN, self.labelPeakKN,
                                self.labelPortThroatRatio, self.labelCoreLD, self.labelPeakMassFlux]

        self.loadDefaultMotor()

        self.setupMotorStats()
        self.setupMotorEditor()
        self.setupGrainAddition()
        self.setupMenu()
        self.setupPropSelector()
        self.setupGrainTable()
        self.setupGraph()

        self.show()

    def setupMotorStats(self):
        for label in self.motorStatLabels:
            label.setText("-")

    def setupMotorEditor(self):
        self.motorEditor.setPreferences(self.preferences)
        self.pushButtonEditGrain.pressed.connect(self.editGrain)
        self.motorEditor.changeApplied.connect(self.applyChange)
        self.motorEditor.closed.connect(self.checkGrainSelection) # Enables only buttons for actions possible given the selected grain

    def setupGrainAddition(self):
        self.comboBoxGrainGeometry.addItems(motorlib.grainTypes.keys())
        self.pushButtonAddGrain.pressed.connect(self.addGrain)

    def setupMenu(self):
        #File menu
        self.actionNew.triggered.connect(self.newMotor)
        self.actionSave.triggered.connect(self.saveMotor)
        self.actionOpen.triggered.connect(self.loadMotor)
        self.actionQuit.triggered.connect(self.exit)

        #Edit menu
        self.actionPreferences.triggered.connect(self.showPreferences)
        self.actionPropellantEditor.triggered.connect(self.propManager.showMenu)

        #Sim
        self.actionRunSimulation.triggered.connect(self.runSimulation)

    def setupPropSelector(self):
        self.pushButtonPropEditor.pressed.connect(self.propManager.showMenu)
        self.populatePropSelector()
        self.comboBoxPropellant.currentIndexChanged.connect(self.propChooserChanged)

    def disablePropSelector(self):
        self.pushButtonPropEditor.pressed.disconnect()
        self.comboBoxPropellant.currentIndexChanged.disconnect()

    def populatePropSelector(self):
        self.comboBoxPropellant.clear()
        self.comboBoxPropellant.addItems(self.propManager.getNames())

    def setupGrainTable(self):
        self.tableWidgetGrainList.clearContents()

        header = self.tableWidgetGrainList.horizontalHeader()       
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.updateGrainTable()

        self.pushButtonMoveGrainUp.pressed.connect(lambda: self.moveGrain(-1))
        self.pushButtonMoveGrainDown.pressed.connect(lambda: self.moveGrain(1))
        self.pushButtonDeleteGrain.pressed.connect(self.deleteGrain)

        self.tableWidgetGrainList.itemSelectionChanged.connect(self.checkGrainSelection)
        self.checkGrainSelection()

    def setupGraph(self):
        self.graphWidget.resetPlot()
        self.graphWidget.setPreferences(self.preferences)

    def applyChange(self, propDict):
        self.editing.setProperties(propDict)
        self.updateGrainTable()

    def propListChanged(self):
        self.resetOutput()
        self.disablePropSelector()
        if self.motor.propellant.getProperty("name") not in self.propManager.getNames():
            print("Motor's propellant must have been deleted, readding")
            self.propManager.propellants.append(self.motor.propellant)
        self.populatePropSelector()
        self.setupPropSelector()
        self.comboBoxPropellant.setCurrentText(self.motor.propellant.getProperty("name"))

    def propChooserChanged(self):
        self.motor.propellant = self.propManager.propellants[self.comboBoxPropellant.currentIndex()]

    def updateGrainTable(self):
        self.tableWidgetGrainList.setRowCount(len(self.motor.grains) + 1)
        for gid, grain in enumerate(self.motor.grains):
            self.tableWidgetGrainList.setItem(gid, 0, QTableWidgetItem(grain.geomName))
            self.tableWidgetGrainList.setItem(gid, 1, QTableWidgetItem(grain.getDetailsString(self.preferences)))

        self.tableWidgetGrainList.setItem(len(self.motor.grains), 0, QTableWidgetItem('Nozzle'))
        self.tableWidgetGrainList.setItem(len(self.motor.grains), 1, QTableWidgetItem(self.motor.nozzle.getDetailsString(self.preferences)))

    def toggleGrainEditButtons(self, state, grainTable = True):
        if grainTable:
            self.tableWidgetGrainList.setEnabled(state)
        self.pushButtonDeleteGrain.setEnabled(state)
        self.pushButtonEditGrain.setEnabled(state)
        self.pushButtonMoveGrainDown.setEnabled(state)
        self.pushButtonMoveGrainUp.setEnabled(state)

    def toggleGrainButtons(self, state):
        self.toggleGrainEditButtons(state)
        self.comboBoxPropellant.setEnabled(state)
        self.comboBoxGrainGeometry.setEnabled(state)
        self.pushButtonAddGrain.setEnabled(state)

    def checkGrainSelection(self):
        ind = self.tableWidgetGrainList.selectionModel().selectedRows()
        if len(ind) > 0:
            gid = ind[0].row()
            self.toggleGrainButtons(True)
            if gid == 0: # Top grain selected
                self.pushButtonMoveGrainUp.setEnabled(False)
            if gid == len(self.motor.grains) - 1: # Bottom grain selected
                self.pushButtonMoveGrainDown.setEnabled(False)
            elif gid == len(self.motor.grains):
                self.pushButtonMoveGrainUp.setEnabled(False)
                self.pushButtonMoveGrainDown.setEnabled(False)
                self.pushButtonDeleteGrain.setEnabled(False) 
        else:
            self.toggleGrainEditButtons(False, False)

    def moveGrain(self, offset):
        ind = self.tableWidgetGrainList.selectionModel().selectedRows()
        if len(ind) > 0:
            gid = ind[0].row()
            if gid < len(self.motor.grains) and gid + offset < len(self.motor.grains) and gid + offset >= 0:
                self.motor.grains[gid + offset], self.motor.grains[gid] = self.motor.grains[gid], self.motor.grains[gid + offset]
                self.tableWidgetGrainList.selectRow(gid + offset)
                self.updateGrainTable()

    def editGrain(self):
        ind = self.tableWidgetGrainList.selectionModel().selectedRows()
        if len(ind) > 0:
            gid = ind[0].row()
            if gid < len(self.motor.grains):
                self.motorEditor.loadGrain(self.motor.grains[gid])
                self.editing = self.motor.grains[gid]
            else:
                self.motorEditor.loadNozzle(self.motor.nozzle)
                self.editing = self.motor.nozzle
            self.toggleGrainButtons(False)

    def deleteGrain(self):
        ind = self.tableWidgetGrainList.selectionModel().selectedRows()
        if len(ind) > 0:
            gid = ind[0].row()
            if gid < len(self.motor.grains):
                del self.motor.grains[gid]
                self.updateGrainTable()
                self.checkGrainSelection()

    def addGrain(self):
        newGrain = motorlib.grainTypes[self.comboBoxGrainGeometry.currentText()]()
        self.motor.grains.append(newGrain)
        self.updateGrainTable()
        self.tableWidgetGrainList.selectRow(len(self.motor.grains) - 1)
        self.motorEditor.loadGrain(self.motor.grains[-1])
        self.editing = newGrain
        self.checkGrainSelection()
        self.toggleGrainButtons(False)

    def formatMotorStat(self, quantity, inUnit):
        convUnit = self.preferences.getUnit(inUnit)
        return str(round(motorlib.convert(quantity, inUnit, convUnit), 3)) + ' ' + convUnit

    def updateMotorStats(self, simResult):
        self.labelMotorDesignation.setText(simResult.getDesignation())
        self.labelImpulse.setText(self.formatMotorStat(simResult.getImpulse(), 'ns'))
        self.labelDeliveredISP.setText(self.formatMotorStat(simResult.getISP(), 's'))
        self.labelBurnTime.setText(self.formatMotorStat(simResult.getBurnTime(), 's'))

        self.labelAveragePressure.setText(self.formatMotorStat(simResult.getAveragePressure(), 'pa'))
        self.labelPeakPressure.setText(self.formatMotorStat(simResult.getMaxPressure(), 'pa'))
        self.labelInitialKN.setText(self.formatMotorStat(simResult.getInitialKN(), ''))
        self.labelPeakKN.setText(self.formatMotorStat(simResult.getPeakKN(), ''))

        if simResult.getPortRatio() is not None:
            self.labelPortThroatRatio.setText(self.formatMotorStat(simResult.getPortRatio(), ''))
            self.labelPeakMassFlux.setText(self.formatMotorStat(simResult.getPeakMassFlux(), 'kg/(m^2*s)'))

        else:
            self.labelPortThroatRatio.setText('-')
            self.labelPeakMassFlux.setText('-')

        self.labelCoreLD.setText('????')

    def runSimulation(self):
        self.setupMotorStats()
        simResult = self.motor.runSimulation(self.preferences)
        self.graphWidget.showData(simResult)

        self.updateMotorStats(simResult)

    def resetOutput(self):
        self.setupMotorStats()
        self.graphWidget.resetPlot()
        self.updateGrainTable()

    def newMotor(self):
        #Check for unsaved changes
        self.loadDefaultMotor()
        self.resetOutput()

    def saveMotor(self):
        path = QFileDialog.getSaveFileName(self, 'Save motor', '', 'Motor Files (*.ric)')[0]
        if path[-4:] != '.ric':
            path += '.ric'
        with open(path, 'w') as saveFile:
            yaml.dump(self.motor.getDict(), saveFile)

    def loadMotor(self):
        # Check for unsaved changes
        path = QFileDialog.getOpenFileName(self, 'Load motor', '', 'Motor Files (*.ric)')[0]
        with open(path, 'r') as loadFile:
            self.disablePropSelector()
            motorData = yaml.load(loadFile)
            self.motor.loadDict(motorData)
            self.resetOutput()

            if self.motor.propellant.getProperty('name') not in self.propManager.getNames():
                print("Propellant not in library, adding")
                self.propManager.propellants.append(self.motor.propellant)
                self.propManager.savePropellants()
            else:
                if self.motor.propellant.getProperties() != self.propManager.getPropellantByName(self.motor.propellant.getProperty('name')).getProperties():
                    print("Loaded propellant name matches existing propellant, but properties differ. Using propellant from library.")
                    self.motor.propellant = self.propManager.getPropellantByName(self.motor.propellant.getProperty('name'))

            self.setupPropSelector()
            self.comboBoxPropellant.setCurrentText(self.motor.propellant.getProperty("name"))

    def exit(self):
        #if self.checkUnsaved():
        #    print(self.showdialog())
        sys.exit()

    def loadPreferences(self):
        try:
            with open('preferences.yaml', 'r') as prefFile:
                prefDict = yaml.load(prefFile)
                self.preferences.applyDict(prefDict)
        except FileNotFoundError:
            self.savePreferences()

    def savePreferences(self):
        try:
            with open('preferences.yaml', 'w') as prefFile:
                yaml.dump(self.preferences.getDict(), prefFile)
        except:
            print('Unable to save preferences')

    def applyPreferences(self, prefDict):
        self.preferences.applyDict(prefDict)
        self.savePreferences()
        self.updateGrainTable()
        self.setupMotorStats()
        self.setupGraph()
        self.propManager.setPreferences(self.preferences)

    def showPreferences(self):
        self.preferencesWindow.load(self.preferences)
        self.preferencesWindow.show()

    def loadDefaultMotor(self):
        self.motor = uilib.defaultMotor()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    sys.exit(app.exec_())
