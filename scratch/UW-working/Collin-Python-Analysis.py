#!/usr/bin/python3




#the goal of the script is to write both the  mid and high level data processing files
#
#mid level processing files:
#Data Rate (bytes/s) (note 1) (1 file per UE), title (example) = dataRate,UE1,binWidth$binWidth.csv
#eNb association over time (note 1) (note 2) (1 file per UE), title (example) = eNbAssociation,UE1.csv
#RSRP over time (note 3) (1 file per UE), title (example) = RSRP,UE1.csv
#RSRQ over time (note 3) (1 file per UE), title (example) = RSRQ,UE1.csv
#
#note 1: Each trial will get a copy of each of these files. The file will be formatted as two lines. The first line is the 
#time axis, second line is the performance indicator, defined by the file title. The top level scenario folder will also 
#recieve an averaged version of this metric. the averaged version of these files will be formatted as first line = time, 
#second line = performance indicator, final line = 95% confidence interval (even bounds).
#
#note 2: This trace will not have an average, averaging this data makes no sense.
#
#note 3: Each trial will get a copy of each of these files. The file will be formatted as 3*numBS + 1 lines. The first line is the 
#time axis, the subsequent lines will be the rsrp/rsrq traces. line N indicates the trace comes from eNb ceil((N-1)/3), sector ((N-1) - 1) % 3 
#The top level scenario folder will also recieve an averaged version of this metric. The averaged version will be formatted as first line = time, 
#final line = 95% confidence interval (even bounds), starting with line 2 every other line will be the average value of the rsrp/rsrq
#across all trials over time and starting line 3 every other line will be the 95% confidence interval (even bounds).
#
#the top level scenario folder (the folder which contains each trial folder) will contain a version of each of these data files
#which has averaged appended to the title name which will be defined as the average of the relevant performance indicator for all trials
#and will be formatted as first line = time, line 2 to end-1 = performance indicator, final line = 95% confidence interval (even bounds).
#
#high level files:
#TBD on the exact formatting but it will be a record of ping pong ratio and too-early/too-late ratio


import sys
import math
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats
import os
import csv

scenario = sys.argv[1]
HystVal = float(sys.argv[2])
TTT = float(sys.argv[3])
trials = int(sys.argv[4])

print(" ")
print("Analysis Script Starting")

print("Determining Configuration Parameters")
configData = {}
with open("/home/collin/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario "+scenario+"/simulation_config.txt") as config:
	config_line = config.readline()
	while config_line:
		temp = config_line.split(':')
		if len(temp) == 2:
			if len(temp[1].split(' ')) == 3:
				configData[temp[0]] = float(temp[1])
			else:
				temp2 = temp[1].split(' ')
				configData[temp[0]] = [float(i) for i in temp2[1:(len(temp2)-1)]]
		config_line = config.readline()


numUE = int(configData["number of UEs"])
numBS = int(configData["number of BS"])
simuationDuration = configData["Simulation duration (s)"]
samplingFrequency = configData["Sampling Frequency (Hz)"]


print("Loading Data")
rsrpRsrqTime = []
rsrpData = []
rsrqData = []
currentServingCell = []
packetData = []

for i in range(trials):
	rsrpRsrqTime.append([])
	currentServingCell.append([])
	rsrpData.append([])
	rsrqData.append([])
	packetData.append([])
	for j in range(numUE):
		rsrpRsrqTime[i].append([])
		currentServingCell[i].append([])
		rsrpData[i].append([])
		rsrqData[i].append([])
		packetData[i].append({})
		for k in range(numBS):#initialize the rsrp/rsrq data dicts with numBS*3 values (3 sectors for each BS)
			rsrpData[i][j].append([])
			rsrqData[i][j].append([])
			for a in range(3):
				rsrpData[i][j][k].append([])
				rsrqData[i][j][k].append([])


