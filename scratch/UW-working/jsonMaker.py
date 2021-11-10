import csv
import os

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
field_edges = [0,1000,0,1000]#the bounds of this should be an integer multiple of inter_BS_distance
number_of_UE = 1
inter_BS_distance = 500
average_UE_speed = 200
UE_speed_bound = 50





#BS
#numberOfBS = 2
number_of_sectors = 1
#the lengths of the next four variables must be equal to numberOfBS
hysteresis_db = []#[[3],[3]]
a3_offset_db = []#[[0],[0]]
time_to_trigger_ms = []#[[100],[100]]
location = []#[[0,0,25],[50,0,25]]

x = 0
y = 0
while x < field_edges[1] or y < field_edges[3]:
	location.append([x,y,25])
	hysteresis_db.append([3])
	a3_offset_db.append([0])
	time_to_trigger_ms.append([256])
	if x >= field_edges[1]:
		y = y + math.sqrt(3)*inter_BS_distance/2
		x = x - field_edges[1] - inter_BS_distance/2
	else:
		x = x + inter_BS_distance
	if not(x < field_edges[1] or y < field_edges[3]):
		location.append([x,y,25])
		hysteresis_db.append([3])
		a3_offset_db.append([0])
		time_to_trigger_ms.append([256])

numberOfBS = len(a3_offset_db)




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
#location = [[0,0,25],[50,0,25]]


hystVals = 3
tttVals = 256#[0,40,64,80,100,128,160,256,320,480,512,640,1024,1280,2560,5120]





NS3={"use_rlc_um":use_rlc_um,"qout_db":qout_db,"qin_db":qin_db,"handover_type":handover_type,"number_qout_eval_sf":number_qout_eval_sf,"number_qin_eval_sf":number_qin_eval_sf,"t310":t310,"n310":n310,"n311":n311,"x2_delay_ms":x2_delay_ms,"transport_protocol":transport_protocol}
Simulation={"mobility_type":mobility_type,"resource_blocks":resource_blocks,"simulation_duration_s":simulation_duration_s,"seed":1,"field_edges":field_edges,"number_of_UE":number_of_UE,"inter_BS_distance":inter_BS_distance,"average_UE_speed":average_UE_speed,"UE_speed_bound":UE_speed_bound}

BS=[]
BS2=[]
for k in range(numberOfBS):
	BS.append({"Name":("BS_"+str(k+1)),"number_of_sectors":number_of_sectors,"hysteresis_db":hysteresis_db[k],"a3_offset_db":a3_offset_db[k],"time_to_trigger_ms":time_to_trigger_ms[k]})
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









