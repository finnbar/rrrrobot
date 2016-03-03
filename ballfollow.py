#!/usr/bin/python2.7
import atexit
import ev3dev as ev3
from time import sleep

STORAGE_LENGTH = 15 # No of values in the mean
TURNINESS = 150 # Sharpness of turn
HOLD_SR_LEN = 20 # Length of shift register for holding

ir = ev3.sensor('in1:i2c8') # It's an old sensor, so it needs i2c8
gyro = ev3.gyro_sensor('in2')
steer = [ev3.large_motor('outA'),ev3.large_motor('outB')]
hold = ev3.large_motor('outD')
kicker = ev3.motor('outC')

# a.run_to_rel_pos(position_sp=720,duty_cycle_sp=-100) is the command for doing certain length rotationy stuff

vals = [5 for i in range(STORAGE_LENGTH)]
c = 0
gyroValue = 0
calibrateGyro = 0

def updateGyro(dt):
	# Update the gyro, given delta time
	gyroValue += (gyro.value()*dt) - calibrateGyro
	gyroValue = (abs(gyroValue) % 360) * (abs(gyroValue)/gyroValue)

def mean(t):
	return sum(t)/float(len(t))

def move(angle):
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
	steer[0].run_forever(duty_cycle_sp=int(ls))
	steer[1].run_forever(duty_cycle_sp=int(rs))

def move(a): pass # uncomment this line for tabletop tests, to stop it moving

def exit_handler(): # This stops the motors, which is a good idea.
	steer[0].stop()
	steer[1].stop()
	hold.stop()

if __name__ == '__main__':
	print "GO!"
	holding_sr=[] # This is our general shift register, I'll explain later.
	assert steer[0].connected and steer[1].connected and hold.connected # Basic assert, just in case
	hold.run_forever(duty_cycle_sp=50) # This is our dribbler motor
	hold_threshold = 0
	gyro.mode = "GYRO-RATE"
	sleep(1)
	for _ in range(20): # Check the dribbler speed to work out when the ball is in the way
		holding_sr.append(hold.speed)
	hold_threshold=sum(holding_sr)/21.0
	holding_sr = []
	for _ in range(20):
		holding_sr.append(gyro.value())
	print hold_threshold
	calibrateGyro = sum(holding_sr)/20.0
	oldTime = time.time()
	while True:
		updateGyro(time.time() - oldTime)
		q = ir.value() # Angle from 1 - 9 units (very left to very right)
		del(holding_sr[0])
		holding_sr.append(hold.speed)
		if sum(holding_sr)/HOLD_SR_LEN <= hold_threshold: # If the ball is in the dribbler (the dribbler motor is slower)
			move(0) # This will be rewritten! It'll rotate the right way, go forward until something's close and then fire!
			sleep(0.5)
			hold.run_forever(duty_cycle_sp=-100)
			sleep(0.5)
		elif q != 0: # We see the ball!
			vals[c] = q
			c+=1
			if c>=STORAGE_LENGTH:
				c = 0
			s = mean(vals) # Get the mean of the last STORAGE_LENGTH readings
			angle = (s-5)*0.25
			move(angle)
			hold.run_forever(duty_cycle_sp=50)
		else: # Angle is 0, or failed to find ball
			if mean(vals) > 5: # If it was already going right,
				move(1)    # Go right!
			else:
				move(-1)   # Else, go left!
			hold.run_forever(duty_cycle_sp=50)
		oldTime = time.time()
