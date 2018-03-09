# -*- coding: utf-8 -*-

import pyjama
import glob
import sys
import ipdb
import os
import numpy as np
import json

# ===============================================
def F_readCsv2(annotFile):
    """
    annotTime_l, annotLabel_l = F_readCsv2(annotFile)
    """

    text_file = open(annotFile, 'r')
    lines = text_file.readlines()
    text_file.close()
    annotTime_l = []
    annotLabel_l = []
    for line in lines:
        line = line.strip('\n')
        aaa = line.split('\t')
        annotTime_l.append(float(aaa[0]))
        annotLabel_l.append(aaa[1])
    return annotTime_l, annotLabel_l

# ===============================================
def F_readCsv3(annotFile):
    """
    annotTime_l, annotStop_l, annotLabel_l = F_readCsv3(annotFile)
    """

    text_file = open(annotFile, 'r')
    lines = text_file.readlines()
    text_file.close()
    annotTime_l = []
    annotStop_l = []
    annotLabel_l = []
    for line in lines:
        line = line.strip('\n')
        aaa = line.split('\t')
        print aaa
        annotTime_l.append( float(aaa[0]) )
        annotStop_l.append( float(aaa[1]) )
        annotLabel_l.append( aaa[2] )
    return annotTime_l, annotStop_l, annotLabel_l

# ==========================
def exampleSegmentPitchAndText(argv):
    """
    Example of using pyjama to the store the structural segments of a
    collection (here we consider the SALAMI music structure collection)
    """

    # --- 1) Create the pyjama file structure
    #myPyjama = pyjama.C_pyjama(notValidAction='reject')
    myPyjama = pyjama.C_pyjama(notValidAction='addToDictionary')
    #myPyjama = pyjama.C_pyjama(notValidAction='filterOut')

    myPyjama.M_addDefinition(descriptionName='filepath',
                             typeConstraint='free')
    myPyjama.M_addDefinition(descriptionName='pitchandtexttype',
                             typeExtent='segment',
                             typeConstraint='free',
                             generator={},
                             dictionary=[])


    myPyjama.M_addEntry()
    myPyjama.M_updateEntry(descriptionName='filepath', value_l='./myAudioFile.mp3')
    myPyjama.M_updateEntry(descriptionName='pitchandtexttype', value_l=[440., 'wasabi'], time_l=0.0, duration_l=1.0)

    # --- 3) Save
    myPyjama.M_save('./exampleSegmentPitchAndText.pyjama')
    return



# ==========================
def exampleSegment(argv):
    """
    Example of using pyjama to the store the structural segments of a
    collection (here we consider the SALAMI music structure collection)
    """

    # --- 1) Create the pyjama file structure
    #myPyjama = pyjama.C_pyjama(notValidAction='reject')
    myPyjama = pyjama.C_pyjama(notValidAction='addToDictionary')
    #myPyjama = pyjama.C_pyjama(notValidAction='filterOut')
    myPyjama.M_addDefinition(descriptionName='filepath',
                             typeConstraint='filePath')
    myPyjama.M_addDefinition(descriptionName='structtype',
                             typeExtent='segment',
                             typeConstraint='valueInDictionary',
                             generator={'name': '', 'version': '', 'date': ''},
                             dictionary=['Silence', 'A', 'B', 'C', 'D', 'E', 'F', 'I', 'V', 'End'])

    myPyjama.M_addDefinition(descriptionName='structtypeList',
                             typeExtent='segment',
                             typeConstraint='valueInDictionary',
                             generator={'name': '', 'version': '', 'date': ''},
                             dictionary=['Silence', 'A', 'B'])

    audioFile_l = glob.glob('./_examples/*.mp3')

    for audioFile in audioFile_l:
        annotFile = audioFile.replace('.mp3', '.struct.lab')
        if os.path.isfile(annotFile):
            # --- 2) Create a new entry and update its value
            myPyjama.M_addEntry()
            myPyjama.M_updateEntry(descriptionName='filepath', value_l=audioFile)
            annotTime_l, annotStop_l, annotLabel_l = F_readCsv3(annotFile)
            annotDuration_l = []
            for num in range(0, len(annotTime_l)):
                myPyjama.M_updateEntry(descriptionName='structtype', value_l=annotLabel_l[num], time_l=annotTime_l[num], duration_l=annotStop_l[num]-annotTime_l[num])
                annotDuration_l.append(annotStop_l[num]-annotTime_l[num])

            myPyjama.M_updateEntry(descriptionName='structtypeList', value_l=annotLabel_l, time_l=annotTime_l, duration_l=annotDuration_l)

    # --- 3) Save
    myPyjama.M_save('./exampleSegment.pyjama')
    return


