# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 14:29:43 2017

@author: ede
"""
import json
import sys
import importlib

#load configuration file
try:
    jsonfile = sys.argv[1]
except IndexError as e:
    jsonfile = 'cfg.json'   
try:
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
    data_file.close()
except IOError as e:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."

# load scripts
parseScript = importlib.import_module(cfg['parseScript'])
preprocScript = importlib.import_module(cfg['preprocScript'])
analysisScript = importlib.import_module(cfg['analysisScript'])
makeEvents = importlib.import_module(cfg['eventsScript'])
# run scrips
parseScript.run(cfg)
preprocScript.run(cfg)
#makeEvents.run(cfg)
analysisScript.run(cfg)
