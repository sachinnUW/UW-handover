from py_interface import *
from ctypes import *
import sys
import time
import argparse
import math
import random
import ns3_util
import torch
import torch.nn as nn
import json
import os
import csv
from itertools import zip_longest
import numpy as np
from DQN import *

#def load_config(input_file)->Dict[str,Any]:
#    try:
#        with open(input_file,"r") as read_file:
#            config_params = json.load(read_file)
##        return config_params
#    except Exception:
#        logging.error(f"{input_file} doesn't exist")
#        return None
seed = 2
torch.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

class mlInput(Structure):
    _pack_ = 1
    _fields_ = [("x", c_double), ("y", c_double), ("time", c_double), ("imsi", c_int), ("cellId", c_int), ("packetSize",c_double), ("packetReceiverId",c_int), ("rsrp",c_double), ("packetRxFlag",c_int), ("hoInProgress",c_int), ("hoEnded",c_int)]


class mlOutput(Structure):
    _pack_ = 1
    _fields_ = [("tttAdjustment", c_double)]


parser = argparse.ArgumentParser()
parser.add_argument("--resultsDir")
parser.add_argument("--rfConfigFileName")
parser.add_argument("--protocolConfigFileName")
#parser.add_argument("--mroExp")
parser.add_argument("--runMode",help='select the mode to run the simulation, valid options are DQN, MRO, and no_ML')
#parser.add_argument('--pure_online', action='store_true',help='whether use rl algorithm')


args = parser.parse_args()
dirCurrent = os.getcwd()
print(dirCurrent)
#parsing inputs and assigning default values if none were input. all defaults are the local filepaths on Collin Brady's computer, unlikely they will work you you.
if type(args.resultsDir) is str:
    resultsDir = args.resultsDir
else:
    resultsDir = dirCurrent + "/results/"

if type(args.rfConfigFileName) is str:
    rfConfigFileName = args.rfConfigFileName
else:
    rfConfigFileName = dirCurrent + "/rf_config.json"

if type(args.protocolConfigFileName) is str:
    protocolConfigFileName = args.protocolConfigFileName
else:
    protocolConfigFileName = dirCurrent + "/protocol_config.json"


# if type(args.rngSeedNum) is str:
#     rngSeedNum = int(args.rngSeedNum)
# else:
#     rngSeedNum = 1

#if type(args.mroExp) is str:
#    mroExp = bool(args.mroExp)
#else:
#    mroExp = True

if type(args.runMode) is str:
    runMode = args.runMode
else:
    runMode = "no_ML"

with open(rfConfigFileName) as f:
    rfConfig = json.load(f)

if runMode == "DQN":
    loss_val = []
    #action_space = [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640, 1024, 1280]
    action_space = [0, 40, 64, 80, 100, 128, 160, 256, 320, 480]
    
    all_dqn = {}
    # not_first_trail = 0
    # state = []
    # state_ = []
    # reward = 0
    # count = 0
    # action_index = 0
    # action = 0
    
    mroExp=True
elif runMode == "MRO":
    mroExp=True
elif runMode == "no_ML":
    mroExp=False
else:
    print("runMode not set correctly, valid options are DQN, MRO, and no_ML")
    exit()
print("Running with: " + runMode)
#print(len(rfConfig["UE"]))

#parameters for throughput calculation
recievedPacketRecord = []
throughputRecord = []
each_act = []
for i in range(rfConfig["simulation"]["number_of_UE"]*2):
    recievedPacketRecord.append([])
    throughputRecord.append([])
    each_act.append([])

binWidth = .01 #s, the width of the throughput calculation bin, moving average

print ("starting")
ns3Settings = {'resultDir' : resultsDir, 'rfConfigFileName' : rfConfigFileName, 'protocolConfigFileName' : protocolConfigFileName, 'mroExp' : mroExp}
exp = Experiment(1234, 4096, "UW-working", "../..")
model = torch.jit.load("temp_NN.pt")
exp.reset()
r1 = Ns3AIRL(1357, mlInput, mlOutput)
pro = exp.run(setting=ns3Settings, show_output=True)
print ("Starting ns-3 simulation")
T = 5
x_arr = np.zeros(T)
y_arr = np.zeros(T)

