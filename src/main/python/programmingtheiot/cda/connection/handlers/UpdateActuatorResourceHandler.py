#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# Copyright (c) 2020 by Andrew D. King
# 

import logging

from coapthon import defines
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData

class UpdateActuatorResourceHandler(Resource):
	"""
	Resource handler that processes PUT requests from the GDA
	containing actuation commands for the CDA.
	"""

	def __init__(self, dataMsgListener: IDataMessageListener = None):
		super(UpdateActuatorResourceHandler, self).__init__(
			name = ConfigConst.ACTUATOR_CMD,
			coap_server = None,
			visible = True,
			observable = False,
			allow_children = False)

		self.dataMsgListener = dataMsgListener
		self.dataUtil        = DataUtil()

		self.pollCycles = \
			ConfigUtil().getInteger(
				section    = ConfigConst.CONSTRAINED_DEVICE,
				key        = ConfigConst.POLL_CYCLES_KEY,
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)

		logging.info("UpdateActuatorResourceHandler initialized.")

	def render_PUT_advanced(self, request, response):
		if request:
			logging.info("PUT request received for actuator command.")

			requestPayload = request.payload

			logging.info(f"Incoming actuator command payload: {requestPayload}")

			actuatorCmdData = self.dataUtil.jsonToActuatorData(requestPayload)

			response.payload = self._createResponse(
				response = response,
				data     = actuatorCmdData)

			response.max_age = self.pollCycles

		return self, response

	def _createResponse(self, response = None, data: ActuatorData = None) -> str:
		actuatorResponseData = None

		if self.dataMsgListener:
			actuatorResponseData = \
				self.dataMsgListener.handleActuatorCommandMessage(data)

		if not actuatorResponseData:
			actuatorResponseData = ActuatorData()
			actuatorResponseData.updateData(data)
			actuatorResponseData.setAsResponse()
			actuatorResponseData.setStatusCode(-1)

			response.code = defines.Codes.PRECONDITION_FAILED.number

			logging.warning("Actuator command failed - no response from listener.")
		else:
			response.code = defines.Codes.CHANGED.number

			logging.info("Actuator command processed successfully.")

		jsonData = self.dataUtil.actuatorDataToJson(actuatorResponseData)

		return (defines.Content_types["application/json"], jsonData)
