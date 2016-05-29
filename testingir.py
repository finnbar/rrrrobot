from ev3dev.auto import *

ir = Sensor("in1:i2c8")

def r():
	if ir.mode == 'DC' or ir.mode == 'AC':
		return "Direction: {}".format(ir.value())
	elif ir.mode == 'AC-ALL':
		return "Direction: {i[0]}, Channels: {i[1]} {i[2]} {i[3]} {i[4]} {i[5]}".format(i=[ir.value(i) for i in range(6)])
	else:
		return "Direction: {i[0]}, Channels: {i[1]} {i[2]} {i[3]} {i[4]} {i[5]}, Sensor Mean: {i[6]}".format(i=[ir.value(i) for i in range(7)])

def setMode(m):
	ir.mode = m

def getMode():
	return ir.mode