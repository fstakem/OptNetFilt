#!/usr/bin/env python
# encoding: utf-8
"""
TestSnapLimit.py

Created by Fredrick Stakem on 2010-03-27.
Copyright (c) 2010 __Research__. All rights reserved.
"""

# Import libraries
#------------------------------------------------------------------------------
import Simulator as s
import pdb
import numpy
import scipy
import scipy.signal
import pylab
import time
import math
from enum import Enum
from Globals import *

# Filesystem paramters
#------------------------------------------------------------------------------
dataRoot = "/Users/fstakem/Data/Movements_5_1_08/"
root = "/Users/fstakem/Research/OptimalFiltering/"
logDir = root + "code/log/"
outputDir = root + "code/output/"
movement = "Stacking"
# TODO -> increase the number of simulations
simulations = range(1,2)
inputFiles = []
for i in simulations:
    inputFile = dataRoot + movement + "/Simulation" + str(i) + \
				"/positionLog.txt"
    inputFiles.append(inputFile)

# Transmission parameters
#------------------------------------------------------------------------------
predictionInterval = 100
samplingInterval = 10
heartbeat = 500
drThreshold = 0.02
convergenceType = InterpolationType.Time

# Network parameters
#------------------------------------------------------------------------------
delay = 100
jitter = 20
packetLoss = 0

# Reconstruction parameters
#------------------------------------------------------------------------------
#convergenceTimes = range(10,510,10)
#relativeSnapLimits = [ .1, .3, .5, .7, .9 ]
# TODO -> pick better values for absolute
#absoluteSnapLimits = [ .002, .004, .006, .008, .01 ]
convergenceTimes = range(80,130,10)
relativeSnapLimits = scipy.linspace(.1, .9, 9) 
# TODO -> pick better values for absolute
absoluteSnapLimits = scipy.linspace(.0002, .002, 10) 

# Calculation parameters
#------------------------------------------------------------------------------
jumpThreshold = 0
jumpSpacing = 1

# Plotting parameters
#------------------------------------------------------------------------------
plotDistance = False
plotJump = False
plotMean = False
plotMedian = False

# Create the output data structures
#------------------------------------------------------------------------------
outputData = []
inputStats = None
outputStats = []
algorithms = 2
files = len(inputFiles)
for i in range(0,algorithms):
	outputData.append([])
	outputStats.append([])

algorithm = 0
for snapLimit in relativeSnapLimits:
	outputData[algorithm].append([])
	outputStats[algorithm].append([])
	
	for convergenceTime in convergenceTimes:
		outputData[algorithm][-1].append([])
		outputStats[algorithm][-1].append([])

algorithm = 1
for snapLimit in absoluteSnapLimits:
	outputData[algorithm].append([])
	outputStats[algorithm].append([])
	
	for convergenceTime in convergenceTimes:
		outputData[algorithm][-1].append([])
		outputStats[algorithm][-1].append([])

# Simulate the transmission of the data
#------------------------------------------------------------------------------
startTimeTotal = time.time()
transmittedData = []
for inputFile in inputFiles:
	simNumber = inputFile.split('/')[-2][-1]
	print "Simulating the transmission for simulation: " + str(simNumber)
	
	data = s.transmitData(inputFile, logDir, predictionInterval,
						  samplingInterval, heartbeat, drThreshold,
						  delay, jitter, packetLoss)
	transmittedData.append(data)

print "Total time spent simulating the transmission: " + str(time.time() - \
															 startTimeTotal)
print

