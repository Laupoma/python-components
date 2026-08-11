#####
#
# This class is part of the Programming the Internet of Things project.
#
import logging
import time
import ssl
import paho.mqtt.client as mqttClient

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

from programmingtheiot.data.DataUtil import DataUtil

class MqttClientConnector(IPubSubClient):
	"""
	Shell representation of class for student implementation.
	"""

	def __init__(self, clientID: str = None):
		self.config = ConfigUtil()
		self.dataMsgListener = None

		self.host = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)

		self.port = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_MQTT_PORT)

		self.keepAlive = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.KEEP_ALIVE_KEY, ConfigConst.DEFAULT_KEEP_ALIVE)

		self.defaultQos = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.DEFAULT_QOS_KEY, ConfigConst.DEFAULT_QOS)


		# TLS: leer si el cifrado esta habilitado y la ruta al certificado (.pem)
		# del broker. Por ahora enableEncryption estara en False en PiotConfig.props,
		# asi que este cliente seguira conectandose sin cifrar (puerto 1883).
		self.enableEncryption = \
			self.config.getBoolean( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.ENABLE_CRYPT_KEY)

		self.pemFileName = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.CERT_FILE_KEY)
		self.mqttClient = None

		if not clientID:
			clientID = 'CDAMqttClientID001'

		self.clientID = \
			self.config.getProperty( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.DEVICE_LOCATION_ID_KEY, clientID)

		logging.info('\tMQTT Client ID:   ' + self.clientID)
		logging.info('\tMQTT Broker Host: ' + self.host)
		logging.info('\tMQTT Broker Port: ' + str(self.port))
		logging.info('\tMQTT Keep Alive:  ' + str(self.keepAlive))

	def connectClient(self) -> bool:
		if not self.mqttClient:
			self.mqttClient = mqttClient.Client(client_id = self.clientID, clean_session = True)


			# TLS: si el cifrado esta habilitado, cambiar al puerto seguro (8883)
			# y cargar el certificado del broker antes de conectar. El try/except
			# asegura que si algo falla, cae a conexion sin cifrar en vez de romper.
			try:
				if self.enableEncryption:
					logging.info("Enabling TLS encryption...")

					self.port = \
						self.config.getInteger( \
							ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.SECURE_PORT_KEY, ConfigConst.DEFAULT_MQTT_SECURE_PORT)

					self.mqttClient.tls_set(self.pemFileName, tls_version = ssl.PROTOCOL_TLS_CLIENT)
					self.mqttClient.tls_set_context(context = None)
			except:
				logging.warning("Failed to enable TLS encryption. Using unencrypted connection.")

			self.mqttClient.on_connect    = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message    = self.onMessage
			self.mqttClient.on_publish    = self.onPublish
			self.mqttClient.on_subscribe  = self.onSubscribe

		if not self.mqttClient.is_connected():
			logging.info('MQTT client connecting to broker at host: ' + self.host)
			self.mqttClient.connect(self.host, self.port, self.keepAlive)
			self.mqttClient.loop_start()

			# NOTA: connect() y loop_start() son asincronos. connect() solo INICIA
			# la conexion y retorna al instante; el handshake real con el broker
			# ocurre en el hilo de fondo de loop_start(). Si devolvieramos True aca,
			# el metodo mentiria (diria "conectado" antes de estarlo), lo que rompia
			# el test de performance. Solucion: esperar activamente hasta que
			# is_connected() confirme, con un limite de intentos (timeout) para que
			# NUNCA se cuelgue de forma infinita si el broker no responde.
			maxConnAttempts = 50   # 50 x 0.1s = hasta 5 segundos de espera
			connAttempt = 0

			while not self.mqttClient.is_connected() and connAttempt < maxConnAttempts:
				time.sleep(0.1)
				connAttempt += 1

			if self.mqttClient.is_connected():
				logging.info('MQTT client connected to broker at host: ' + self.host)
				return True
			else:
				logging.warning('MQTT client failed to connect within timeout. Host: ' + self.host)
				return False
		else:
			logging.warning('MQTT client is already connected. Ignoring connect request.')

			return False

	def disconnectClient(self) -> bool:
		if self.mqttClient.is_connected():
			logging.info('Disconnecting MQTT client from broker: ' + self.host)
			self.mqttClient.loop_stop()
			self.mqttClient.disconnect()

			return True
		else:
			logging.warning('MQTT client already disconnected. Ignoring.')

			return False

	def onConnect(self, client, userdata, flags, rc):
		if rc == 0:
			logging.info('MQTT client connected to broker: ' + str(client))

			# Suscribirse al topic de comandos de actuacion SOLO tras conexion exitosa.
			# subscribe() registra la suscripcion; message_callback_add() redirige los
			# mensajes de ese topic al callback especifico onActuatorCommandMessage().
			self.mqttClient.subscribe( \
				topic = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value, qos = self.defaultQos)

			self.mqttClient.message_callback_add( \
				sub = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value, \
				callback = self.onActuatorCommandMessage)
		else:
			logging.warning('MQTT client failed to connect. Result code: ' + str(rc))

	def onDisconnect(self, client, userdata, rc):
		logging.info('MQTT client disconnected from broker: ' + str(client))

	def onMessage(self, client, userdata, msg):
		payload = msg.payload

		if payload:
			logging.info('MQTT message received with payload: ' + str(payload.decode("utf-8")))
		else:
			logging.info('MQTT message received with no payload: ' + str(msg))

	def onPublish(self, client, userdata, mid):
		#logging.info('MQTT message published: ' + str(client))
		pass

	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info('MQTT client subscribed: ' + str(client))

	def onActuatorCommandMessage(self, client, userdata, msg):
		logging.info('[Callback] Actuator command message received. Topic: %s.', msg.topic)

		if self.dataMsgListener:
			try:
				# se asume que todo viaja codificado en UTF-8 entre GDA y CDA
				actuatorData = DataUtil().jsonToActuatorData(msg.payload.decode('utf-8'))
				self.dataMsgListener.handleActuatorCommandMessage(actuatorData)
			except:
				logging.exception("Failed to convert incoming actuation command payload to ActuatorData: ")

	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		if not resource:
			logging.warning('No topic specified. Cannot publish message.')
			return False

		if not msg:
			logging.warning('No message specified. Cannot publish message to topic: ' + resource.value)
			return False

		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS

		msgInfo = self.mqttClient.publish(topic = resource.value, payload = msg, qos = qos)

		# NOTA: wait_for_publish() se comenta a proposito. Bloquea el cliente MQTT
		# hasta que la publicacion termina, lo que en un sistema que publica Y escucha
		# a la vez puede causar deadlock (traba la recepcion de suscripciones). Al
		# comentarlo, publishMessage retorna sin bloquear. El True ya NO garantiza
		# publicacion exitosa; se podria verificar despues con msgInfo.is_published().
		#msgInfo.wait_for_publish()

		return True

	def subscribeToTopic(self, resource: ResourceNameEnum = None, callback = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		if not resource:
			logging.warning('No topic specified. Cannot subscribe.')
			return False

		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS

		logging.info('Subscribing to topic %s', resource.value)
		self.mqttClient.subscribe(resource.value, qos)

		return True

	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None) -> bool:
		if not resource:
			logging.warning('No topic specified. Cannot unsubscribe.')
			return False

		logging.info('Unsubscribing from topic %s', resource.value)
		self.mqttClient.unsubscribe(resource.value)

		return True

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
