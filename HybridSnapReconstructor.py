#  .---------------------------------------------------------------------------.
#  |                                                                           |
#  |            H Y B R I D   S N A P    R E C O N S T R U C T O R             |
#  |                                                                           |
#  '---------------------------------------------------------------------------'

import pdb
import inspect
from copy import *
from enum import Enum
from Globals import *
from Vector import Vector
from Sample import Sample
from PredictionSample import PredictionSample

class HybridSnapReconstructor(object):
    
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #       P U B L I C   F U N C T I O N S
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __init__(self):
        # Data
        self.rawSignal = []
        self.reconstructedSignal = []
        # Algorithm parameters
        self.samplingInterval = 10
        self.interpolationType = InterpolationType.Time
        self.snapType = SnapLimitType.Relative
        self.threshold = 100
        self.heartbeatRate = 500
        self.snapLimit = 0.5
        
    def getReconstructedSignal(self, rawSignal=[], samplingInterval=10,
                               interpolationType=InterpolationType.Time,
							   snapLimitType=SnapLimitType.Relative,
							   threshold=100, heartbeatRate=500, snapLimit=0.5):
        if isinstance( rawSignal, list ):
            self.rawSignal = rawSignal
        if isinstance( samplingInterval, int ) and samplingInterval > 0:
            self.samplingInterval = samplingInterval
        if isinstance( interpolationType, Enum ):
            self.interpolationType = interpolationType
        if isinstance( snapLimitType, Enum ):
            self.snapType = snapLimitType
        if (isinstance( threshold, float ) and threshold > 0) or \
           (isinstance(threshold, int ) and threshold > 0):
            self.threshold = threshold
        if isinstance( heartbeatRate, int ) and heartbeatRate > 0:
            self.heartbeatRate = heartbeatRate
        if isinstance( snapLimit, float ) and snapLimit > 0:
            self.snapLimit = snapLimit

        self.snapType = snapLimitType
        self.pullDataFromPackets()
        self.executeAlgorithm()
        self.resampleData()
		
        return self.reconstructedSignal
    
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #       P R I V A T E   F U N C T I O N S
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def pullDataFromPackets(self):
		temp = []
		for packet in self.rawSignal:
			temp.append(packet.predictionSample)
		
		self.rawSignal = temp
    
    def executeAlgorithm(self):
		self.reconstructedSignal = []
		self.reconstructedSignal.append( deepcopy(self.rawSignal[0].sample) )
		extrapolationSample = self.rawSignal[0]
		futureExtrapolationSample = None
		nextTimeToRecord = self.reconstructedSignal[0].time + 1
		
		tempRawSignal = self.rawSignal[1:]
		for index, predictionSample in enumerate(tempRawSignal):
			while predictionSample.sample.time > nextTimeToRecord:
				if futureExtrapolationSample != None and \
				   futureExtrapolationSample.sample.time == nextTimeToRecord:
					extrapolationSample = futureExtrapolationSample
					futureExtrapolationSample = None
					self.reconstructedSignal.append( deepcopy(extrapolationSample.sample) )
				else:
					estimatedSample = self.estSample(extrapolationSample, nextTimeToRecord)
					self.reconstructedSignal.append( deepcopy(estimatedSample) )
					
				nextTimeToRecord += 1
							
			lastEstimatedSample = self.reconstructedSignal[-1]
			estimatedSample = self.estSample(extrapolationSample, nextTimeToRecord)
			updateSample = predictionSample.sample
			targetSample = self.calcTargetSample(predictionSample)
			snapSample = self.calcSnapSample(lastEstimatedSample, lastEstimatedSample, 
											 updateSample, targetSample)
			extrapolationSample = self.calcExtrapolationSample(snapSample, targetSample)
			futureExtrapolationSample = PredictionSample(targetSample, predictionSample.velocity)
			self.reconstructedSignal.append( deepcopy(snapSample) )
			nextTimeToRecord += 1

    def estSample(self, predictionSample, time):
        deltaTime = time - predictionSample.sample.time
        if time < 0:
            print "Error: must estimate a position in the future"
            return deepcopy( predictionSample.sample )

        deltaTimeVector = Vector(deltaTime, deltaTime, deltaTime)
        deltaPosition = predictionSample.velocity * deltaTimeVector
        estimatedPosition = predictionSample.sample.position + deltaPosition
        estimatedSample = Sample(time, estimatedPosition)

        return estimatedSample	

    def calcSnapSample(self, lastEstimatedSample, estimatedSample, updateSample, targetSample):
		if self.snapType == SnapLimitType.Absolute:
			return self.calcAbsoluteSnapSample(lastEstimatedSample, estimatedSample, 
											   updateSample, targetSample)
		elif self.snapType == SnapLimitType.Relative:
			return self.calcRelativeSnapSample(lastEstimatedSample, estimatedSample, 
			    							   updateSample, targetSample)
			
    def calcRelativeSnapSample(self, lastEstimatedSample, estimatedSample, 
							  updateSample, targetSample):
		estDiff = estimatedSample.position - lastEstimatedSample.position
		updateDiff = updateSample.position - lastEstimatedSample.position
		targetDiff = targetSample.position - lastEstimatedSample.position
		
		if cmp(estDiff.x, 0):
			# Moving positive
			if cmp(updateDiff.x, 0):
				# Jump positive
				updateDiff.x *= self.snapLimit
			else:
				# Jump negative
				if cmp(targetDiff.x, 0):
					# Moving positive from update
					updateDiff.x = estDiff.x
				else:
					# Moving negative from update
					updateDiff.x *= self.snapLimit
					#updateDiff.x = estDiff.x
		else:
			# Moving negative
			if cmp(updateDiff.x, 0):
				# Jump positive
				if cmp(targetDiff.x, 0):
					# Moving positive from update
					updateDiff.x *= self.snapLimit
				else:
					# Moving negative from update
					updateDiff.x = estDiff.x
			else:
				# Jump negative
				updateDiff.x *= self.snapLimit
				
		if cmp(estDiff.y, 0):
			# Moving positive
			if cmp(updateDiff.y, 0):
				# Jump positive
				updateDiff.y *= self.snapLimit
			else:
				# Jump negative
				if cmp(targetDiff.y, 0):
					# Moving positive from update
					updateDiff.y = estDiff.y
				else:
					# Moving negative from update
					updateDiff.y *= self.snapLimit
		else:
			# Moving negative
			if cmp(updateDiff.y, 0):
				# Jump positive
				if cmp(targetDiff.y, 0):
					# Moving positive from update
					updateDiff.y *= self.snapLimit
				else:
					# Moving negative from update
					updateDiff.y = estDiff.y
			else:
				# Jump negative
				updateDiff.y *= self.snapLimit
				
		if cmp(estDiff.z, 0):
			# Moving positive
			if cmp(updateDiff.z, 0):
				# Jump positive
				updateDiff.z *= self.snapLimit
			else:
				# Jump negative
				if cmp(targetDiff.z, 0):
					# Moving positive from update
					updateDiff.z = estDiff.z
				else:
					# Moving negative from update
					updateDiff.z *= self.snapLimit
		else:
			# Moving negative
			if cmp(updateDiff.z, 0):
				# Jump positive
				if cmp(targetDiff.z, 0):
					# Moving positive from update
					updateDiff.z *= self.snapLimit
				else:
					# Moving negative from update
					updateDiff.z = estDiff.z
			else:
				# Jump negative
				updateDiff.z *= self.snapLimit
		
		snapPosition = lastEstimatedSample.position + updateDiff
		snapSample = Sample(updateSample.time, snapPosition)

		return snapSample
		
    def calcAbsoluteSnapSample(self, lastEstimatedSample, estimatedSample, 
							   updateSample, targetSample):
		return updateSample
			
    def calcTargetSample(self, predictionSample):
        if self.interpolationType == InterpolationType.Time:
            return self.calcTargetForTimeThreshold(predictionSample)
        elif self.interpolationType == Interpolation.Distance:
			return self.calcTargetForDistanceThreshold(predictionSample)
	
    def calcTargetForTimeThreshold(self, predictionSample):
		time = min(self.threshold, self.heartbeatRate)
		targetSample = self.estSample(predictionSample, predictionSample.sample.time + time)
		return targetSample
	
    def calcTargetForDistanceThreshold(self, predictionSample):
        distance = 0
        targetSample = None
        time = predictionSample.sample.time
        timeDiff = 0

        while distance < self.threshold and timeDiff < self.heartbeatRate:
            time += 1
            timeDiff = time - predictionSample.sample.time
            targetSample = self.estSample(predictionSample, time)
            distance = predictionSample.sample.position.distance(target.sample.position)

        return targetSample

    def calcExtrapolationSample(self, snapSample, targetSample):
		deltaPosition = targetSample.position - snapSample.position
		deltaTime = targetSample.time - snapSample.time
		invDeltaTimeVector = Vector( 1 / float(deltaTime), \
		                             1 / float(deltaTime), \
		                             1 / float(deltaTime))
		velocity = deltaPosition * invDeltaTimeVector

		extrapolationSample = PredictionSample()
		extrapolationSample.sample = deepcopy(snapSample)
		extrapolationSample.velocity = velocity
		return extrapolationSample

    def resampleData(self):
        temp = []
        for sample in self.reconstructedSignal:
            if (sample.time % self.samplingInterval) == 0:
                temp.append(sample)
		
            self.reconstructedSignal = temp