# Simulate the reconstruction of the data
#------------------------------------------------------------------------------
# Simulate relative snap reconstruction
startTimeRel = time.time()
algorithm = 0
print "Simulating relative snap reconstruction..."
for i, snapLimit in enumerate(relativeSnapLimits):
	print "\tSimulating snap limit: " + str(snapLimit)
	startTimeSnap = time.time()
	
	for j, convergenceTime in enumerate(convergenceTimes):
		print "\t\tSimulating convergence time: " + str(convergenceTime)
		startTimeConverge = time.time()
		
		for k, data in enumerate(transmittedData):
			print "\t\t\tSimulating data set: " + str(k+1)
			rawInputData = data[0]
			filteredInputData = data[1]
			predictedData = data[2]
			drTxPackets = data[3]
			drRxPackets = data[4]
			drRxFilteredPackets = data[5]
			
			relativeSnapData = s.snapLimitReconstructData(drRxFilteredPackets,
														  logDir,
														  simNumber,
														  samplingInterval,
											              convergenceType,
														  SnapLimitType.Relative,
														  convergenceTime,
											              snapLimit)[0]
			outputData[algorithm][i][j].append(relativeSnapData)
		
		print "\t\tSimulation time for all of the data sets: " + \
			  str(time.time() - startTimeConverge)
	print "\t\tSimulation time for all of the convergence values sets: " + \
	      str(time.time() - startTimeSnap)

# Simulate absolute snap reconstruction
startTimeAbs = time.time()
algorithm = 1
print "Simulating absolute snap reconstruction..."
for i, snapLimit in enumerate(absoluteSnapLimits):
	print "\tSimulating snap limit: " + str(snapLimit)
	startTimeSnap = time.time()
	
	for j, convergenceTime in enumerate(convergenceTimes):
		print "\t\tSimulating convergence time: " + str(convergenceTime)
		startTimeConverge = time.time()
		
		for k, data in enumerate(transmittedData):
			print "\t\t\tSimulating data set: " + str(k+1)
			rawInputData = data[0]
			filteredInputData = data[1]
			predictedData = data[2]
			drTxPackets = data[3]
			drRxPackets = data[4]
			drRxFilteredPackets = data[5]
			
			absoluteSnapData = s.snapLimitReconstructData(drRxFilteredPackets,
														  logDir,
														  simNumber,
														  samplingInterval,
											              convergenceType,
														  SnapLimitType.Absolute,
														  convergenceTime,
											              snapLimit)[0]
			outputData[algorithm][i][j].append(absoluteSnapData)
		
		print "\t\tSimulation time for all of the data sets: " + \
			  str(time.time() - startTimeConverge)
	print "\t\tSimulation time for all of the convergence values sets: " + \
	      str(time.time() - startTimeSnap)

# Calculate the results and statistics
#------------------------------------------------------------------------------
distanceJumps = []

for inputData in transmittedData:
	initialData = inputData[1]
	distanceJump = s.findDistanceBetweenSamples(initialData,
											    jumpThreshold,
											    jumpSpacing)
	distanceJumps.append( s.calculateStats(distanceJump) )

inputStats = [ s.aggregateStats(distanceJumps) ]


for i, algorithm in enumerate(outputData):
    for j, snapLimit in enumerate(algorithm):
        for k, convergenceTime in enumerate(snapLimit):
            distanceErrors = []
            distanceJumps = []
            stats = []
            for l, reconstructedData in enumerate(convergenceTime):
                inputData = transmittedData[l][1]
                distanceError = s.findDistanceError(inputData,
													reconstructedData)
                distanceErrors.append( s.calculateStats(distanceError) )
				
                distanceJump = s.findDistanceBetweenSamples(reconstructedData,
															jumpThreshold,
															jumpSpacing)
                distanceJumps.append( s.calculateStats(distanceJump) )
				
            outputStats[i][j][k].append( s.aggregateStats(distanceErrors) )
            outputStats[i][j][k].append( s.aggregateStats(distanceJumps) )

# Create the curves to be plotted
#------------------------------------------------------------------------------
relativeErrorMeans = []
relativeErrorMedians = []
relativeJumpMeans = []
relativeJumpMedians = []
absoluteErrorMeans = []
absoluteErrorMedians = []
absoluteJumpMeans = []
absoluteJumpMedians = []