lineCounter = 0
servingCellCount = 0
servingCellSetFlag = 0
resultsHome = "/home/collin/workspace/ns-3-dev-git/results/"
for i in range(trials):
	print("     Trial " + str(i+1))
	#first load the RSRP/RSRQ measurements
	scenarioFolder = "Scenario" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + "Scenario" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
	rsrpRsrqFilename = "lte-tcp-x2-handover.ue-measurements.dat"
	with open(resultsHome + scenarioFolder + rsrpRsrqFilename) as rsrpRsrqFile:
		rsrpRsrq_line = rsrpRsrqFile.readline()
		rsrpRsrq_line = rsrpRsrqFile.readline()#first line is just the header, skip it
		while rsrpRsrq_line:
			temp = rsrpRsrq_line.split()
			time = float(temp[0])
			imsi = int(temp[1])
			cellID = int(temp[2])
			servingCellFlag = int(temp[3])
			currentRsrp = float(temp[4])
			currentRsrq = float(temp[5])

			if (lineCounter % (numBS*3)) == 0:#not(int(1000*time) in [int(1000*x) for x in rsrpRsrqTime[i][imsi-1]]):
				rsrpRsrqTime[i][imsi-1].append(time)
				
			rsrpData[i][imsi-1][int(math.ceil((cellID)/3)-1)][int(((cellID - 1) % 3))].append(currentRsrp)
			rsrqData[i][imsi-1][int(math.ceil((cellID)/3)-1)][int(((cellID - 1) % 3))].append(currentRsrq)

			if servingCellFlag == 1:
				currentServingCell[i][imsi-1].append(cellID)
				servingCellSetFlag = 1

			if (lineCounter % (numBS*3)) == (numBS*3)-1:
				if servingCellSetFlag == 0:#this checks for the event that there is no serving cell, which occurs after RLFs
					currentServingCell[i][imsi-1].append(0)
				servingCellSetFlag = 0

			lineCounter = lineCounter + 1
			rsrpRsrq_line = rsrpRsrqFile.readline()

	#next the packet data
	packetFilename = "lte-tcp-x2-handover.tcp-receive.dat"
	with open(resultsHome + scenarioFolder + packetFilename) as packetFile:
		packet_line = packetFile.readline()
		packet_line = packetFile.readline()
		while packet_line:
			temp = packet_line.split()
			time = temp[0]
			bytesRx = int(temp[1])
			rxAddress = temp[2].split(':')
			rxAddress = int(rxAddress[3])
			if time in packetData[i][rxAddress-2]:
				packetData[i][rxAddress-2][time] = packetData[i][rxAddress-2][time] + bytesRx
			else:
				packetData[i][rxAddress-2][time] = bytesRx
			packet_line = packetFile.readline()

print("Finding Data Rate")
dataRate = []
dataRateTime = []

for i in range(trials):
	dataRate.append([])
	dataRateTime.append([])
	for j in range(numUE):
		dataRate[i].append([])
		dataRateTime[i].append([])

binWidth = 2;#number of points to average over

for i in range(trials):
    print("     Trial " +str(i+1))
    for j in range(numUE):
        if len(packetData[i][j].keys()) > 0:
            print("          UE " + str(j+1))
            packetTime = [float(x) for x in packetData[i][j].keys()]
            recievedBytes = list((packetData[i][j].values()))
            dataRateTime[i][j] = [float(i)/1000 for i in range(int(1000*simuationDuration))]
            recievedBytes2 = [0 for x in range(len(dataRateTime[i][j]))]
            for k in range(len(packetTime)):
                recievedBytes2[int(packetTime[k]*1000-1)] = recievedBytes[k]
            for k in range(len(dataRateTime[i][j])):
                if k < binWidth-1:
                    dataRate[i][j].append(sum([recievedBytes2[x]/(binWidth*.001) for x in range(k)]))
                else:
                    dataRate[i][j].append(sum([recievedBytes2[x]/(binWidth*.001) for x in range(k-binWidth+1,k)]))

#for i in range(numUE):
#    plt.plot(dataRateTime[0][i],dataRate[0][i],label="UE"+str(i+1))
#    plt.legend()
#    plt.show()

#for i in range(numUE):
#    for j in range(numBS):
#        for k in range(3):#number of sectors
#            plt.plot(rsrpRsrqTime[0][i],rsrpData[0][i][j][k],label="UE"+str(i+1)+", eNb"+str(j+1)+", sector"+str(k+1))
#    plt.plot(rsrpRsrqTime[0][i],currentServingCell[0][i],label="UE"+str(i+1)+", Current Serving Cell")
#    plt.legend()
#    plt.show()

#for i in range(numUE):
#    plt.plot(rsrpRsrqTime[0][i],currentServingCell[0][i],label="UE"+str(i+1)+", Current Serving Cell")
#    plt.legend()
#    plt.show()

