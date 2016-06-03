#!/usr/bin/python2.7
from ev3dev.auto import *
import time

'''
come-to-robotics

WHY IS INFRARED BEING LIKE THIS??? Check this, possibly rebuild grabber (not spinner). It detects 7 everwhere within a few centimetres of the sensor, thus causing it to turn sharply and have a hard time catching the ball on ONE SIDE (on the other side, this actually helps it to turn in). Also, we should give a delay to spinning (that is, wait for a few zeroes before spinning).

IDEA: Okay, run ir.driver_name, and refer to that documentation. Or if all goes south, pull out the dark magic. Seriously, there's some crazy stuff for directly reading the sensor's registers. (See http://www.ev3dev.org/docs/sensors/using-i2c-sensors/, the bit about addressing and the sensor's manual/datasheet).

Notes: Use it in AC-ALL mode. When values hit > 110, discount sensor and charge forwards until no longer the case.

TODO:
> Write getIR(), which returns the direction it thinks it's going to UNLESS max(irValues) > 110, then just go forwards. BETTER IDEA: GET A BETTER IR SENSOR.
> Import the colour sensor, get it to fire retreat() when it gets white, if it's got the ball, or spin if you don't have the ball and that's the case. THIS KIND OF WORKS!
> Collisions.
'''

ir = Sensor('in1:i2c8') # It's an old sensor, so it needs i2c8
gyro = GyroSensor('in2')
steer = [LargeMotor('outA'),LargeMotor('outB')]
hold = LargeMotor('outD')
ultra = UltrasonicSensor('in3')
co = ColorSensor('in4')

'''
Cool Things we Could Add:
> Bluetooth - "I've got the ball, don't go for it." (Seb Towers 2016)
'''

STORAGE_LENGTH = 15 # No of values in the mean
TURNINESS = 150 # Sharpness of turn
HOLD_SR_LEN = 20 # Length of shift register for holding
CLOSENESS_THRESHOLD = 100 # (in mm) Distance before going "that's too close"
SPINNING_SPEED = 50 # Speed that it spins at.
WHITENESS_THRESHOLD = 750

'''
Useful Functions
'''

def mean(t):
	return float(sum(t))/len(t)

def move(angle, direction=1):
	# Turn with a sharpness of TURNINESS (+TURNINESS => +angle)
	if angle > 0:
		ls = 100 - TURNINESS*angle
		rs = 100
	elif angle < 0:
		ls = 100
		rs = 100 + TURNINESS*angle # Finnbar, angle will be less than zero so this is legit code. Don't worry yourself!
	else:
		ls = 100
		rs = 100
	steer[0].run_forever(duty_cycle_sp=int(ls)*direction)
	steer[1].run_forever(duty_cycle_sp=int(rs)*direction)

def spin(direction):
	steer[0].run_forever(duty_cycle_sp=SPINNING_SPEED*direction)
	steer[1].run_forever(duty_cycle_sp=-SPINNING_SPEED*direction)

def stop():
	steer[0].stop()
	steer[1].stop()

def getGyro():
	# gyroValue takes values of -180 to +180, as you'd expect.
	return ((gyro.value() + 180) % 360) - 180

def resetGyro():
	gyro.mode = "GYRO-RATE"
	gyro.mode = "GYRO-ANG"

def getIR():
	v = ir.value(0)
	if v == 7:
		return 6
	else:
		return v

def isWhite():
	return sum([co.value(i) for i in range(3)]) > WHITENESS_THRESHOLD

def hasBall(ro):
	ro.holdValues[ro.holdPointer] = hold.speed
	ro.holdPointer += 1
	if ro.holdPointer >= HOLD_SR_LEN:
		ro.holdPointer = 0
	if mean(ro.holdValues) <= ro.holdThreshold:
		return ro, True
	else:
		return ro, False

def collision(ro):
	pass

'''
States
'''

def moveToGoal(ro):
	# Move forwards in a straight line, but if you're >45d out, spin back (realign). Check throughout whether retreat should be called.
	while True:
		move(0)
		ro, gotBall = hasBall(ro)
		if not gotBall:
			return "lookForBall", ro
		if abs(getGyro()) > 45:
			return "realign", ro
		ul = ultra.value()
		if ul < CLOSENESS_THRESHOLD:
			return "shoot", ro
		if isWhite():
			return "retreat", ro

def retreat(ro):
	# We hit "the wall", reverse slightly, turn 90d, move forwards a bit (this is blocking). Then go to realign.
	move(0,-1)
	time.sleep(0.5)
	while abs(getGyro()) < 90:
		spin(1)
	move(1)
	for i in range(20):
		time.sleep(0.075)
		if isWhite():
			return "retreat", ro
	return "realign", ro

def shoot(ro):
	# Fire all motors forwards! Gotta go fast. On losing the ball, swap to findBall.
	move(0)
	hold.run_forever(duty_cycle_sp=-100)
	time.sleep(0.5)
	return "lookForBall", ro

def lookForBall(ro):
	# If ball's in sight, go get it, else spin. On finding it, realign.
	# NOTE: ADD OBJECT DETECTION
	while True:
		ro, gotBall = hasBall(ro)
		irValue = getIR()
		if irValue != 0 and not isWhite():
			ro.irValues[ro.irPointer] = irValue
			ro.irPointer += 1
			if ro.irPointer >= STORAGE_LENGTH:
				ro.irPointer = 0
			angle = (irValue-5)*0.25
			move(angle)
		elif isWhite():
			print "Saw line."
			# Back away a bit, then spin.
			move(0,-1)
			time.sleep(0.75)
			spin(1)
			time.sleep(0.75)
		else:
			if mean(ro.irValues) > 5:
				move(1)
			else:
				move(-1)
		hold.run_forever(duty_cycle_sp=50)
		# Check if it's found:
		if gotBall:
			return "realign", ro

def realign(ro):
	# If angle is far off, rotate until not the case.
	while True:
		gyroValue = getGyro()
		ro, gotBall = hasBall(ro)
		if not gotBall:
			return "lookForBall", ro
		if abs(gyroValue) < 5:
			return "moveToGoal", ro
		else:
			spin(-gyroValue/abs(gyroValue))

def reset(ro):
	# Reset the robot as it's been picked up.
	resetGyro()
	return "lookForBall", ro

class RobotObject():
	def __init__(self):
		self.irValues = [5] * STORAGE_LENGTH
		self.irPointer = 0
		self.holdThreshold = 0
		self.holdValues = [1000] * HOLD_SR_LEN
		self.holdPointer = 0

if __name__ == '__main__':
	functions = {"moveToGoal": moveToGoal, "retreat": retreat, "shoot": shoot, "lookForBall": lookForBall, "realign": realign}
	ro = RobotObject()
	ir.mode = "AC-ALL"
	co.mode = "RGB-RAW"
	state = "lookForBall"
	print "GO!"
	holdingSr=[] # This is our general shift register, I'll explain later.
	assert steer[0].connected and steer[1].connected and hold.connected # Basic assert, just in case
	hold.run_forever(duty_cycle_sp=50) # This is our dribbler motor
	hThreshold = 0
	resetGyro()
	time.sleep(1)
	for _ in range(HOLD_SR_LEN): # Check the dribbler speed to work out when the ball is in the way
		holdingSr.append(hold.speed)
	hThreshold = sum(holdingSr)/(HOLD_SR_LEN + 1.0)
	ro.holdThreshold = hThreshold
	while True:
		print state
		state,ro = functions[state](ro)
