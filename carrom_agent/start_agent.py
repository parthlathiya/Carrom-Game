# A Sample Carrom Agent to get you started. The logic for parsing a state
# is built in
from __future__ import division
from thread import *
import math
import numpy as np
import time
import socket
import sys
import argparse
import random
import ast
 
# Parse arguments
 
parser = argparse.ArgumentParser()
 
parser.add_argument('-np', '--num-players', dest="num_players", type=int,
                    default=1,
                    help='1 Player or 2 Player')
parser.add_argument('-p', '--port', dest="port", type=int,
                    default=12121,
                    help='port')
parser.add_argument('-rs', '--random-seed', dest="rng", type=int,
                    default=0,
                    help='Random Seed')
parser.add_argument('-c', '--color', dest="color", type=str,
                    default="Black",
                    help='Legal color to pocket')
args = parser.parse_args()
 
off =0
host = '127.0.0.1'
port = args.port
num_players = args.num_players
random.seed(args.rng)  # Important
color = args.color
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect((host, port))
 
 
# Given a message from the server, parses it and returns state and action
 
 
def parse_state_message(msg):
    s = msg.split(";REWARD")
    s[0] = s[0].replace("Vec2d", "")
    reward = float(s[1])
    state = ast.literal_eval(s[0])
    return state, reward
 
 
pockets = [[44.1, 44.1], [755.9, 44.1], [755.9, 755.9], [44.1, 755.9]]
stry = 140
strikeleft = (170,stry)
strikeright = (630,stry)
striker_radius = 20.6
pocket_radius = 22.51
coin_radius = 15.01
max_force = 0.08
min_force = 0.04
gradient = 0.00008695652
gradient2 = 0.00005395652
SIDE_COLLISION_BOUND = 5
 
 
def slope_with_pocket(coin,pocket_idx):
    pock = pockets[pocket_idx]
    return (coin[1]-pock[1])/(coin[0]-pock[0])
 
def intercept_with_pocket(coin,pocket_idx):
    return coin[1] - slope_with_pocket(coin,pocket_idx)*coin[0]
 
def slope_with_point(coin,point):
    return (coin[1]-point[1])/(coin[0]-point[0])
 
def is_on_strikeline(coin):
    if coin[1] < 170 and coin[1] > 120:
        if coin[0] >= strikeleft[0] - 15 and coin[1] <= strikeright[0] + 15:
            return True
    return False
 
 
def distance_from_point(coin,any_x,any_y):
    return math.sqrt((coin[0] - any_x)**2 + (coin[1] - any_y)**2)
 
def distance_from_pocket(coin,pocket_idx):
    return distance_from_point(coin,pockets[pocket_idx][0],pockets[pocket_idx][1])
 
 
 
# intersection of two points
 
def get_normalised_position(position_x):
    return (position_x - strikeleft[0]) /(strikeright[0] - strikeleft[0])
 
def get_strike_position(p0,p1,p2,p3):
    m1 = (p1[1] - p0[1]) / (p1[0] - p0[0])
    m2 = (p3[1] - p2[1]) / (p3[0] - p2[0])
    if  m1 != m2:
        x = ((m1 * p0[0]) - (m2*p2[0]) + p2[1] - p0[1] ) / (m1-m2)
        y = p0[1] + m1*(x - p0[0])
        if x >= strikeleft[0] and x <= strikeright[0]:
            return x
        else:
            return -1
    else:
        return -1
     
 
def get_direct_shot(allcoins,coin,pocket_idx):
    #return (true,striker_x,angle,force) if shot is possible else return (false,-1,-1,-1)
    #print coin,"dir"
    xpos = get_strike_position(coin,pockets[pocket_idx],strikeleft,strikeright)
    if xpos == -1:
        return False,-1,-1,-1
    slope = slope_with_pocket(coin,pocket_idx)
    angle = math.degrees(math.atan(slope))
    if pocket_idx == 1 and coin[1] > strikeLine and angle < 0:
        angle = angle + 180
    force = computeforce(allcoins,coin,pocket_idx,xpos)
    if force == -1:
        return False,-1,-1,-1
    return True,xpos,angle,force
 
def computeforce(allcoins,coin, pocket_idx,striker_x):
 
    if pocket_idx == 3:
        force = min_force + (striker_x - strikeleft[0])*gradient
    elif pocket_idx == 2:
        force = min_force + (strikeright[0] - striker_x)*gradient
    flag,blocks = iswayclear_fordirectshot(allcoins,coin,pocket_idx,(striker_x,stry))
    if flag == False:
        #force = force + blocks*0.02
        return -1
    return force
 