# ==========================
def exampleBreakPoint(argv):
    """
    This is an example of code to store a 'breakpoint' function in pyjama
    In a breakpoint
        times must be represented as a numpy vector (not a matrix) with dimension (nbDim)
        values must be represented as a numpy matrix with dimensions (nbDim, nbTime)
    Pyjama store both as list or list of lists
    """


    # --- 1) Create the pyjama file structure
    my = pyjama.C_pyjama()

    # --- 2) Create a first entry and update its value
    my.M_addDefinition(descriptionName='f0', typeExtent='breakpoint', columnName=['f0'])
    my.M_addDefinition(descriptionName='mfcc', typeExtent='breakpoint', columnName=['mfcc1', 'mfcc2', 'mfcc3', 'mfcc4', 'mfcc5', 'mfcc6', 'mfcc7', 'mfcc8', 'mfcc9', 'mfcc10', 'mfcc11', 'mfcc12', 'mfcc13'])
    my.M_addDefinition(descriptionName='meanMfcc', typeExtent='global', typeContent='numeric', columnName=['mfcc1', 'mfcc2', 'mfcc3', 'mfcc4', 'mfcc5', 'mfcc6', 'mfcc7', 'mfcc8', 'mfcc9', 'mfcc10', 'mfcc11', 'mfcc12', 'mfcc13'])

    my.M_addEntry()

    f0_time_v = np.arange(0, 1, 0.08)
    f0_value_m = np.random.randn(1, f0_time_v.shape[0])
    my.M_updateEntry(descriptionName='f0', value_l=f0_value_m, time_l=f0_time_v)

    mfcc_time_v = np.arange(0, 1, 0.1)
    mfcc_value_m = np.random.randn(13, mfcc_time_v.shape[0])
    my.M_updateEntry(descriptionName='mfcc', value_l=mfcc_value_m, time_l=mfcc_time_v)

    my.M_updateEntry(descriptionName='meanMfcc', value_l=np.mean(mfcc_value_m, axis=1, keepdims=True))

    my.M_addEntry()
    # --- 2) Create a second entry and update its value
    f0_time_v = np.arange(0, 1, 0.08)
    f0_value_m = np.random.randn(1, f0_time_v.shape[0])
    my.M_updateEntry(descriptionName='f0', value_l=f0_value_m, time_l=f0_time_v)
    mfcc_time_v = np.arange(0, 1, 0.1)
    mfcc_value_m = np.random.randn(13, mfcc_time_v.shape[0])
    my.M_updateEntry(descriptionName='mfcc', value_l=mfcc_value_m, time_l=mfcc_time_v)

    # --- 3) Save
    my.M_save('exampleBreakPoint.pyjama')
    return

    # --- Re-load to pyjama file and convert back the breakpoint to numpy format
    with open('exampleBreakPoint.pyjama') as f:
        my = json.load(f)
    time_v = np.array(my['collection']['entry'][0]['mfcc'][0]['time']).T
    value_m = np.array(my['collection']['entry'][0]['mfcc'][0]['value']).T

    ipdb.set_trace()


# ==========================
def exampleBreakPointTimeValue(argv):
    """
    This an example to store several 'breakpoint' functions with a shared time
    In this case the times are stored as a 'breakpointTime'
    while the values of each breakpoint are stored as 'breakpointValue'?
    in a 'breakpointTime'
        times must be represented as a numpy vector (not a matrix) with dimension (nbDim)
    in a 'breakpointValue'
        values must be represented as a numpy matrix with dimensions (nbDim, nbTime)
    """

    # --- 1) Create the pyjama file structure
    my = pyjama.C_pyjama()
    my.M_addDefinition(descriptionName='time', typeExtent='breakpointTime')
    my.M_addDefinition(descriptionName='alldescriptors', typeExtent='breakpointValue', columnName=['f0', 'harmonicity'])
    my.M_addDefinition(descriptionName='loudness', typeExtent='breakpointValue', columnName=['loudness'])

    nbTime = 10
    # --- 2) Create a new entry and update its value
    my.M_addEntry()
    my.M_updateEntry(descriptionName='time', value_l=np.arange(0,nbTime).reshape((1,nbTime)))
    my.M_updateEntry(descriptionName='alldescriptors', value_l=np.zeros((2, nbTime)))
    my.M_updateEntry(descriptionName='loudness', value_l=np.zeros((1, nbTime)))

    # --- 3) Save
    my.M_save('exampleBreakPointTimeValue.pyjama')

    return
    # --- Re-load to pyjama file and convert back the breakpoint to numpy format
    with open('exampleBreakPointTimeValue.pyjama') as f:
        my = json.load(f)

    time_v = np.array(my['collection']['entry'][0]['time'][0]['value'])
    alldescriptor_m = np.array(my['collection']['entry'][0]['alldescriptors'][0]['value'])
    loudness_v = np.array(my['collection']['entry'][0]['loudness'][0]['value'])
    ipdb.set_trace()


# ==========================
if __name__ == '__main__':
    """
    """
    exampleSegmentPitchAndText(sys.argv[1:])
    exampleSegment(sys.argv[1:])
    exampleBreakPoint(sys.argv[1:])
    exampleBreakPointTimeValue(sys.argv[1:])
