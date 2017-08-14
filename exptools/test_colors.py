# -*- coding: utf-8 -*-
"""

Program Instructions: TEST_CONTRASTS
====================================
-Change the rgb values at the top of the script to reflect your experiment 
colors on lines 38-42
-Change the session number to reflect the day of testing on line 56.
-Change the color you will currently adjust on line 65.

Click "RUN". 

Decrease the luminance with the back arrow, increase the luminance with the 
forward arrow.

Once the luminance is adjusted as necessary, press the ESCAPE key. This will 
then save the final contrast as a variable.
"""
import pickle
import numpy as np
from psychopy import visual, event, monitors

#change the session here for each day of testing
session = int(raw_input('Which session? '))
timepoint = int(raw_input('Before or after (0 or 1)? '))
try:
    Input = open(('/home/slnib/studies/psyinf/experiments/Foraging/exp_files/colors-%.2i-00.pkl'%session), 'rb')
    colorDict = pickle.load(Input)
    for k in colorDict.keys():
           if k == 'blue':
              color4 = colorDict[k]
           elif k == 'red':
               color1 = colorDict[k]
           elif k == 'purple':
               color5 = colorDict[k]
           elif k == 'brown':
               color2 = colorDict[k]
           elif k == 'green':
               color3 = colorDict[k]
except:
    color1 = np.array([235,0,0])#red
    color5 = np.array([166,  53, 214] )
    color2 = np.array([143,  86,  61])
    color3 = np.array([ 37, 115,   0])
    color4 = np.array([  19,  109, 119])


colors = ['red','brown','green','blue','purple']
possible_colors = [color1, color2, color3, color4, color5]
pp_cols = [(col-128)/128.0 for col in possible_colors]



mon=monitors.Monitor('scanMonitor', width=30, distance=35)
mon.setSizePix((1280,1050))
win=visual.Window(fullscr=False, units='deg', monitor=mon)

#change the color here
polygon = visual.Circle(win, radius=50, lineColor=[0,0,0], pos=(0,2), fillColor = pp_cols[0])
gun_idx = 0# change r, g or b value?
col_idx = 0# which of the 5 colors needs changing
new_col = [0,0,0,0,0]
polygon.draw()
win.flip()  
while True:
    key = event.waitKeys(keyList = ['left','right','up','down','return','escape','space'])[0]
    
    if key == 'up':
        gun_idx += 1
        if gun_idx%3 ==0:
            print 'change R GUN'
        elif gun_idx%3 == 1:
            print 'change G GUN'
        else:
            print 'change B GUN'
    elif key == 'down':
        gun_idx -=1
        if gun_idx%3 ==0:
            print 'change R GUN'
        elif gun_idx%3 == 1:
            print 'change G GUN'
        else:
            print 'change B GUN'
    elif key == 'space':
        print polygon.fillColor
    elif key == 'left' and not polygon.fillColor[gun_idx%3] <-0.95:
        polygon.fillColor[gun_idx%3] -= 0.05
    elif key == 'right' and not polygon.fillColor[gun_idx%3] >0.95:
        polygon.fillColor[gun_idx%3] += 0.05
    elif key == 'return':
        new_col[col_idx%5] = np.int16(polygon.fillColor*128.0 +128)
        print 'SAVE RGB VALUES FOR %s: '%colors[col_idx%5], polygon.fillColor
        pp_cols[col_idx%5] = polygon.fillColor
        col_idx +=1
        polygon.fillColor= pp_cols[col_idx%5] 
    elif key == 'escape':
        newColDict =  {j: new_col[i] for i,j in enumerate(colors)}
        print 'Final colors: \n'
        for i in newColDict.items():
            print i
        break
    polygon.draw()
    win.flip()          
  
output = open(('/home/slnib/studies/psyinf/experiments/Foraging/exp_files/colors-%.2i-%.2i.pkl' %(session,timepoint)), 'wb')
#output = open(('/home/ede/Desktop/data/colors-%.2i.pkl' %session), 'wb')
pickle.dump(newColDict, output)
output.close() 
win.close()        
