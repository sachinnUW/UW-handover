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

scenario = "Scenario" + sys.argv[1]
HystVal = float(sys.argv[2])
TTT = float(sys.argv[3])
trials = int(sys.argv[4])

#find some parameters via the config file
print("Determining Configuration Parameters")
configData = {}
with open("/home/collin/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario 0.3.1/simulation_config.txt") as config:
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


#load in the files, two of relevance, 'lte-tcp-x2-handover.ue-measurements.dat' and 'lte-tcp-x2-handover.tcp-receive.dat' into memory

#creating the variables
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
resultsHome = "/home/collin/workspace/ns-3-dev-git/results/"
for i in range(trials):
	print("     Trial " + str(i+1))
	#first load the RSRP/RSRQ measurements
	scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
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


#we are going to insert 0s into the packet data for subframes where no packets arrived.
#We are doing this because otherwise the throughput analysis takes prohibatiely long

for i in range(trials):
    for j in range(numUE):
        for k in range(int(1000*max([float(x) for x in packetData[i][j].keys()]))+1):
            if float(k)/1000 not in packetData[i][j]:
                packetData[i][j][str(float(k)/1000)] = 0


#write the event report
#what we want to do it create a sort of event report which records the following events(for now):
#A3 events: when another cell has a higher RSRP than the current serving cell by HystVal (RSRP(otherCell) > RSRP(servingCell) + HystVal). Another A3 event
#	will not be logged until the RSRP has dropped below the threshold handover has been finished. source: TS 36.839
#RLF events: when the CQI of the current cell is less than Qout for T310 (a timer). Although there isn't currently a CQI trace output by NS-3 (there could be)
# 	RLF events will show up in the currentServingCell variable when it's value drops to 0. source: TS 36.839
#Handover Completion Events: after the A3 event has been true for TTT milliseconds handover will be triggered. at the end of this process the currentServingCell
#	Will change to the cell which triggered the A3 event source: TS 36.839
#Too-Late Handover Failure: Too-late handovers occur when the eNb waits to long to trigger handover results in an RLF after an A3 event. Specifically, if an RLF 
#	event occurs within TTT of an A3 event then that is considered a too-late handover. Generally following a too-late handover the UE will connect to a new cell
#	(likely the one which triggered the A3 event) but this is not gaurenteed. This definition follows from TS 36.839. TS 36.839 does not differentiate between
#	too-early and too-late but their definition of handover failure is similar to academic definitions of too-late handover failure.
#Too-Early Handover Failure: Too-early handovers occur when handover is triggered before it should be and results in an RLF immediately after a successful handover.
#	specifically, if an RLF event occurs within TTT of a successful handover then that is considered a too-early handover. Generally after the RLF the UE will
#	reconnect to the original cell (the one it was connected to before the handover) but this is not gaurenteed. This definition is related to the one found in 
#	TS 36.839, essentially serving as a recipracol to the definition of too-late handover found therein
#Ping-Pong Events: Ping Pong events are defined as a sequence of successful handovers which happen in quick succession between two cells. Specifically, if a UE is
#	in cell A, then hands-over to cell B, then back to cell A in less than MTS (minimum time of stay) seconds a ping pong is considered to have occured. the 
#	recomended value for MTS is 1 second. source: TS 36.839 (this source has a very detailed description of ping-pong and a good description of how to count them).

#Note: I (Collin Brady) am somewhat suspicious of the specific definitions for too-early/late handover in the sense that I think TTT might be the wrong timer. 
#Because we use TTT as the timer for handover failure but the RLF uses T310 and by default T310 > TTT (default T310 is 1 seconds, vs .256 s for TTT) I; 
#1) dont thing that too-early handover failures can even occur (handover resets the T310 timer) and 2) think that the too-late handovers might end up 
#underestimating things (the RLF has to start being logged well before the A3 event). On top of that because we are discussing using ML to vary TTT we 
#may end up in a situation where if you set TTT very low we can never detect any handover failures. In the future I think it may be better to use identical 
#definitions as above with TTT swapped out for T310 for the too-early handover failure and change the conditions of too-late handover to: if a cell change 
#occurs within T310 of an RLF then that was a too-late handover failure.


