import os
import csv
import time
import argparse
import math
import json


#Variables to create protocol_config.json
#NS3 
use_rlc_um = 1
qout_db = -5
qin_db = -3.9
handover_type = "A3Rsrp"
number_qout_eval_sf = 200
number_qin_eval_sf = 100
t310 = 1000
n310 = 6
n311 = 2
x2_delay_ms = 0
transport_protocol = "TCP"

#BS
numberOfBS = 2
number_of_sectors = 1
#the lengths of the next four variables must be equal to numberOfBS
hysteresis_db = []#[[3],[3]]
a3_offset_db = [[0],[0]]
time_to_trigger_ms = []#[[100],[100]]
location = [[0,0,25],[50,0,25]]

#Variables to create rf_config.json
#UE
numberOfUE = 1
#the lengths of the next three variables must be equal to numberOfUE
initial_position = [[10,0,1.5]]
velocity = [[1,0,0]]
initial_attachment = [1]

#Simulation
mobility_type = "constant_velocity"
resource_blocks = 50
simulation_duration_s = 40

#BS
location = [[0,0,25],[50,0,25]]


hystVals = [.5*x for x in range(21)]
tttVals = [0,40,64,80,100,128,160,256,320,480,512,640,1024,1280,2560,5120]



#other variables
numParamSet = len(hystVals)*len(tttVals)#number of parameter sets, could be calculated but easier to just put it here manually
trials = 1#number of trials for each set of parameters
dirCurrent = os.getcwd()


for i in range(len(hystVals)):
	for j in range(len(tttVals)):
		hystTemp = []
		tttTemp = []
		for k in range(numberOfBS):
			hystTemp.append([hystVals[i]])
			tttTemp.append([tttVals[j]])
		hysteresis_db.append(hystTemp)
		time_to_trigger_ms.append(tttTemp)




#Generating Data
for i in range(numParamSet):
	for j in range(trials):
		#build the jsons
		print("Parameter Set " + str(i+1) + ", Trial" + str(j+1))
		NS3={"use_rlc_um":use_rlc_um,"qout_db":qout_db,"qin_db":qin_db,"handover_type":handover_type,"number_qout_eval_sf":number_qout_eval_sf,"number_qin_eval_sf":number_qin_eval_sf,"t310":t310,"n310":n310,"n311":n311,"x2_delay_ms":x2_delay_ms,"transport_protocol":transport_protocol}
		Simulation={"mobility_type":mobility_type,"resource_blocks":resource_blocks,"simulation_duration_s":simulation_duration_s,"seed":(j+1)}

		BS=[]
		BS2=[]
		for k in range(numberOfBS):
			BS.append({"Name":("BS_"+str(k+1)),"number_of_sectors":number_of_sectors,"hysteresis_db":hysteresis_db[i][k],"a3_offset_db":a3_offset_db[k],"time_to_trigger_ms":time_to_trigger_ms[i][k]})
			BS2.append({"Name":("BS_"+str(k+1)),"location":location[k],"number_of_sectors":number_of_sectors})
		
		UE=[]
		for k in range(numberOfUE):
			UE.append({"name":("UE_"+str(k+1)),"initial_position":initial_position[k],"velocity":velocity[k],"initial_attachment":initial_attachment[k]})
		
		protocolConfig = {"NS3":NS3,"BS":BS}
		rfConfig={"UE":UE,"simulation":Simulation,"BS":BS2}
		protocolConfigJson = json.dumps(protocolConfig, indent=4)
		rfConfigJson = json.dumps(rfConfig, indent=4)
		with open('protocol_config.json','w') as outfile:
			outfile.write(protocolConfigJson)
		with open('rf_config.json','w') as outfile:
			outfile.write(rfConfigJson)
		#call the program correctly
		resultsDir = dirCurrent + "/results/Param_Set_"+str(i+1)+"/trial_"+str(j+1)+"/"
		seed = str(j+1)
		os.system("python3 run.py --runMode no_ML --rngSeedNum " + seed + " --resultsDir " + resultsDir)



#Analyzing Data

for p in range(numParamSet):
	print("Loading Data")
	rsrpRsrqTime = []
	rsrpData = []
	currentServingCell = []
	packetData = []

	for i in range(trials):
		rsrpRsrqTime.append([])
		currentServingCell.append([])
		rsrpData.append([])
		packetData.append([])
		for j in range(numberOfUE):
			rsrpRsrqTime[i].append([])
			currentServingCell[i].append([])
			rsrpData[i].append([])
			packetData[i].append({})
			for k in range(numberOfBS):#initialize the rsrp/rsrq data dicts with numBS*3 values (3 sectors for each BS)
				rsrpData[i][j].append([])


	lineCounter = 0
	servingCellCount = 0
	servingCellSetFlag = 0
	resultsHome = resultsDir = dirCurrent + "/results/"
	for i in range(trials):
		print("     Trial " + str(i+1))
		scenarioFolder = "Param_Set_"+str(p+1)+"/trial_"+str(i+1)+"/"
		rsrpRsrqFilename = "ue-measurements.csv"
		with open(resultsHome+scenarioFolder+rsrpRsrqFilename, newline='') as f:
			reader = csv.reader(f)
			data = list(reader)
		for t in range(len(data))
		for j in range(numberOfUE):
			rsrpRsrqTime[i][j] = 
			for k in range(numberOfBS):
				rsrpData[i][j][k] = 
				currentServingCell[i][j][k]