algorithm = 0
for i, snapLimit in enumerate(relativeSnapLimits):
	relativeErrorMean = []
	relativeErrorMedian = []
	relativeJumpMean = []
	relativeJumpMedian = []
	for j, convergenceTime in enumerate(convergenceTimes):
		relativeErrorMean.append(outputStats[algorithm][i][j][0][0])
		relativeErrorMedian.append(outputStats[algorithm][i][j][0][2])
		relativeJumpMean.append(outputStats[algorithm][i][j][1][0])
		relativeJumpMedian.append(outputStats[algorithm][i][j][1][2])
		
	relativeErrorMeans.append(relativeErrorMean)
	relativeErrorMedians.append(relativeErrorMedian)
	relativeJumpMeans.append(relativeJumpMean)
	relativeJumpMedians.append(relativeJumpMedian)
	
algorithm = 1
for i, snapLimit in enumerate(absoluteSnapLimits):
	absoluteErrorMean = []
	absoluteErrorMedian = []
	absoluteJumpMean = []
	absoluteJumpMedian = []
	for j, convergenceTime in enumerate(convergenceTimes):
		absoluteErrorMean.append(outputStats[algorithm][i][j][0][0])
		absoluteErrorMedian.append(outputStats[algorithm][i][j][0][2])
		absoluteJumpMean.append(outputStats[algorithm][i][j][1][0])
		absoluteJumpMedian.append(outputStats[algorithm][i][j][1][2])

	absoluteErrorMeans.append(absoluteErrorMean)
	absoluteErrorMedians.append(absoluteErrorMedian)
	absoluteJumpMeans.append(absoluteJumpMean)
	absoluteJumpMedians.append(absoluteJumpMedian)
	
# Output the data
#------------------------------------------------------------------------------
relativeErrors = [relativeErrorMeans, relativeErrorMedians, 
				  relativeJumpMeans, relativeJumpMedians]
				
for relativeError in relativeErrors:
	strOutput = ""
	for snapLimit in relativeSnapLimits:
		strOutput += "\t" + str(snapLimit)		
	print strOutput

	strOutput = ""
	for i, convergenceTime in enumerate(convergenceTimes):
		strOutput = str(convergenceTime)
		for j, error in enumerate(relativeError):
			strOutput += "\t" + str(relativeError[j][i])
		print strOutput
	print
	
absoluteErrors = [absoluteErrorMeans, absoluteErrorMedians, 
				  absoluteJumpMeans, absoluteJumpMedians]
				
for absoluteError in absoluteErrors:
	strOutput = ""
	for snapLimit in absoluteSnapLimits:
		strOutput += "\t" + str(snapLimit)		
	print strOutput

	strOutput = ""
	for i, convergenceTime in enumerate(convergenceTimes):
		strOutput = str(convergenceTime)
		for j, error in enumerate(absoluteError):
			strOutput += "\t" + str(absoluteError[j][i])
		print strOutput
	print

# Plot the statistics
#------------------------------------------------------------------------------
figure = 1
colors = ['k-']

if plotDistance == True:
	if plotMean == True:
		pylab.figure(figure)
		figure += 1
		for curve in relativeErrorMeans:
			pylab.plot(convergenceTimes, curve)

		pylab.figure(figure)
		figure += 1
		for curve in absoluteErrorMeans:
			pylab.plot(convergenceTimes, curve)

	if plotMedian == True:
		pylab.figure(figure)
		figure += 1
		for curve in relativeErrorMedians:
			pylab.plot(convergenceTimes, curve)

		pylab.figure(figure)
		figure += 1
		for curve in absoluteErrorMedians:
			pylab.plot(convergenceTimes, curve)
		
if plotJump == True:
	if plotMean == True:
		pylab.figure(figure)
		figure += 1
		for curve in relativeJumpMeans:
			pylab.plot(convergenceTimes, curve)

		pylab.figure(figure)
		figure += 1
		for curve in absoluteJumpMeans:
			pylab.plot(convergenceTimes, curve)

	if plotMedian == True:
		pylab.figure(figure)
		figure += 1
		for curve in relativeJumpMedians:
			pylab.plot(convergenceTimes, curve)

		pylab.figure(figure)
		figure += 1
		for curve in absoluteJumpMedians:
			pylab.plot(convergenceTimes, curve)

pylab.show()