while not r1.isFinish():
    with r1 as data:
        if data == None:
            break
        if runMode == "DQN":
            imsi = data.env.imsi
            if imsi not in all_dqn:
                dqn = DQN(state_size=4, n_actions = len(action_space),loss_val=loss_val, batch_size=1)
                all_dqn[imsi] = dqn
            else:
                dqn = all_dqn[imsi]

            x = data.env.x
            y = data.env.y
            x_arr = np.roll(x_arr, 1)
            x_arr[0] = x
            y_arr = np.roll(y_arr, 1)
            y_arr[0] = y

            if dqn.not_first_trail:
                x = data.env.x
                y = data.env.y
                pkt_size = 536#data.env.packetSize#this value is hardcoded due to an oddity in the way tcp works in ns3, multiple duplicate packets can be recieved at once, giving the appearence of a larger reception. This data is however useless to the application layer.
                rsrp = data.env.rsrp
                # reward = 0
                dqn.state_ = np.array([x, y, pkt_size, rsrp])                
                dqn.store_transition(dqn.state, dqn.action_index, dqn.reward, dqn.state_)
                dqn.count += 1
            
            # print("Run with DQN")
            x = data.env.x
            y = data.env.y
            pkt_size = 536#data.env.packetSize#this value is hardcoded due to an oddity in the way tcp works in ns3, multiple duplicate packets can be recieved at once, giving the appearence of a larger reception. This data is however useless to the application layer.
            rsrp = data.env.rsrp
            dqn.state = np.array([x, y, pkt_size, rsrp])
            dqn.action_index = dqn.choose_action(dqn.state)
            action = action_space[dqn.action_index]
            

            #print(data.env.imsi,action)
            data.act.tttAdjustment = 256
            dqn.not_first_trail = 1

            #print(data.env.packetRxFlag)
            if data.env.packetRxFlag == 1:
                #print("banana")
                recievedPacketRecord[2*(data.env.packetReceiverId-1)].append(round(data.env.time,3))
                recievedPacketRecord[2*(data.env.packetReceiverId-1)+1].append(536)#(data.env.packetSize)#this value is hardcoded due to an oddity in the way tcp works in ns3, multiple duplicate packets can be recieved at once, giving the appearence of a larger reception. This data is however useless to the application layer.
                throughputRecord[2*(data.env.packetReceiverId-1)].append(round(data.env.time,3))
                dataReceived = 0
                for i in range(len(recievedPacketRecord[2*(data.env.packetReceiverId-1)]) - 1, -1, -1):
                    #print(i)
                    if recievedPacketRecord[2*(data.env.packetReceiverId-1)][i] >= round(data.env.time,3) - binWidth:
                        dataReceived = dataReceived + recievedPacketRecord[2*(data.env.packetReceiverId-1)+1][i]
                    else:#if this happens then we are outside of the averaging window, stop calculation
                        break
                throughputRecord[2*(data.env.packetReceiverId-1)+1].append(dataReceived/binWidth)
                data.env.packetRxFlag = 0
                dqn.reward = dataReceived/binWidth
                each_act[2*(data.env.packetReceiverId-1)].append(round(data.env.time,3))
                each_act[2*(data.env.packetReceiverId-1)+1].append(action)
            if data.env.hoEnded == 1:
                 dqn.learn()
                 data.env.hoEnded = 0
        elif runMode == "MRO":
            relativeDistanceX = abs(data.env.x - rfConfig["BS"][math.floor((data.env.cellId-1))]["location"][0])
            #print(relativeDistanceX)
            relativeDistanceY = abs(data.env.y - rfConfig["BS"][math.floor((data.env.cellId-1))]["location"][1])
            #print(relativeDistanceY)
            xPredicted = torch.tensor(
                ([data.env.x, data.env.y, data.env.x, data.env.y]), dtype=torch.float
            )  # 1 X 4 tensor
            xPredicted_max, _ = torch.max(xPredicted, 0)
            xPredicted = torch.div(xPredicted, xPredicted_max)
            data.act.tttAdjustment = model.forward(xPredicted).numpy()[0].item()
        else:
            pass
        #.numpy() converts to a numpy array
        #[0] grabs the first (only) value, at this point its type is numpy.float32
        #.item() converts it to a regular old float
        #print(
        #    [
        #        data.env.time,
        #        data.env.imsi,
        #        data.env.x,
        #        data.env.y,
        #        data.act.tttAdjutment,
        #    ]
        #)
pro.wait()
del exp
if runMode == "DQN":
    dqn.save_model('dqn.pt')
#print(recievedPacketRecord[0])
export_data = zip_longest(*recievedPacketRecord, fillvalue = '')#converts the rows into columns for nicer data formatting
file = open(resultsDir + 'packetRecieveTest.csv', 'w', newline='')
with file:
    write = csv.writer(file)
    write.writerow(['time','bytesRx'])
    write.writerows(export_data)


export_data = zip_longest(*throughputRecord, fillvalue = '')#converts the rows into columns for nicer data formatting
file = open(resultsDir + 'throughputTest.csv', 'w', newline='')
with file:
    write = csv.writer(file)
    write.writerow(['time','throughput'])
    write.writerows(export_data)


export_data = zip_longest(*each_act, fillvalue = '')#converts the rows into columns for nicer data formatting
file = open(resultsDir + 'actions.csv', 'w', newline='')
with file:
    write = csv.writer(file)
    write.writerow(['time','action'])
    write.writerows(export_data)
