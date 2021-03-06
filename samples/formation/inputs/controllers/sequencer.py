"""
Authors: Arjun Kumar and Jnaneshwar Das
testing sequencer
"""

import rospy
import subprocess
import os
import sys
import math
import tf
import time
import numpy as np


from std_msgs.msg import Int8, Bool, Float64, Float64MultiArray, MultiArrayLayout, MultiArrayDimension
from std_srvs.srv import Empty


class TestSequence:
    command = Float64MultiArray()
    command.layout = MultiArrayLayout()
    command.layout.dim = [MultiArrayDimension()]
   
    iterator = 1 #step through commands in the sequence - 0 should be reserved for takeoff

    def __init__(self, NUM_UAV):

        global status

	self.command.layout.dim[0].label = 'command'
	self.command.layout.dim[0].size = 4
	self.command.layout.dim[0].stride = 4*8 	
	self.command.layout.data_offset = 0

	#testing circle  data = [x, y, r, n]; n - sequence number
	self.command.data = [0,0,10,0]	

	status = [Int8() for i in range(NUM_UAV)]
	sum_stat = Int8()
	sum_stat.data = 0
	
	#making Anna's Code

	print 'ls -> ' + str(subprocess.check_output('ls /simulation/AnnaCode', shell=True))
	print 'make -> ' + str(subprocess.check_output('make /simulation/AnnaCode', shell=True))
	#print 'cd ->' + str(subprocess.check_output('cd /simulation/AnnaCode', shell=True))
	#print 'ls -> ' + str(subprocess.check_output('ls', shell=True, cwd = '/simulation/AnnaCode'))
	





 
	# subscribing to each uav's status
        for i in range(NUM_UAV):
            
	    exec ('def status_cb' + str(i) + '(msg): status[' + str(i) + '] = msg')
            #exec ('def state_cb' + str(i) + '(msg): state[' + str(i) + '] = msg' )
	    #rospy.Subscriber('/mavros/state')
	    rospy.Subscriber('/sequencer/status' + str(i), Int8, callback=eval('status_cb' + str(i)))

        rospy.init_node('sequencer_test', anonymous=True)

        print "INIT\n"

        pub = rospy.Publisher('/sequencer/command', Float64MultiArray, queue_size=10)
        rospy.Subscriber('/sequencer/status', Float64MultiArray, callback=self.status_cb)

        rate = rospy.Rate(10)  # Hz
        rate.sleep()

        # wait to all drones to connect to the sequencer
        nc = pub.get_num_connections()
        while nc < NUM_UAV:
            nc = pub.get_num_connections()
            rate.sleep()

        print 'num_connections = ' + str(nc)
        print 'publishing - \n' + str(self.command)
        pub.publish(self.command)
        sys.stdout.flush()

        while not rospy.is_shutdown():
		publish = True

		for i in range(NUM_UAV): 
			if status[i].data < self.command.data[3]:
				publish = False

		if publish and self.iterator < 5:
 
			self.command.data = self.nextCommand()
			pub.publish(self.command)
			print 'published  - ' + str(self.command.data)
			continue #continue past next if check so publish goes back to false 

		if publish and self.iterator > 4 and self.iterator < 13:		
			for i in range(NUM_UAV): 
				print status[i].data
				print status[i].data < self.command.data[3]
			print self.command.data[3]
			print publish

			if self.iterator == 5:
				print 'running wrapper'
				sys.stdout.flush()
				#print 'wrapper -> \n' + str(subprocess.check_output('python mpcpsowrapper.py 0 1', shell = True, cwd = '/simulation/AnnaCode'))
				config = np.loadtxt('/simulation/AnnaCode/config0_0.txt')
				print config.ndim
				print config.shape
				print config
				for i in range (0, config.shape[0] - 1):
					if config[i,0] == 0:
						config = np.delete(config, (range(i,config.shape[0])), axis = 0)
						break
				print '\n\n\n\n\n\n\n'	
				print config
				np.savetxt('/simulation/AnnaCode/config0_0.txt',config)
			self.command.data = self.nextCommand()
			pub.publish(self.command)
			print 'published - ' + str(self.command.data)

		sys.stdout.flush() 

	
    def status_cb(self, msg):
        self.status = msg
	                  
    def nextCommand(self):
	if self.iterator > 4:
		temp = [0,0,0, self.iterator]
	elif self.iterator == 4:                #flip to velocity control
		temp = [0,0,30,self.iterator]	
	elif self.iterator == 3:
		temp = [0,0,30,self.iterator]
	elif self.iterator == 2:
		temp = [0,0,40,self.iterator]
	elif self.iterator == 1:
		temp = [0,0,10,self.iterator]
	self.iterator += 1
	return temp 

if __name__ == "__main__":
    TestSequence(int(sys.argv[1]))
