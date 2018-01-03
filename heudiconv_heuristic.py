import os

scaninfo_suffix = '.json'

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return (template, outtype, annotation_classes)

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module: 

    item: index within category 
    subject: participant id 
    seqitem: run number during scanning
    subindex: sub index within group
    """

    info = {}
    for s in seqinfo:
	print s
        if 'SmartBrain' in s[2]:
            continue
        elif 'SMARTPLAN_TYPE_BRAIN' in s[2]:
            continue
        elif 'EPI_3mm' in s[2]:
            key = create_key('func/{subject}_task-choice_run-{item:01d}_bold')
        elif 'field' in s[2]:
            key = create_key('fmap/{subject}_fmap')       
        elif 'T1W_' in s[2]:
            key = create_key('anat/{subject}_T1w')
	elif 'ScreenCapture' in s[2]:
        print("What is ScreenCapture supposed to be?")
	    continue
        else:
            print s[2]
            raise(RuntimeError, "YOU SHALL NOT PASS!")

        if not key in info:
            info[key] = []

        info[key].append(s[2])
	print s[2]
    return info