nLate = 0 #counter for too late handover failures
nEarly = 0 #counter for too early handover failures
nPingPong = 0 #counter for ping-pong events
nRLF = 0 #counter for RLF events
nHandover = 0 #counter for handovers/cell changes (the cell can change because of a reconection after an RLF, this is considered a handover for analysis purposes)
nA3 = 0 #counter for A3 events
T310 = 1 
TMTS = 1 #minimum stay time, for ping pong detection

for i in range(trials):
	for j in range(len(rsrpRsrqTime[i])):
















#from here we will do some smoothing on the recieve packet data to get data rate. Packet arrivals are binned together based upon the variable
#binWidth, the data rate at the center of each bin is equal to the number of packets which arrive in that bin divided by binWidth. increasing binWidth
#acts to smooth the data rate. an actual moving average filter can't be used because the packet arrivals arent uniformly sampled. another potential
#technique would be to force uniform sampling by inserting 0 every millisecond which doesnt have a packet arrival then using a moving average filter.
#such a technique would result in a data rate trace with more data rate points but the same issues with oversmoothing present in the binning method.
#the binning method used here is approximately identical a downsampled version of the moving average method described above.
print("Finding Data Rate")
dataRate = []
dataRateTime = []


for i in range(trials):
	dataRate.append([])
	dataRateTime.append([])
	for j in range(numUE):
		dataRate[i].append([])
		dataRateTime[i].append([])



binWidth = 20;#number of points to average over


for i in range(trials):
	for j in range(numUE):
		print("     Trial " + str(i+1) + ", UE " + str(j+1))
		packetTime = [float(x) for x in packetData[i][j].keys()]
		#temp = list(range(int(1000*(packetTime[0]+binWidth/2)),int(1000*(packetTime[-1]-binWidth/2)),int(1000*binWidth)))#converted to integers for range
		dataRateTime[i][j] = [float(i)/1000 for i in range(int(1000*max(packetTime))+1)]#converted back to floats
		recievedBytes = list(packetData[i][j].values())
		for k in range(len(dataRateTime[i][j])):
			if k < binWidth-1:
				dataRate[i][j].append(sum([recievedBytes[x]/binWidth for x in range(k)]))
			else:
				dataRate[i][j].append(sum([recievedBytes[x]/binWidth for x in range(k-binWidth+1,k)]))








#first find the averaged values (only do this if there is more than 1 trial)
if trials > 1:
	print("Finding Averages of Performance Indicators")

	averageDataRateTime = []
	averageDataRate = []
	dataRateConfidenceInterval = []
	for i in range(len(dataRateTime[0])):
		#first is data rate
		#grab the ith value 
		#this is a sloppy way of doing things but will work for a first draft, it presumes that the packet arrivals begin and end at the same
		#time for all files, which isnt nescesarily the case
		tempTime = [x[i] for x in dataRateTime]
		tempData = [x[i] for x in dataRate]
		averageDataRateTime.append(sum(tempTime)/len(tempTime))
		averageDataRate.append(sum(tempData)/len(tempData))
		tempDataArray = 1.0 * np.array(tempData)
		std = scipy.stats.sem(tempDataArray)
		CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
		dataRateConfidenceInterval.append(CI)


	averageRsrpRsrqTime = []
	averageRsrp = []
	averageRsrq = []
	rsrpConfidenceInterval = []
	rsrqConfidenceInterval = []

	for i in range(numBS):
		averageRsrp.append([])
		averageRsrq.append([])
		rsrpConfidenceInterval.append([])
		rsrqConfidenceInterval.append([])
		for j in range(3):
			averageRsrp[i].append([])
			averageRsrq[i].append([])
			rsrpConfidenceInterval[i].append([])
			rsrqConfidenceInterval[i].append([])





	for i in range(len(rsrpRsrqTime[0])):
		#next RSRP/RSRQ/CellID, this has to be done in a separate for loop as the lengths are different
		#this is less sloppy than for the data rate, the timestamps for all RSRP/RSRQ/CellID measurements should be identical
		tempTime = [x[i] for x in rsrpRsrqTime]
		averageRsrpRsrqTime.append(sum(tempTime)/len(tempTime))

		for j in range(numBS):
			for k in range(3):
				tempRSRP = [x[j][k][i] for x in rsrpData]
				tempRSRQ = [x[j][k][i] for x in rsrqData]

				averageRsrp[j][k].append(sum(tempRSRP)/len(tempRSRP))
				averageRsrq[j][k].append(sum(tempRSRQ)/len(tempRSRQ))
				
				tempRsrpArray = 1.0 * np.array(tempRSRP)
				std = scipy.stats.sem(tempRsrpArray)
				CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
				rsrpConfidenceInterval[j][k].append(CI)

				tempRsrqArray = 1.0 * np.array(tempRSRQ)
				std = scipy.stats.sem(tempRsrqArray)
				CI = std * scipy.stats.t.ppf((1 + .95)/2.,trials-1)
				rsrqConfidenceInterval[j][k].append(CI)
































