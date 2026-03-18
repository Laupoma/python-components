import logging

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.ActuatorData import ActuatorData

class BaseActuatorSimTask():

	def __init__(self, name: str = ConfigConst.NOT_SET, typeID: int = ConfigConst.DEFAULT_ACTUATOR_TYPE, simpleName: str = "Actuator"):
		self.latestActuatorResponse = ActuatorData(typeID = typeID, name = name)
		self.latestActuatorResponse.setAsResponse()

		self.name = name
		self.typeID = typeID
		self.simpleName = simpleName
		self.lastKnownCommand = ConfigConst.DEFAULT_COMMAND
		self.lastKnownValue = ConfigConst.DEFAULT_VAL
		self.lastKnownState = ""

	def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		msg = "\n*******"
		msg = msg + "\n* O N *"
		msg = msg + "\n*******"
		msg = msg + "\n" + self.name + " VALUE -> " + str(val) + "\n======="

		logging.info("Simulating %s actuator ON: %s", self.name, msg)

		return 0

	def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		msg = "\n*******"
		msg = msg + "\n* OFF *"
		msg = msg + "\n*******"

		logging.info("Simulating %s actuator OFF: %s", self.name, msg)

		return 0

	def updateActuator(self, data: ActuatorData) -> ActuatorData:
		if data and self.typeID == data.getTypeID():
			statusCode = ConfigConst.DEFAULT_STATUS

			curCommand = data.getCommand()
			curVal     = data.getValue()
			curState   = data.getStateData()

			if curCommand == self.lastKnownCommand and curVal == self.lastKnownValue and curState == self.lastKnownState:
				logging.debug( \
					"New actuator command, value and state are repeats. Ignoring: %s %s", \
					str(curCommand), str(curVal))
			else:
				logging.debug( \
					"New actuator command and value to be applied: %s %s", \
					str(curCommand), str(curVal))

				if curCommand == ConfigConst.COMMAND_ON:
					logging.info("Activating actuator...")
					statusCode = self._activateActuator(val = data.getValue(), stateData = data.getStateData())
				elif curCommand == ConfigConst.COMMAND_OFF:
					logging.info("Deactivating actuator...")
					statusCode = self._deactivateActuator(val = data.getValue(), stateData = data.getStateData())
				else:
					logging.warning("ActuatorData command is unknown. Ignoring: %s", str(curCommand))
					statusCode = -1

				self.lastKnownCommand = curCommand
				self.lastKnownValue = curVal
				self.lastKnownState = curState

				actuatorResponse = ActuatorData()
				actuatorResponse.updateData(data)
				actuatorResponse.setStatusCode(statusCode)
				actuatorResponse.setAsResponse()

				self.latestActuatorResponse.updateData(actuatorResponse)

				return actuatorResponse

		return None
