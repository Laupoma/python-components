#####
#
# This class is part of the Programming the Internet of Things project.
#
import logging

from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector
from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.CoapServerAdapter import CoapServerAdapter
from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class DeviceDataManager(IDataMessageListener):

	def __init__(self, disableAllComms: bool = False):
		self.configUtil = ConfigUtil()

		self.enableSystemPerf = \
			self.configUtil.getBoolean(
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SYSTEM_PERF_KEY)

		self.enableSensing = \
			self.configUtil.getBoolean(
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SENSING_KEY)

		self.enableActuation = True

		self.handleTempChangeOnDevice = \
			self.configUtil.getBoolean(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY)

		self.triggerHvacTempFloor = \
			self.configUtil.getFloat(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY)

		self.triggerHvacTempCeiling = \
			self.configUtil.getFloat(
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY)

		# disableAllComms permite forzar el apagado de MQTT y CoAP sin tocar
		# la config global (PiotConfig.props). Lo usan los tests que quieren
		# probar la logica del DeviceDataManager de forma aislada, sin depender
		# de un broker o servidor CoAP vivo. Por defecto (False) se lee la config.
		if disableAllComms:
			self.enableMqttClient = False
			self.enableCoapServer = False
			self.enableCoapClient = False
		else:
			self.enableMqttClient = \
				self.configUtil.getBoolean(
					section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_MQTT_CLIENT_KEY)

			self.enableCoapServer = \
				self.configUtil.getBoolean(
					section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_SERVER_KEY)

			self.enableCoapClient = \
				self.configUtil.getBoolean(
					section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_CLIENT_KEY)


		self.sysPerfMgr         = None
		self.sensorAdapterMgr   = None
		self.actuatorAdapterMgr = None
		self.mqttClient         = None
		self.coapClient         = None
		self.coapServer         = None
		self.actuatorResponseCache = {}

		if self.enableSystemPerf:
			self.sysPerfMgr = SystemPerformanceManager()
			self.sysPerfMgr.setDataMessageListener(self)
			logging.info("Local system performance tracking enabled")

		if self.enableSensing:
			self.sensorAdapterMgr = SensorAdapterManager()
			self.sensorAdapterMgr.setDataMessageListener(self)
			logging.info("Local sensor tracking enabled")

		if self.enableActuation:
			self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener = self)
			logging.info("Local actuation capabilities enabled")

		if self.enableMqttClient:
			self.mqttClient = MqttClientConnector()
			self.mqttClient.setDataMessageListener(self)
			logging.info("MQTT client enabled")

		if self.enableCoapServer:
			self.coapServer = CoapServerAdapter(dataMsgListener = self)
			logging.info("CoAP server enabled")
		if self.enableCoapClient:
			self.coapClient = CoapClientConnector(dataMsgListener = self)
			logging.info("CoAP client enabled")


	def handleActuatorCommandMessage(self, data: ActuatorData = None) -> ActuatorData:
		logging.info("Actuator data: " + str(data))
		if data:
			logging.info("Processing actuator command message.")
			return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Incoming actuator command is invalid (null). Ignoring.")
			return None

	def handleActuatorCommandResponse(self, data: ActuatorData = None) -> bool:
		if data:
			logging.debug("Incoming actuator response received: " + str(data))
			self.actuatorResponseCache[data.getName()] = data
			return True
		else:
			logging.warning("Incoming actuator response is invalid (null). Ignoring.")
			return False

	def handleIncomingMessage(self, resourceEnum: ResourceNameEnum, msg: str) -> bool:
		logging.debug("Incoming message received.")
		if msg:
			self._handleIncomingDataAnalysis(msg)
			return True
		return False

	def handleSensorMessage(self, data: SensorData = None) -> bool:
		if data:
			logging.debug("Incoming sensor data received (from sensor manager): " + str(data))
			self._handleSensorDataAnalysis(data = data)
			return True
		else:
			logging.warning("Incoming sensor data is invalid (null). Ignoring.")
			return False

	def handleSystemPerformanceMessage(self, data: SystemPerformanceData = None) -> bool:
		if data:
			logging.debug("Incoming system performance message received: " + str(data))
			return True
		else:
			logging.warning("Incoming system performance data is invalid (null). Ignoring.")
			return False

	def setSystemPerformanceDataListener(self, listener: ISystemPerformanceDataListener = None):
		pass

	def setTelemetryDataListener(self, name: str = None, listener: ITelemetryDataListener = None):
		pass

	def startManager(self):
		logging.info("Starting DeviceDataManager...")

		if self.sysPerfMgr:
			self.sysPerfMgr.startManager()

		if self.sensorAdapterMgr:
			self.sensorAdapterMgr.startManager()

		if self.mqttClient:
			self.mqttClient.connectClient()
			self.mqttClient.subscribeToTopic(
				resource = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
				callback = None,
				qos      = ConfigConst.DEFAULT_QOS)

		if self.coapServer:
			self.coapServer.startServer()

		logging.info("Started DeviceDataManager.")

	def stopManager(self):
		logging.info("Stopping DeviceDataManager...")

		if self.sysPerfMgr:
			self.sysPerfMgr.stopManager()

		if self.sensorAdapterMgr:
			self.sensorAdapterMgr.stopManager()

		if self.mqttClient:
			self.mqttClient.unsubscribeFromTopic(
				resource = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
			self.mqttClient.disconnectClient()

		if self.coapServer:
			self.coapServer.stopServer()

		logging.info("Stopped DeviceDataManager.")

	def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
		pass

	def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
		pass

	def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
		pass

	def _handleIncomingDataAnalysis(self, msg: str):
		logging.debug("Incoming data analysis: " + str(msg))

	def _handleSensorDataAnalysis(self, data: SensorData = None):
		if self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.info("Handle temp change: %s - type ID: %s", str(self.handleTempChangeOnDevice), str(data.getTypeID()))

			ad = ActuatorData(typeID = ConfigConst.HVAC_ACTUATOR_TYPE)

			if data.getValue() > self.triggerHvacTempCeiling:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempCeiling)
			elif data.getValue() < self.triggerHvacTempFloor:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempFloor)
			else:
				ad.setCommand(ConfigConst.COMMAND_OFF)

			self.handleActuatorCommandMessage(ad)

	def _handleUpstreamTransmission(self, resourceName: ResourceNameEnum, msg: str):
		logging.debug("Upstream transmission (not yet implemented): " + str(resourceName))
