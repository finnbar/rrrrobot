from ev3dev.auto import *

ir = Sensor("in1:i2c8")

def mean(t):
	return float(sum(t))/len(t)

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

def averagingDirection():
	registerLength = 20
	ir.mode = 'AC-ALL'
	channels = [[0 for i in range(5)] for j in range(registerLength)]
	pointer = 0
	while True:
		for i in range(5):
			channels[pointer][i] = ir.value(i+1)
		largest = 0
		averaged = [mean([channels[i][j] for i in range(registerLength)]) for j in range(5)]
		print averaged
		m = max(averaged)
		for i in range(5):
			if averaged[i] == m:
				print "Direction: " + str([1,3,5,7,9][i])
		pointer += 1
		if pointer >= registerLength:
			pointer = 0