#https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_two_points
def distance_point_line(P1,P2,x,y):
    return abs( (P2[1] - P1[1])*x - (P2[0] - P1[0])*y + P2[0]*P1[1] - P1[0]*P2[1]) / math.sqrt( (P2[1] - P1[1])**2 + (P2[0] - P1[0])**2)
 
def distance(P1,P2):
    return math.sqrt( (P2[1] - P1[1])**2 + (P2[0] - P1[0])**2)
 
 
 
 
def iswayclear_fordirectshot(allcoins,pickedcoin, pocket_idx, striker_position):
     
    flag = True
    count = 0
    for coin in allcoins:
        if coin == pickedcoin:
            continue
        coin_distance = distance_point_line(pockets[pocket_idx],striker_position,coin[0],coin[1])
        if coin_distance < coin_radius + striker_radius:
            flag = True
            count = count+1
 
 
    return flag,count
     
def iswayclear_fortrickshot(allcoins,pickedcoin, pocket_idx, striker_position):
     
    flag = True
    count = 0   
    for coin in allcoins:
        if coin == pickedcoin:
            continue
        coin_distance = distance_point_line(pockets[pocket_idx],pickedcoin,coin[0],coin[1])
        coin_distance2 = distance_point_line(striker_position,pickedcoin,coin[0],coin[1])
        if coin_distance < coin_radius + striker_radius or coin_distance2 < coin_radius + striker_radius:
            flag = False
            count = count+1
 
    return flag,count
 
turns = 0
strikeLine = 145
def agent_1player(state):
 
    global turns
    currflag = False
    flag = 1
    a = str(0) + ',' + \
    str(0) + ',' + str(0)
    # print state
    try:
        state, reward = parse_state_message(state)  # Get the state and reward
     
    # Assignment 4: your agent's logic should be coded here
        whites = state['White_Locations']
        blacks = state['Black_Locations']
        red = state['Red_Location']
        allcoins = red + whites + blacks
        if(turns == 0):
            angle = 100
            force = 1.0
            position = 0.6
        else:
            selectedpocket = -1
            selectedcoin = -1
            for coin in allcoins:
                if is_on_strikeline(coin):
                    if coin[0] > 400:
                        angle = 0
                        force = 0.5
                        position = 0.4
                    else:
                        angle = 180
                        force = 0.5
                        position = 0.6
                    currflag = True
                    break
 
            if currflag == False:       
                for coin in allcoins:
                    if is_on_strikeline(coin):
                        continue
                    if coin[1] < 160:
                        continue   
                    currflag,position,angle,force = get_direct_shot(allcoins,coin,2)
                    if coin[1] > 600 and coin[0] > 650:
                        currflag = False
                    #if position < strikeright[0] - 10:
                    #    position = position + 10
                    #angle = angle + 0.5
                    position = get_normalised_position(position)
                    #print currflag
                    if currflag == True:
                        selectedpocket = 2
                        selectedcoin = coin
                        force = 0.5
                        print "Taking direct shot top right"
                        break
                    currflag,position,angle,force = get_direct_shot(allcoins,coin,3)
                    #if coin[1] > 600 and coin[0] < 350:
                    #    currflag = False
                    if angle < 0:
                        angle = angle + 180
                    #angle = angle - 2
                    #if position > strikeleft[0] + 10:
                    #    position = position - 10
                    position = get_normalised_position(position)
                    #print currflag
                    if currflag == True:
                        selectedpocket = 3
                        selectedcoin = coin
                        force = 0.5
                        print "Taking direct shot top left"
                        break
 
 
            if currflag == False:
                # tricky shot
                for coin in allcoins:
                    if coin[1] < 700:
                        continue
                    if coin[0] < 400:    
                        position = strikeright
                        selectedpocket = 3
                    else:
                        position = strikeleft
                        selectedpocket = 2
                    if distance(coin,pockets[selectedpocket]) < 100:
                        if position == strikeright:
                            position = strikeleft
                        else:
                            position = strikeright    
                    print coin
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    angle2 =  math.degrees(math.atan(slope_with_pocket(coin,selectedpocket)))
                    clear,blocks = iswayclear_fortrickshot(allcoins,coin,selectedpocket,position)
 
                    force = 0.05 + (distance(coin,position))*gradient2
                    position = get_normalised_position(position[0])
                    print "Taking trick shot upside Mustafa"
 
                    if coin[0] < 400 and angle < 0:
                        angle = angle + 180
                        angle2 = angle2 + 180
                    if selectedpocket == 2:
                        if angle > angle2:
                            angle = angle - 0
                        else:
                            angle = angle + 0
                    if selectedpocket == 3:
                        if angle > angle2:
                            angle = angle + 0
                        else:
                            angle = angle - 0          
                     
                    # if angle>125 and angle<155:
                    #     force = 0.05
                    # elif angle<55 and angle>35:
                    #     force = 0.05
                    # else:
                    #     force = 0.08
                    #if angle > 90:
                        #angle = angle - 1
                    #else:
                       # angle = angle + 1
                    if clear == False :
                        force = force + blocks*0.01
                    currflag = True
                    break
 
            if currflag == False:
                # tricky shot
                # side shot
                for coin in allcoins:
                    if coin[1]<300:
                        continue
                    if coin[0] > 170 and coin[0] < 630:
                        continue
                    if coin[0] < 170:    
                        position = strikeleft
                        selectedpocket = 3
                    else:
                        position = strikeright
                        selectedpocket = 2
 
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
 
                    clear,blocks = iswayclear_fortrickshot(allcoins,coin,selectedpocket,position)
                    position = get_normalised_position(position[0])
                    print "Taking trick shot upside"
                    if coin[1]>600 and coin[0]>50:
                        force = 0.04
                    else:
                        force = 0.07
                    if clear == False:
                        force = force + blocks*0.01
                    if coin[0] < 170 and angle < 0:
                        angle = angle + 180
                    currflag = True
                    break
 
 
             
            if currflag == False:
                # tricky shot
                for coin in allcoins:
                    if coin[1]>strikeLine:
                        continue
                    if coin[0] > 400:    
                        position = strikeleft
                    else:
                        position = strikeright
 
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    position = get_normalised_position(position[0])
                    force = 0.06
                    print "Taking down shot"
                    if coin[0] > 400 and angle > 0:
                        angle = angle - 180
                    if coin[0] < 400 and angle < 180:
                        angle = angle + 180
                    currflag = True
                    break
 
            if currflag == False:
                # random touch shot
                for coin in allcoins:
                    if coin[1]<strikeLine:
                        continue
                    if coin[0]<400:
                        position = strikeright
                    else:
                        position = strikeleft
                    print "Taking touch shot"
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    if coin[1] > strikeLine and angle < 0:
                        angle = angle + 180
                    elif coin[1] < strikeLine and angle > 0:
                        angle = angle - 180
 
 
 
                    position = get_normalised_position(position[0])
                    force = 0.2
                    break
        a = str(position) + ',' + \
        str(angle) + ',' + str(force)        
        s.send(a)
        print(a)
        turns= turns+1
    except Exception as e:
        pass
         
 
    return flag
 
 
