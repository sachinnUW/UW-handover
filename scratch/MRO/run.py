from py_interface import *
from ctypes import *
import sys
import ns3_util
import time


class mlInput(Structure):
    _pack_ = 1
    _fields_ = [
        ('x', c_double),
        ('y', c_double),
        ('time', c_double),
        ('imsi', c_int)
    ]


class mlOutput(Structure):
    _pack_ = 1
    _fields_ = [
        ('tttAdjutment', c_double)
    ]

exp = Experiment(1234, 4096, 'MRO', '../..')
for i in range(1):
	exp.reset()
	r1 = Ns3AIRL(1357, mlInput, mlOutput)
	pro = exp.run(show_output=False)
	while not r1.isFinish():
		with r1 as data:
			if data == None:
				break
			data.act.tttAdjutment = data.env.x + data.env.y
			print([data.env.time,data.env.imsi,data.env.x,data.env.y,data.act.tttAdjutment])
	pro.wait()
del exp