if trials > 1:
    print("Finding Averages of Performance Indicators")
    #creating the variables to hold the averages
    averageDataRateTime = []
    averageDataRate = []
    dataRateConfidenceInterval = []
    
    averageRsrpRsrqTime = []
    averageRsrp = []
    averageRsrq = []
    rsrpConfidenceInterval = []
    rsrqConfidenceInterval = []
    
    for i in range(numUE):
        averageDataRateTime.append([])
        averageDataRate.append([])
        dataRateConfidenceInterval.append([])
        
        averageRsrpRsrqTime.append([])
        averageRsrp.append([])
        averageRsrq.append([])
        rsrpConfidenceInterval.append([])
        rsrqConfidenceInterval.append([])
        for j in range(numBS):
            averageRsrp[i].append([])
            averageRsrq[i].append([])
            rsrpConfidenceInterval[i].append([])
            rsrqConfidenceInterval[i].append([])
            for k in range(3):
                averageRsrp[i][j].append([])
                averageRsrq[i][j].append([])
                rsrpConfidenceInterval[i][j].append([])
                rsrqConfidenceInterval[i][j].append([])
    
    for i in range(numUE):
        print("     UE" + str(i+1))
        for j in range(int(1000*simuationDuration)):#first the data rate
            tempTime = [x[i][j] for x in dataRateTime]
            tempData = [x[i][j] for x in dataRate]
            averageDataRateTime[i].append(sum(tempTime)/len(tempTime))
            averageDataRate[i].append(sum(tempData)/len(tempData))
            tempDataArray = 1.0 * np.array(tempData)
            std = scipy.stats.sem(tempDataArray)
            CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
            dataRateConfidenceInterval[i].append(CI)
        
        for j in range(len(rsrpRsrqTime[0][0])):#next the RSRP/RSRQ
            tempTime = [x[i][j] for x in rsrpRsrqTime]
            averageRsrpRsrqTime[i].append(sum(tempTime)/len(tempTime))
            for k in range(numBS):
                for l in range(3):
                    tempRSRP = [x[i][k][l][j] for x in rsrpData]
                    tempRSRQ = [x[i][k][l][j] for x in rsrqData]
                    
                    averageRsrp[i][k][l].append(sum(tempRSRP)/len(tempRSRP))
                    averageRsrq[i][k][l].append(sum(tempRSRQ)/len(tempRSRQ))
                    
                    tempRsrpArray = 1.0 * np.array(tempRSRP)
                    std = scipy.stats.sem(tempRsrpArray)
                    CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
                    rsrpConfidenceInterval[i][k][l].append(CI)
                    
                    tempRsrqArray = 1.0 * np.array(tempRSRQ)
                    std = scipy.stats.sem(tempRsrqArray)
                    CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
                    rsrqConfidenceInterval[i][k][l].append(CI)

print("Writing Generated Traces")
home = os.getcwd()

#start with writing the files for each trial
for i in range(trials):
    scenarioFolder = "Scenario" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + "Scenario" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
    os.chdir(resultsHome + scenarioFolder)
    for j in range(numUE):
        #data rate
        temp  = [dataRateTime[i][j],dataRate[i][j]]
        file = open('dataRate-UE' + str(j+1) + '-binWidth' + str(binWidth*.001) + '.csv', 'w+', newline ='')
        with file:
            write = csv.writer(file)
            write.writerows(temp)

        #RSRP over time
        temp = [rsrpRsrqTime[i][j]]
        for k in range(numBS):
            for l in range(3):
                temp.append(rsrpData[i][j][k][l])
        file = open('RSRP-UE' + str(j+1) + '.csv', 'w+', newline ='')
        with file:
            write = csv.writer(file)
            write.writerows(temp)
        
        #RSRQ over time
        temp = [rsrpRsrqTime[i][j]]
        for k in range(numBS):
            for l in range(3):
                temp.append(rsrqData[i][j][k][l])
        file = open('RSRQ-UE' + str(j+1) + '.csv', 'w+', newline ='')
        with file:
            write = csv.writer(file)
            write.writerows(temp)

        #cell ID over time
        temp = [rsrpRsrqTime[i][j],currentServingCell[i][j]]
        file = open('currentServingCell-UE' + str(j+1) + '.csv', 'w+', newline ='')
        with file:
            write = csv.writer(file)
            write.writerows(temp)


#next the averages
scenarioFolder = "Scenario" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT))
os.chdir(resultsHome + scenarioFolder)
for i in range(numUE):
    #data rate
    temp = [averageDataRateTime[i],averageDataRate[i],dataRateConfidenceInterval[i]]
    file = open('AverageDataRate-UE' + str(i+1) + '-binWidth' + str(binWidth*.001) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
    with file:
    	write = csv.writer(file)
    	write.writerows(temp)
        
    #RSRP over Time
    temp = [averageRsrpRsrqTime[i]]
    for j in range(numBS):
        for k in range(3):
            temp.append(averageRsrp[i][j][k])
            temp.append(rsrpConfidenceInterval[i][j][k])
    file = open('AverageRSRP-UE' + str(i+1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
    with file:
    	write = csv.writer(file)
    	write.writerows(temp)

    #RSRQ over Time
    temp = [averageRsrpRsrqTime[i]]
    for j in range(numBS):
        for k in range(3):
            temp.append(averageRsrq[i][j][k])
            temp.append(rsrqConfidenceInterval[i][j][k])
    file = open('AverageRSRQ-UE' + str(i+1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
    with file:
    	write = csv.writer(file)
    	write.writerows(temp)

os.chdir(home)


print("Analysis Script Complete")