# currently commented out, dont want to use it
if False:'''
	#start with writing the files for each trial
	home = os.getcwd()

	for i in range(trials):
		scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "/" + scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT)) + "-" + str(i+1) + "/"
		os.chdir(resultsHome + scenarioFolder)
		#data rate
		temp = [dataRateTime[i],dataRate[i]]
		file = open('dataRate,UE' + str(1) + ',binWidth' + str(binWidth) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
		with file:
			write = csv.writer(file)
			write.writerows(temp)


		#RSRP over time
		temp = [rsrpRsrqTime[i]]
		for j in range(numBS):
			for k in range(3):
				temp.append(rsrpData[i][j][k])
		file = open('RSRP,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
		with file:
			write = csv.writer(file)
			write.writerows(temp)


		#RSRQ over time
		temp = [rsrpRsrqTime[i]]
		for j in range(numBS):
			for k in range(3):
				temp.append(rsrqData[i][j][k])
		file = open('RSRQ,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
		with file:
			write = csv.writer(file)
			write.writerows(temp)


		#cellID
		temp = [rsrpRsrqTime[i],currentServingCell]
		file = open('currentServingCell,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
		with file:
			write = csv.writer(file)
			write.writerows(temp)

	#now write the averages
	scenarioFolder = scenario + "-" + str(int(HystVal)) + "-" + str(int(TTT))
	os.chdir(resultsHome + scenarioFolder)
	#data rate
	temp = [averageDataRateTime,averageDataRate,dataRateConfidenceInterval]
	file = open('AveragedataRate,UE' + str(1) + ',binWidth' + str(binWidth) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)


	#RSRP over time
	temp = [averageRsrpRsrqTime]
	for j in range(numBS):
		for k in range(3):
			temp.append(averageRsrp[j][k])
			temp.append(rsrpConfidenceInterval[j][k])
	file = open('AverageRSRP,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)


	#RSRQ over time
	temp = [averageRsrpRsrqTime]
	for j in range(numBS):
		for k in range(3):
			temp.append(averageRsrq[j][k])
			temp.append(rsrqConfidenceInterval[j][k])
	file = open('AverageRSRQ,UE' + str(1) + '.csv', 'w+', newline ='') #the UE ID will need to be fixed in the future
	with file:
		write = csv.writer(file)
		write.writerows(temp)
	os.chdir(home)'''









#plt.plot(rsrpRsrqTime[0],rsrpData[0][0][0],label="eNb1,sector1")
#plt.plot(rsrpRsrqTime[0],rsrpData[0][0][1],label="eNb1,sector2")
#plt.plot(rsrpRsrqTime[0],rsrpData[0][0][2],label="eNb1,sector3")
#plt.plot(rsrpRsrqTime[0],rsrpData[0][1][0],label="eNb2,sector1")
#plt.plot(rsrpRsrqTime[0],rsrpData[0][1][1],label="eNb2,sector2")
#plt.plot(rsrpRsrqTime[0],rsrpData[0][1][2],label="eNb2,sector3")
#plt.plot(averageRsrpRsrqTime,averageRsrp[0][0],label="average")




#tempTime = [sum(x)/2 for x in zip(dataRateTime[0],dataRateTime[1])]
#tempData = [sum(x)/2 for x in zip(dataRate[0],dataRate[1])]
#plt.plot(dataRateTime[0],dataRate[0],label="trial1")
#plt.plot(dataRateTime[1],dataRate[1],label="trial2")
#plt.plot(averageDataRateTime,averageDataRate,label="average")

#plt.plot(averageDataRateTime,dataRateConfidenceInterval,label="CI")
#plt.legend()
#plt.show()
#










