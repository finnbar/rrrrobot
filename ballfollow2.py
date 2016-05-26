#!/usr/bin/python2.7
import atexit
from ev3dev.auto import *
import time

ir = Sensor('in1:i2c8') # It's an old sensor, so it needs i2c8
gyro = GyroSensor('in2')
steer = [LargeMotor('outA'),LargeMotor('outB')]
hold = LargeMotor('outD')
ultra = UltrasonicSensor('in3')

'''
Cool Things we Could Add:
> Bluetooth - "I've got the ball, don't go for it." (Seb Towers 2016)
'''

STORAGE_LENGTH = 15 # No of values in the mean
TURNINESS = 150 # Sharpness of turn
HOLD_SR_LEN = 20 # Length of shift register for holding
CLOSENESS_THRESHOLD = 10 # (in cm) Distance before going "that's too close"
SPINNING_SPEED = 50 # Speed that it spins at.

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


def getGyro():
	# gyroValue takes values of -180 to +180, as you'd expect.
	return ((gyro.value() + 180) % 360) - 180
	
def resetGyro():
	gyro.mode = "GYRO-RATE"
	gyro.mode = "GYRO-ANG"

def collision(ro):
	pass

'''
States
'''

def moveToGoal(ro):
	# Move forwards in a straight line, but if you're >45d out, spin back (realign). Check throughout whether retreat should be called.
	while True:
		move(0)
		if abs(getGyro) > 45:
			return "realign", ro

def retreat(ro):
	# We hit "the wall", reverse slightly, turn 90d, move forwards a bit (this is blocking). Then go to realign.
	move(0,-1)
	time.sleep(0.2)
	while abs(getGyro()) < 90:
		spin(1)
	move(1)
	time.sleep(0.2)
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
		ro[holdValues][ro[holdPointer]] = hold.speed
		if ro[holdPointer] >= HOLD_SR_LEN:
			ro[holdPointer] = 0
		irValue = ir.value()
		if irValue != 0:
			ro[irValues][ro.irPointer] = irValue
			ro[irPointer] += 1
			if ro[irPointer] >= STORAGE_LENGTH:
				ro[irPointer] = 0
			angle = (irValue-5)*0.25
			move(angle)
			hold.run_forever(duty_cycle_sp=50)
		else:
			if mean(ro[irValues]) > 5:
				move(1)
			else:
				move(-1)
			hold.run_forever(duty_cycle_sp=50)
		# Check if it's found:
		if mean(ro[oldValues]) <= ro[holdThreshold]:
			# We've got the ball
			return "realign", ro

def realign(ro):
	# If angle is far off, rotate until not the case.
	while True:
		gyroValue = getGyro()
		if abs(gyroValue) < 5:
			return "moveToGoal", ro
		else:
			spin(-gyroValue/abs(gyroValue))

def reset(ro):
	# Reset the robot as it's been picked up.
	resetGyro()
	return "lookForBall", ro

if __name__ == '__main__':
	functions = {"moveGoal": moveToGoal, "retreat": retreat, "shoot": shoot, "lookForBall": lookForBall, "realign": realign}
	robotObject = {irValues: [5] * STORAGE_LENGTH, irPointer: 0, holdThreshold: 0, holdValues: [0] * HOLD_SR_LEN, holdPointer: 0} # List of helpful things that are helpful.
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
	hThreshold=sum(holdingSr)/(HOLD_SR_LEN + 1.0)
	oldTime = time.time()
	robotObject[holdThreshold] = hThreshold
	while True:
		print state
		state,robotObject = functions[state](robotObject)