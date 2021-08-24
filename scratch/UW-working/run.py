from py_interface import *
from ctypes import *
import sys
import time
import argparse
import math
import ns3_util
import torch
import torch.nn as nn
import json
import os


#def load_config(input_file)->Dict[str,Any]:
#    try:
#        with open(input_file,"r") as read_file:
#            config_params = json.load(read_file)
##        return config_params
#    except Exception:
#        logging.error(f"{input_file} doesn't exist")
#        return None



class mlInput(Structure):
    _pack_ = 1
    _fields_ = [("x", c_double), ("y", c_double), ("time", c_double), ("imsi", c_int), ("cellId", c_int)]


class mlOutput(Structure):
    _pack_ = 1
    _fields_ = [("tttAdjutment", c_double)]


parser = argparse.ArgumentParser()
parser.add_argument("--resultsDir")
parser.add_argument("--rfConfigFileName")
parser.add_argument("--protocolConfigFileName")
parser.add_argument("--rngSeedNum")
parser.add_argument("--mroExp")
args = parser.parse_args()
dirCurrent = os.getcwd()
print(dirCurrent)
#parsing inputs and assigning default values if none were input. all defaults are the local filepaths on Collin Brady's computer, unlikely they will work you you.
if type(args.resultsDir) is str:
    resultsDir = args.resultsDir
else:
    resultsDir = dirCurrent + "/results"

if type(args.rfConfigFileName) is str:
    rfConfigFileName = args.rfConfigFileName
else:
    rfConfigFileName = dirCurrent + "/rf_config.json"

if type(args.protocolConfigFileName) is str:
    protocolConfigFileName = args.protocolConfigFileName
else:
    protocolConfigFileName = dirCurrent + "/protocol_config.json"


if type(args.rngSeedNum) is str:
    rngSeedNum = int(args.rngSeedNum)
else:
    rngSeedNum = 1

if type(args.mroExp) is str:
    mroExp = bool(args.mroExp)
else:
    mroExp = True

with open(rfConfigFileName) as f:
    rfConfig = json.load(f)

print ("starting")
ns3Settings = {'resultDir' : resultsDir, 'rfConfigFileName' : rfConfigFileName, 'protocolConfigFileName' : protocolConfigFileName, 'rngSeedNum' : rngSeedNum,'mroExp' : mroExp}
exp = Experiment(1234, 4096, "UW-working", "../..")
model = torch.jit.load("temp_NN.pt")
for i in range(1):
    exp.reset()
    r1 = Ns3AIRL(1357, mlInput, mlOutput)
    pro = exp.run(setting=ns3Settings, show_output=True)
    print ("starting")
    while not r1.isFinish():
        with r1 as data:
            if data == None:
                break
            relativeDistanceX = abs(data.env.x - rfConfig["BS"][math.floor((data.env.cellId-1)/3)]["location"][0])
            #print(relativeDistanceX)
            relativeDistanceY = abs(data.env.y - rfConfig["BS"][math.floor((data.env.cellId-1)/3)]["location"][1])
            #print(relativeDistanceY)
            xPredicted = torch.tensor(
                ([data.env.x, data.env.y, data.env.x, data.env.y]), dtype=torch.float
            )  # 1 X 4 tensor
            xPredicted_max, _ = torch.max(xPredicted, 0)
            xPredicted = torch.div(xPredicted, xPredicted_max)
            data.act.tttAdjutment = model.forward(xPredicted).numpy()[0].item()
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
