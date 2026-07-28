#####
#
# This class is part of the Programming the Internet of Things project.
#
# It is provided as a simple shell to guide the student and assist with
# implementation for the Programming the Internet of Things exercises,
# and designed to be modified by the student as needed.
#

import logging
import socket
import traceback

from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.messages.option import Option
from coapthon.utils import generate_random_token

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

from programmingtheiot.data.DataUtil import DataUtil

class CoapClientConnector(IRequestResponseClient):
	"""
	CoAP client connector implementation using the CoAPthon3 library.
	Provides GET, PUT, POST, DELETE, DISCOVERY and OBSERVE functionality
	against a remote CoAP server (hosted by the GDA).
	"""

	def __init__(self, dataMsgListener: IDataMessageListener = None):
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		self.coapClient = None

		self.observeRequests = { }

		self.host = \
			self.config.getProperty( \
				ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		self.port = \
			self.config.getInteger( \
				ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_COAP_PORT)

		self.includeDebugLogDetail = True

		try:
			tmpHost = socket.gethostbyname(self.host)

			if tmpHost:
				self.host = tmpHost
				self.uriPath = f"coap://{self.host}:{self.port}/"
				logging.info(f"CoAP client will connect to: {self.uriPath}")
				self._initClient()
			else:
				logging.error(f"Can't resolve host: {self.host}")
				raise

		except socket.gaierror:
			logging.error(f"Failed to resolve host: {self.host}")
			raise

	def sendDeleteRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			logging.info(f"Issuing DELETE with path: {resourcePath}")

			request = self.coapClient.mk_request(defines.Codes.DELETE, path = resourcePath)
			request.token = generate_random_token(2)

			if not enableCON:
				request.type = defines.Types["NON"]

			self.coapClient.send_request(request = request, callback = self._onDeleteResponse, timeout = timeout)

			return True
		else:
			logging.warning("Can't test DELETE - no path or path list provided.")

			return False

	def sendGetRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			logging.info(f"Issuing GET with path: {resourcePath}")

			request = self.coapClient.mk_request(defines.Codes.GET, path = resourcePath)
			request.token = generate_random_token(2)

			if not enableCON:
				request.type = defines.Types["NON"]

			response = self.coapClient.send_request(request = request, timeout = timeout)

			self._onGetResponse(response = response, resourcePath = resourcePath)

			return True
		else:
			logging.warning("Can't test GET - no path or path list provided.")

			return False

	def sendPostRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			logging.info(f"Issuing POST with path: {resourcePath}")

			request = self.coapClient.mk_request(defines.Codes.POST, path = resourcePath)
			request.token = generate_random_token(2)
			request.payload = payload

			if not enableCON:
				request.type = defines.Types["NON"]

			logging.info(f"Sending POST with payload: {payload}")

			self.coapClient.send_request(request = request, callback = self._onPostResponse, timeout = timeout)

			return True
		else:
			logging.warning("Can't test POST - no path or path list provided.")

			return False

	def sendPutRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)

			logging.info(f"Issuing PUT with path: {resourcePath}")

			request = self.coapClient.mk_request(defines.Codes.PUT, path = resourcePath)
			request.token = generate_random_token(2)
			request.payload = payload

			if not enableCON:
				request.type = defines.Types["NON"]

			self.coapClient.send_request(request = request, callback = self._onPutResponse, timeout = timeout)

			return True
		else:
			logging.warning("Can't test PUT - no path or path list provided.")

			return False

	def sendDiscoveryRequest(self, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		logging.info("Discovering remote resources...")

		resourcePath = self._createResourcePath(None, '.well-known/core')

		logging.info(f"Issuing DISCOVERY with path: {resourcePath}")

		request = self.coapClient.mk_request(defines.Codes.GET, path = resourcePath)
		request.token = generate_random_token(2)

		self.coapClient.send_request(request = request, timeout = timeout, callback = self._onDiscoveryResponse)

		return True

	def startObserver(self, resource: ResourceNameEnum = None, name: str = None, ttl: int = ConfigConst.DEFAULT_TTL) -> bool:
		if resource or name:
			if resource in self.observeRequests:
				logging.warning(f"Already observing resource {resource}. Ignoring start observe request.")
				return False

			self.observeRequests[resource] = None

			resourcePath = self._createResourcePath(resource, name)

			observeActuatorCmdHandler = \
				HandleActuatorEvent( \
					listener = self.dataMsgListener, resource = resource, requests = self.observeRequests)

			try:
				self.coapClient.observe(path = resourcePath, callback = observeActuatorCmdHandler.handleActuatorResponse)

				return True
			except Exception as e:
				logging.warning(f"Failed to observe path: {resourcePath}")

				return False
		else:
			logging.warning("Can't start observe - no path or path list provided.")

			return False

	def stopObserver(self, resource: ResourceNameEnum = None, name: str = None, timeout: int = ConfigConst.DEFAULT_TIMEOUT) -> bool:
		if resource or name:
			if not resource in self.observeRequests:
				logging.warning(f"Resource {resource} not being observed. Ignoring stop observe request.")
				return False

			response = self.observeRequests[resource]

			if response:
				logging.info(f"Cancelling observe for resource {resource}.")

				try:
					self.coapClient.cancel_observing(response = response, send_rst = True)

					del self.observeRequests[resource]

					logging.info(f"Cancelled observe for resource {resource}.")

					return True
				except Exception as e:
					logging.warning(f"Failed to cancel observe for resource {resource}")
					traceback.print_exception(type(e), e, e.__traceback__)

					return False
			else:
				logging.warning(f"No response yet for observed resource {resource}. Attempting to stop anyway.")

				try:
					self.coapClient.cancel_observing(response = None, send_rst = True)
					logging.info(f"Canceled observe for resource {resource}.")

					return True
				except Exception as e:
					logging.warning(f"Failed to cancel observe for resource {resource}.")
					traceback.print_exception(type(e), e, e.__traceback__)

					return False
		else:
			logging.warning("Can't stop observe - no path or path list provided.")

			return False

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True

		return False

	def _createResourcePath(self, resource: ResourceNameEnum = None, name: str = None):
		resourcePath = ""
		hasResource = False

		if resource:
			resourcePath = resourcePath + resource.value
			hasResource = True

		if name:
			if hasResource:
				resourcePath = resourcePath + "/"

			resourcePath = resourcePath + name

		return resourcePath

	def _initClient(self):
		try:
			self.coapClient = HelperClient(server = (self.host, self.port))

			logging.info(f"Client created. Will invoke resources at {self.uriPath}")

		except Exception as e:
			logging.error(f"Failed to create CoAP client to URI path {self.uriPath}")
			traceback.print_exception(type(e), e, e.__traceback__)

	def _onDeleteResponse(self, response):
		if not response:
			logging.warning("DELETE response invalid. Ignoring.")
			return

		logging.info(f"DELETE response received: {response.payload}")

	def _onGetResponse(self, response, resourcePath: str = None):
		if not response:
			logging.warning("GET response invalid. Ignoring.")
			return

		logging.info("GET response received.")

		jsonData = response.payload
		locationPath = resourcePath.split('/')

		if len(locationPath) > 2:
			dataType = locationPath[2]

			if dataType == ConfigConst.ACTUATOR_CMD:
				logging.info(f"ActuatorData received: {jsonData}")

				try:
					ad = DataUtil().jsonToActuatorData(jsonData)

					if self.dataMsgListener:
						self.dataMsgListener.handleActuatorCommandMessage(ad)
				except:
					logging.warning(f"Failed to decode actuator data. Ignoring: {jsonData}")
					return
			else:
				logging.info(f"Response data received. Payload: {jsonData}")
		else:
			logging.info(f"Response data received. Payload: {jsonData}")

	def _onPostResponse(self, response):
		if not response:
			logging.warning("POST response invalid. Ignoring.")
			return

		logging.info(f"POST response received: {response.payload}")

	def _onPutResponse(self, response):
		if not response:
			logging.warning("PUT response invalid. Ignoring.")
			return

		logging.info(f"PUT response received: {response.payload}")

	def _onDiscoveryResponse(self, response):
		if not response:
			logging.warning("DISCOVERY response invalid. Ignoring.")
			return

		logging.info(f"DISCOVERY response received: {response.payload}")

class HandleActuatorEvent():
	"""
	Internal callback container used by the OBSERVE functionality.
	Receives ActuatorData updates pushed by the CoAP server and forwards
	them to the IDataMessageListener (DeviceDataManager).
	"""

	def __init__(self, \
			listener: IDataMessageListener = None, \
			resource: ResourceNameEnum = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, \
			requests = None):

		self.listener = listener
		self.resource = resource
		self.observeRequests = requests

		if not self.resource:
			self.resource = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE

	def handleActuatorResponse(self, response):
		if response:
			jsonData = response.payload

			if self.observeRequests is not None:
				self.observeRequests[self.resource] = response

			logging.info(f"Received actuator command response to resource {self.resource} -> {jsonData}")

			if self.listener:
				try:
					data = DataUtil().jsonToActuatorData(jsonData = jsonData)
					self.listener.handleActuatorCommandMessage(data = data)

				except:
					logging.warning(f"Failed to decode actuator data. Ignoring: {jsonData}")
