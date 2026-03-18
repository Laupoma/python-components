import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

class TemperatureSensorSimTask(BaseSensorSimTask):

	def __init__(self, dataSet = None):
		super( \
			TemperatureSensorSimTask, self).__init__( \
				name = ConfigConst.TEMP_SENSOR_NAME, \
				typeID = ConfigConst.TEMP_SENSOR_TYPE, \
				dataSet = dataSet, \
				minVal = SensorDataGenerator.LOW_NORMAL_INDOOR_TEMP, \
				maxVal = SensorDataGenerator.HI_NORMAL_INDOOR_TEMP)
