import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.data.BaseIotData import BaseIotData

class SensorData(BaseIotData):

	def __init__(self, typeID: int = ConfigConst.DEFAULT_SENSOR_TYPE, name = ConfigConst.NOT_SET, d = None):
		super(SensorData, self).__init__(name = name, typeID = typeID, d = d)
		
		self.value = ConfigConst.DEFAULT_VAL

	def getValue(self) -> float:
		return self.value

	def setValue(self, newVal: float):
		self.value = newVal
		self.updateTimeStamp()

	def _handleUpdateData(self, data):
		if data and isinstance(data, SensorData):
			self.value = data.getValue()

	def __str__(self):
		return 'SensorData: name={}, typeID={}, value={}'.format(
			self.name,
			self.typeID,
			self.value
		)
