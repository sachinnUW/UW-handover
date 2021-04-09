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
parser.add_argument("--rfConfigFileName")
parser.add_argument("--protocolConfigFileName")
args = parser.parse_args()

#print(args.rfConfigFileName)
#print(args.protocolConfigFileName)



if type(args.rfConfigFileName) is str:
    with open(args.rfConfigFileName) as f:
        rfConfig = json.load(f)
else:
    with open("/home/collin/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario 0.8/trial 0/rf_config.json") as f:
        rfConfig = json.load(f)


if type(args.protocolConfigFileName) is str:
    with open(args.protocolConfigFileName) as f:
        protocolConfig = json.load(f)
else:
    with open("/home/collin/Dropbox/FBC_Maveric Academic Collaboration/NS-3_related_files/Simulation_Scenarios/Scenario 0.8/trial 0/protocol_config.json") as f:
        protocolConfig = json.load(f)



#print(rfConfig["BS"][0]["location"])



exp = Experiment(1234, 4096, "MRO", "../..")
#config_params = load_config
model = torch.jit.load("temp_NN.pt")
for i in range(1):
    exp.reset()
    r1 = Ns3AIRL(1357, mlInput, mlOutput)
    pro = exp.run(show_output=True)
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
