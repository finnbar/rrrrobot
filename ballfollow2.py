#!/usr/bin/python2.7
import atexit
from ev3dev.auto import *
import time

functions = {"moveGoal": moveToGoal, "retreat": retreat, "shoot": shoot, "lookForBall": lookForBall, "realign": realign}

'''
Cool Things we Could Add:
> Bluetooth - "I've got the ball, don't go for it." (Seb Towers 2016)
'''

def moveToGoal():
	# Move forwards in a straight line, but if you're >45d out, spin back (realign). Check throughout whether retreat should be called.
	pass

def retreat():
	# We hit "the wall", reverse slightly, turn 90d, move forwards a bit (this is blocking). Then go to realign.
	pass

def shoot():
	# Fire all motors forwards! Gotta go fast. On losing the ball, swap to findBall.
	pass

def lookForBall():
	# If ball's in sight, go get it, else spin. On finding it, realign.
	pass

def realign():
	# If angle is far off corrects the orientation of the robot. On getting to <5d, switch to moveToGoal.
	pass

def reset():
	# Reset the robot as it's been picked up.

if __name__ == '__main__':
	state = "lookForBall"
	while True:
		state = functions[state]()