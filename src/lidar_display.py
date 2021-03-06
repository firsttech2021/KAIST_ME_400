#!/usr/bin/env python
from __future__ import print_function
import roslib
import sys
import rospy
import cv2
import numpy as np
import math

from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_msgs.msg import Int32
from std_msgs.msg import Float32

## image size setting
x_size = 1080
y_size = 720 

### the origin of the angle is center of the robot front
start_x_angle  = 0
end_x_angle = 60

start_x_angle = 0
end_y_angle = 60

#################
standard_x = x_size/2
standard_y = y_size/2

## color configure
white = (255,255,255)
red = (0,0,255)
green = (0,255,0)
starnge = (102,58,255)

## other parameters

## list of the x,y angle
x_y_coordinate = {}
start_angle_l = 0
end_angle_l = 270

start_angle_r = 540
end_angle_r = 660

dir = 0

class core_processing:

    def __init__(self):

        self.image_sub = rospy.Subscriber("scan",LaserScan,self.callback) #original image subscriber
        self.imu_sub = rospy.Subscriber("compass",Float32,self.callback2)

        self.front = rospy.Publisher('front_motor',Int32,queue_size=10)
        self.rear = rospy.Publisher('rear_motor',Int32,queue_size=10)
        self.servo = rospy.Publisher('servo_motor',Int32,queue_size=10)


    def cal_draw_location(self,img,angle,range):

        global x_y_coordinate
        global start_x
        global start_y
        global end_x
        global end_y

        theta = angle*(math.pi/573)
        x = -(math.sin(theta) *range)
        y = math.cos(theta) *range
        try:
            x = int(x*100)
        except :
            x = 0
        
        try:
            y = int(y*100)
        except:
            y = 0
        #print(x,y)
        self.draw_lidar_point(img,x,y,1,white)
 
        ##save the x,y coordinate
        
        x_y_coordinate[str(angle)] = [x,y]

        if(angle == 60):
            pass

        return x,y

    def draw_lidar_point(self,img,x,y,point_size,color):
        ## draw lidar point
        cv2.circle(img,(x+standard_x,-y+standard_y),point_size,color,-1)

    def draw_line(self,img,point1,point2):

        ## transform the point to the normal X_Y coordinate
        a1 = point1[0]+standard_x
        b1 = -point1[1]+standard_y
        a2 = point2[0]+standard_x
        b2 = -point2[1]+standard_y

        ## draw the line
        cv2.line(img,(a1,b1),(a2,b2),red,2)

    
    def cal_dist(self,x1, y1, x2, y2, a, b):
        # calculate the disstance between point and line
        # (x1,y1) and (x2,y2) make the line , (a,b) is the point

        area = abs((x1-a) * (y2-b) - (y1-b) * (x2 - a))
        AB = ((x1-x2)**2 + (y1-y2)**2) **0.5
        try:
            distance = area/AB
        except:
            distance = 0
        return distance

    def make_point_and_line(self,data,black_img,start_angle,end_angle): #Draw the left line


        #global start_angle
        #global end_angle
        global x_y_coordinate
        global start_x
        global start_y
        global end_x
        global end_y

        ##initialize all data
        x_y_coordinate = {}
        start_x = 0 
        start_y = 0
        end_x = 0
        end_y = 0
        max_dist = 0
        max_index = 0
        max_thres_dist = 0

        for i in range(len(data.ranges)):
            ranges = data.ranges[i]
            self.cal_draw_location(black_img,i,ranges)
        
        
        x1 = x_y_coordinate[str(start_angle)][0]
        y1 = x_y_coordinate[str(start_angle)][1]
        ## check not the origin
        x1 = x_y_coordinate[str(start_angle+1)][0]
        y1 = x_y_coordinate[str(start_angle+1)][1]



        x2 = x_y_coordinate[str(end_angle-1)][0]
        y2 = x_y_coordinate[str(end_angle-1)][1]

        self.draw_lidar_point(black_img,x1,y1,5,white) #Make point to the start angle of the left
        self.draw_lidar_point(black_img,x2,y2,5,green) #Make point to the end angle of the left


        for j in range(start_angle,end_angle): #Get the point to draw the line
            a = x_y_coordinate[str(j)][0]
            b = x_y_coordinate[str(j)][1] 
            dist = self.cal_dist(x1,y1,x2,y2,a,b)
            thres_dist = (a*a+b*b)
            if(dist > max_dist and a != 0 and thres_dist > max_thres_dist and dist < 120):
                max_thres_dist = thres_dist
                max_dist = dist
                max_index = j

                print(max_dist)


        #define the point fo the target
        x3 = x_y_coordinate[str(max_index)][0]
        y3 = x_y_coordinate[str(max_index)][1]
        

        #draw point and line
        self.draw_lidar_point(black_img,x3,y3,5,starnge)
        self.draw_line(black_img,x_y_coordinate[str(start_angle)],x_y_coordinate[str(max_index)])
        self.draw_line(black_img,x_y_coordinate[str(max_index)],x_y_coordinate[str(end_angle-1)])




    def callback(self,data):
        black_img = np.zeros(shape=[y_size,x_size,3],dtype=np.uint8)

        # the 0-360 scale is 0-1146

        self.make_point_and_line(data,black_img,60,270) #This value must be clock wise -> draw left line
        self.make_point_and_line(data,black_img,1146-270,1146) #This value must be clock wise -> draw right line

        
        
        ###
        

        cv2.imshow("black",black_img)
        cv2.waitKey(1)

        ######

        





        ######

        front_motor =  0
        rear_motor = 0
        servo_angle = 90
        ####

        ###publish the command
        self.rear.publish(rear_motor)
        self.front.publish(front_motor)
        self.servo.publish(servo_angle)

    def callback2(self,data):
        global dir
        dir = data.data
        pass

def main(args):
    cp = core_processing()
    rospy.init_node('core', anonymous=True)
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    cv2.destroyAllWindows()
   
if __name__ == '__main__':
    main(sys.argv)


#### system brief

# ros_sub(in the init function ) -> callback(left,right,display)