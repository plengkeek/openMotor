from .. import fmmGrain
from ..properties import *
from .. import simAlert, simAlertLevel, simAlertType

import numpy as np

class moonBurner(fmmGrain):
    geomName = 'Moon Burner'
    def __init__(self):
        super().__init__()
        self.props['coreOffset'] = floatProperty('Core offset', 'm', 0, 1)
        self.props['coreDiameter'] = floatProperty('Core diameter', 'm', 0, 1)

    def generateCoreMap(self):
        coreRadius = self.normalize(self.props['coreDiameter'].getValue()) / 2
        coreOffset = self.normalize(self.props['coreOffset'].getValue())

        # Open up core
        self.coreMap[(self.X - coreOffset)**2 + self.Y**2 < coreRadius**2] = 0

    def getDetailsString(self, preferences):
        lengthUnit = preferences.units.getProperty('m')
        return 'Length: ' + self.props['length'].dispFormat(lengthUnit) + ', Core: ' + self.props['coreDiameter'].dispFormat(lengthUnit)

    def getGeometryErrors(self):
        errors = super().getGeometryErrors()
        if self.props['coreDiameter'].getValue() == 0:
            errors.append(simAlert(simAlertLevel.ERROR, simAlertType.GEOMETRY, 'Core diameter must not be 0'))
        if self.props['coreDiameter'].getValue() >= self.props['diameter'].getValue():
            errors.append(simAlert(simAlertLevel.ERROR, simAlertType.GEOMETRY, 'Core diameter must be less than or equal to grain diameter'))

        if self.props['coreOffset'].getValue() * 2 > self.props['diameter'].getValue():
            errors.append(simAlert(simAlertLevel.WARNING, simAlertType.GEOMETRY, 'Core offset should be less than or equal to grain radius'))

        return errors