def agent_2player(state, color):
    
    
    if(color == "Black"):
        strikeLine = 700 - 145
    else:
        strikeLine = 145
    
    global turns
    currflag = False
    a = str(0) + ',' + \
    str(0) + ',' + str(0) 
    flag = 1
 
    # Can be ignored for now
    #a = str(random.random()) + ',' + \
    #    str(random.randrange(-45, 225)) + ',' + str(random.random())
 
 
    try:
        state, reward = parse_state_message(state)  # Get the state and reward
     
        # Assignment 4: your agent's logic should be coded here
        whites = state['White_Locations']
        blacks = state['Black_Locations']
        red = state['Red_Location']
        
        if(color == "White"):
            allcoins = red + whites
        elif(color == "Black"):
            allcoins = red + blacks
        
        if(turns == 0):
            angle = 100
            force = 1.0
            position = 0.6
        else:
            selectedpocket = -1
            selectedcoin = -1
            for coin in allcoins:
                if is_on_strikeline(coin):
                    if coin[0] > 400:
                        angle = 0
                        force = 0.5
                        position = 0.4
                    else:
                        angle = 180
                        force = 0.5
                        position = 0.6
                    currflag = True
                    break
 
            if currflag == False:       
                for coin in allcoins:
                    if is_on_strikeline(coin):
                        continue
                    if coin[1] < 160:
                        continue   
                    currflag,position,angle,force = get_direct_shot(allcoins,coin,2)
                    if coin[1] > 600 and coin[0] > 650:
                        currflag = False
                    #if position < strikeright[0] - 10:
                    #    position = position + 10
                    #angle = angle + 0.5
                    position = get_normalised_position(position)
                    #print currflag
                    if currflag == True:
                        selectedpocket = 2
                        selectedcoin = coin
                        force = 0.5
                        print "Taking direct shot top right"
                        break
                    currflag,position,angle,force = get_direct_shot(allcoins,coin,3)
                    #if coin[1] > 600 and coin[0] < 350:
                    #    currflag = False
                    if angle < 0:
                        angle = angle + 180
                    #angle = angle - 2
                    #if position > strikeleft[0] + 10:
                    #    position = position - 10
                    position = get_normalised_position(position)
                    #print currflag
                    if currflag == True:
                        selectedpocket = 3
                        selectedcoin = coin
                        force = 0.5
                        print "Taking direct shot top left"
                        break
 
 
            if currflag == False:
                # tricky shot
                for coin in allcoins:
                    if coin[1] < 700:
                        continue
                    if coin[0] < 400:    
                        position = strikeright
                        selectedpocket = 3
                    else:
                        position = strikeleft
                        selectedpocket = 2
                    if distance(coin,pockets[selectedpocket]) < 100:
                        if position == strikeright:
                            position = strikeleft
                        else:
                            position = strikeright    
                    print coin
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    angle2 =  math.degrees(math.atan(slope_with_pocket(coin,selectedpocket)))
                    clear,blocks = iswayclear_fortrickshot(allcoins,coin,selectedpocket,position)
 
                    force = 0.05 + (distance(coin,position))*gradient2
                    position = get_normalised_position(position[0])
                    print "Taking trick shot upside Mustafa"
 
                    if coin[0] < 400 and angle < 0:
                        angle = angle + 180
                        angle2 = angle2 + 180
                    if selectedpocket == 2:
                        if angle > angle2:
                            angle = angle - 0
                        else:
                            angle = angle + 0
                    if selectedpocket == 3:
                        if angle > angle2:
                            angle = angle + 0
                        else:
                            angle = angle - 0          
                     
                    # if angle>125 and angle<155:
                    #     force = 0.05
                    # elif angle<55 and angle>35:
                    #     force = 0.05
                    # else:
                    #     force = 0.08
                    #if angle > 90:
                        #angle = angle - 1
                    #else:
                       # angle = angle + 1
                    if clear == False :
                        force = force + blocks*0.01
                    currflag = True
                    break
 
            if currflag == False:
                # tricky shot
                # side shot
                for coin in allcoins:
                    if coin[1]<300:
                        continue
                    if coin[0] > 170 and coin[0] < 630:
                        continue
                    if coin[0] < 170:    
                        position = strikeleft
                        selectedpocket = 3
                    else:
                        position = strikeright
                        selectedpocket = 2
 
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
 
                    clear,blocks = iswayclear_fortrickshot(allcoins,coin,selectedpocket,position)
                    position = get_normalised_position(position[0])
                    print "Taking trick shot upside"
                    if coin[1]>600 and coin[0]>50:
                        force = 0.04
                    else:
                        force = 0.07
                    if clear == False:
                        force = force + blocks*0.01
                    if coin[0] < 170 and angle < 0:
                        angle = angle + 180
                    currflag = True
                    break
 
 
             
            if currflag == False:
                # tricky shot
                for coin in allcoins:
                    if coin[1]>strikeLine:
                        continue
                    if coin[0] > 400:    
                        position = strikeleft
                    else:
                        position = strikeright
 
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    position = get_normalised_position(position[0])
                    force = 0.06
                    print "Taking down shot"
                    if coin[0] > 400 and angle > 0:
                        angle = angle - 180
                    if coin[0] < 400 and angle < 180:
                        angle = angle + 180
                    currflag = True
                    break
 
            if currflag == False:
                # random touch shot
                for coin in allcoins:
                    if coin[1]<strikeLine:
                        continue
                    if coin[0]<400:
                        position = strikeright
                    else:
                        position = strikeleft
                    print "Taking touch shot"
                    angle = math.degrees(math.atan(slope_with_point(coin,position)))
                    if coin[1] > strikeLine and angle < 0:
                        angle = angle + 180
                    elif coin[1] < strikeLine and angle > 0:
                        angle = angle - 180
 
 
 
                    position = get_normalised_position(position[0])
                    force = 0.2
                    break
        a = str(position) + ',' + \
        str(angle) + ',' + str(force)        
        print(a)
        turns= turns+1
        s.send(a)
    except Exception as e:
        print "Error in sending:",  a, " : ", e
        print "Closing connection"
        flag = 0
 
    return flag
 
off=0
while 1:
    state = s.recv(1024)  # Receive state from server
    if num_players == 1:
        if agent_1player(state) == 0:
            break
    elif num_players == 2:
        if agent_2player(state, color) == 0:
            break
s.close()
 
 
#testcases
 
TESTSTATE = {'White_Locations': [(400, 368), (437, 420), (372, 428), (337, 367), (402, 332),
                                     (463, 367), (470, 437), (405, 474), (340, 443)],
                 'Red_Location': [(400, 403)],
                 'Score': 0,
                 'Black_Locations': [(433, 385), (405, 437), (365, 390), (370, 350), (432, 350),
                                     (467, 402), (437, 455), (370, 465), (335, 406)]}
