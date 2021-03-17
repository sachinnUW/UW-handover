from py_interface import *
from ctypes import *
import sys
import time

import ns3_util
import torch
import torch.nn as nn


class mlInput(Structure):
    _pack_ = 1
    _fields_ = [("x", c_double), ("y", c_double), ("time", c_double), ("imsi", c_int)]


class mlOutput(Structure):
    _pack_ = 1
    _fields_ = [("tttAdjutment", c_double)]


exp = Experiment(1234, 4096, "MRO", "../..")
model = torch.jit.load("temp_NN.pt")
for i in range(1):
    exp.reset()
    r1 = Ns3AIRL(1357, mlInput, mlOutput)
    pro = exp.run(show_output=True)
    while not r1.isFinish():
        with r1 as data:
            if data == None:
                break
            xPredicted = torch.tensor(
                ([data.env.x, data.env.y, data.env.x, data.env.y]), dtype=torch.float
            )  # 1 X 4 tensor
            xPredicted_max, _ = torch.max(xPredicted, 0)
            xPredicted = torch.div(xPredicted, xPredicted_max)
            data.act.tttAdjutment = model.forward(xPredicted)
            # data.act.tttAdjutment = ML_model(data.env.x,data.env.y)
            print(
                [
                    data.env.time,
                    data.env.imsi,
                    data.env.x,
                    data.env.y,
                    data.act.tttAdjutment,
                ]
            )
    pro.wait()
del exp
