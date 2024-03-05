# -*- coding: utf-8 -*-
"""
@date: 2017/03/08

@author: peeters

@description:
This file contains the definition and methods of the class pyjama 1.0.

pyJAMA (python Json Audio Music Annotation) is a json format for storing annotations.
Its main differences with other proposals is that a pyjama file describes the whole collection of (audio) files not only a single file.
A pyjama file is a dictionay with two main keys:
    - 'schemaversion': which gives the version of the pyjama schema used (currently 1.2)
    - 'collection' which describes a collection. It contains two main keys
        - 'entry' which is a list of entries, each describing a single (audio file)
            - An entry is itself a dictionary which keys are the various descriptions
            - A single description is itself a list (it is therefore possible to have various values for a single description, such as various segments or multi-label)
                Each element of this list is a SDDE (Shared Description Dictionary Atiom)
                A SDDA has the keys
                    value, confidence, time, duration, startFreq, endFreq
                    Not all this keys are mandatory.
                To store a global (not time specific) description: simply use 'value' (use 'confidence' if you know how reliable is the 'value')
                To store a marker (with null duration, such as beat positions) description: simply use 'value' and 'time'
                To store a segment (such as speech segments in a file): simply use 'value', 'time' and 'duration'
                The keys 'startFreq' and 'endFreq' are used for Audiosculpt musicdescription xml compatibility.

        - 'descriptiondefinition' (which provides the definitions of the description provided for each entry)
            - Each description is defined by a dictionary with the following keys
                - 'typeExtent': describes the temporal extent of the value {'global', 'marker', 'segment'}
                - 'typeContent': describes the format of the value {'text', 'numeric'}
                - 'typeConstraint': describes whether a constraint has to be applied to validate a value  {'free', 'filePath, 'valueInDictionary'}
                - 'dictionary': contains the list of possible values (when 'valueInDictionary' is used)
                The following 'keys' are used for GUI purposes
                - 'isTable'
                - 'isEditable'
                - 'isFilter'

version 1.1
2017/03/08:	Added breakpoint support
        Format is
            time(nbTime): is a vecor
            value((nbDIm,nbTime)): is a matrix

version 1.2
2017/03/14: Following discussion with Diemo Schwarz and Benjamin Matuszewski:
        1) Update breakpoint format -> add columnName key to descriptiondefinition
        2) Add new typeExtent 'breakpointTime' and 'breakpointValue' -> in order to be able to share time across descriptions
        Other proposals:
            - flip the dimensions of 'value' for breakpoint -> REJECTED: this would lead to a [[][][][][]] when storing a 1-dimensional breakpoint over time
            - change 'entry' with 'entries' -> REJECTED for backward compatibility

2017/03/24: Re-factoring the python code to follow pep8 writing style recommendations

2018/03/06: Added example of meanMfcc output

2024/03/05: Change compatibility to python 3 -> changed print
            Removed 'encoding' in json_dump
"""

import sys
import os
import json
import glob
import pprint as pp
#import ipdb
import copy
import numpy as np
import collections


def F_backwardCompatibility(entry):
    """
    to ensure backward compatibility: IF only one value THEN do not use list
    """
    #return entry

    if len(entry) == 1:
        if type(entry[0]) is not list:
            entry = entry[0]
    return entry


def F_numericInput(numeric_l=[], checkVector=False, prefix='', fieldName=''):
    """
    check and transform numerical value to list of float
    """

    if type(numeric_l) not in [float, list, np.ndarray]:
        raise Exception("%s '%s' must be float, list or np.ndarray" % (prefix, fieldName))

    if type(numeric_l) is list:
        for numeric in numeric_l:
            if type(numeric) is not float:
                raise Exception("%s all elements of '%s' list must be float" % (prefix, fieldName))


    if type(numeric_l) is float:
        numeric_l = [numeric_l]

    elif type(numeric_l) is np.ndarray:
        if checkVector:
            if numeric_l.ndim == 2:
                if (numeric_l.shape[0] > 1) and (numeric_l.shape[0] > 1):
                    raise Exception("%s '%s' cannot be a matrix" % (prefix, fieldName))
                elif (numeric_l.shape[0] == 1) and (numeric_l.shape[0] > 1):
                    numeric_l = numeric_l[0, :]
                else:
                    numeric_l = numeric_l[:, 0]
            numeric_l = numeric_l.tolist()

    return numeric_l


def F_checkValueInDictionary(value_l, currentTypeContent, dictionary, notValidAction):
    """
    """
    if type(value_l) is list:
        """ flatten value: in case it is a list of list, it is changed to a list """
        flattenValue_l = [item for sublist in value_l for item in sublist]
    else:
        flattenValue_l = [value_l]

    isValid = True
    for value in flattenValue_l:

        if currentTypeContent == 'text':
            if value not in dictionary:
                if notValidAction == 'addToDictionary':
                    print("'value'(%s) is not part of dictionary ->  updating dictionary" % (value))
                    dictionary.append(value)
                else:
                    isValid = False

        elif currentTypeContent == 'numeric':
            minValue = dictionary[0]
            maxValue = dictionary[1]
            if (value < minValue) or (maxValue < value):
                if notValidAction == 'addToDictionary':
                    if value < minValue:
                        dictionary[0] = value
                    if value > maxValue:
                        dictionary[1] = value
            else:
                isValid = False

    return isValid, dictionary



class C_pyjama():
    """
    """

    data = {}
    currentPosition = -1
    notValidAction = ''

    # ===============================================
    def __init__(self, notValidAction='addToDictionary'):
        """
        """

        self.data['schemaversion'] = 1.31
        self.data['collection'] = {'descriptiondefinition': {}, 'entry': []}
        if notValidAction in ['addToDictionary', 'filterOut', 'reject']:
            self.notValidAction = notValidAction
        else:
            raise Exception('Problem creating "pyjama" structure: unknown type "%s" for notValidAction' % (notValidAction))


    # ===============================================
    def __setattr__(self, attrName, val):
        """
        """

        if hasattr(self, attrName):
            self.__dict__[attrName] = val
        else:
            raise Exception("self.%s note part of the fields" % attrName)

    # ===============================================
    def M_addDefinition(self, descriptionName, typeConstraint='free', typeContent='text',
                        typeExtent='global', columnName=[], generator={},
                        dictionary=[], isTable=True, isEditable=True,
                        isFilter=True):
        """
        """

        self.data['collection']['descriptiondefinition'][descriptionName] = collections.OrderedDict()

        if typeContent in ['text', 'numeric']:
            self.data['collection']['descriptiondefinition'][descriptionName]['typeContent'] = typeContent
        else:
            raise Exception('unknown type "%s" for typeContent' % (typeContent))

        if typeExtent in ['global', 'segment', 'marker', 'breakpoint', 'breakpointTime', 'breakpointValue']:
            self.data['collection']['descriptiondefinition'][descriptionName]['typeExtent'] = typeExtent
        else:
            raise Exception('unknown type "%s" for typeExtent' % (typeExtent))

        if typeConstraint in ['filePath', 'free', 'valueInDictionary']:
            self.data['collection']['descriptiondefinition'][descriptionName]['typeConstraint'] = typeConstraint
        else:
            raise Exception('unknown type "%s" for typeConstraint' % (typeConstraint))

        self.data['collection']['descriptiondefinition'][descriptionName]['dictionary'] = copy.copy(dictionary)
        self.data['collection']['descriptiondefinition'][descriptionName]['columnName'] = copy.copy(columnName)
        self.data['collection']['descriptiondefinition'][descriptionName]['isTable'] = isTable
        self.data['collection']['descriptiondefinition'][descriptionName]['isEditable'] = isEditable
        self.data['collection']['descriptiondefinition'][descriptionName]['isFilter'] = isFilter
        if len(generator):
            self.data['collection']['descriptiondefinition'][descriptionName]['generator'] = generator

    # ===============================================
    def M_addEntry(self):
        """
        """

        entry = {}
        for descriptionName in self.data['collection']['descriptiondefinition'].keys():
            entry[descriptionName] = []
        self.data['collection']['entry'].append(entry)
        self.currentPosition += 1

    # ===============================================
    def M_updateEntry(self, descriptionName, value_l=[], confidence_l=[], time_l=[], duration_l=[],
                      startFreq_l=[], endFreq_l=[], comment=''):
        """
        """

        prefix = "ERROR updating self.data['collection']['entry'][%d]['%s']:\n\t" % (len(self.data['collection']['entry']), descriptionName)

        if descriptionName not in self.data['collection']['descriptiondefinition'].keys():

            raise Exception("%s '%s' is not part of 'descriptiondefinition' -> add it first in 'descriptiondefinition'" % (prefix, descriptionName))

        else:

            currentTypeExtent = self.data['collection']['descriptiondefinition'][descriptionName]['typeExtent']
            currentTypeContent = self.data['collection']['descriptiondefinition'][descriptionName]['typeContent']
            currentTypeConstraint = self.data['collection']['descriptiondefinition'][descriptionName]['typeConstraint']

            if currentTypeExtent in ['global', 'marker', 'segment', 'breakpoint', 'breakpointTime', 'breakpointValue']:
                """ check VALUE """

                if type(value_l) not in [str, int, float, list, np.ndarray]:
                    raise Exception("%s 'value' must be str, int, float, list or np.ndarray")

                if type(value_l) in [str, float, int]:
                    value_l = [value_l]

                elif type(value_l) is np.ndarray:
                    if value_l.ndim != 2:
                        raise Exception("%s IF 'value' is np.ndarray THEN it must be must value.ndim == 2")
                    """ value (nbDim, nbTime) -> [ [allDim(Time1)] [allDim(Time2)] [allDim(Time3)] [allDim(Time4)] ]"""
                    value_l = value_l.T.tolist()

                if currentTypeExtent in ['breakpoint', 'breakpointValue']:
                    nbColumnName = len(self.data['collection']['descriptiondefinition'][descriptionName]['columnName'])
                    if len(value_l[0]) != nbColumnName:
                        raise Exception("%s nbDim of 'value' (%d) must be equal to nbColumnName' (%d)" % (prefix, len(value_l[0]), nbColumnName))

                if currentTypeConstraint == 'free':
                    isValid = True

                elif currentTypeConstraint == 'filePath':
                    isValid = True
                    for value in value_l:
                        if not(os.path.isfile(value)):
                            isValid = False
                elif currentTypeConstraint == 'valueInDictionary':
                    isValid, dictionary = F_checkValueInDictionary(value_l, currentTypeContent, self.data['collection']['descriptiondefinition'][descriptionName]['dictionary'], self.notValidAction)



            if currentTypeExtent in ['marker', 'segment', 'breakpoint']:
                """ check TIME """

                time_l = F_numericInput(numeric_l=time_l, checkVector=True, prefix=prefix, fieldName='time')

                if len(time_l) > 1: # WASABI exception
                    if len(time_l) != len(value_l):
                        raise Exception("%s len('time') must be equal to len('value')" % (prefix))



            if currentTypeExtent in ['segment']:
                """ check DURATION """

                duration_l = F_numericInput(numeric_l=duration_l, checkVector=True, prefix=prefix, fieldName='duration')

                if len(time_l) > 1: # WASABI exception
                    if len(time_l) != len(duration_l):
                        raise Exception("%s len('time') must be equal to len('duration')" % (prefix))

            confidence_l = F_numericInput(numeric_l=confidence_l, checkVector=True, prefix=prefix, fieldName='confidence')
            startFreq_l = F_numericInput(numeric_l=startFreq_l, checkVector=True, prefix=prefix, fieldName='startFreq')
            endFreq_l = F_numericInput(numeric_l=endFreq_l, checkVector=True, prefix=prefix, fieldName='endFreq')

            if len(confidence_l):
                if len(time_l):
                    if len(time_l) != len(confidence_l):
                        raise Exception("%s len('time') must be equal to len('confidence')" % (prefix))

            if len(startFreq_l):
                if len(time_l):
                    if len(time_l) != len(startFreq_l):
                        raise Exception("%s len('time') must be equal to len('startFreq')" % (prefix))

            if len(endFreq_l):
                if len(time_l):
                    if len(time_l) != len(endFreq_l):
                        raise Exception("%s len('time') must be equal to len('endFreq')" % (prefix))


            if currentTypeExtent == 'breakpointValue':

                # --- Look for the name of the corresponding breakpointTime
                # -- in descriptiondefinition
                timeName = ''
                for key in self.data['collection']['descriptiondefinition'].keys():
                    if self.data['collection']['descriptiondefinition'][key]['typeExtent'] == 'breakpointTime':
                        timeName = key

                if len(timeName) == 0:
                    raise Exception("%s no 'breakpointTime' has been defined in 'descriptiondefinition'" % (prefix))

                if timeName not in self.data['collection']['entry'][self.currentPosition].keys():
                    raise Exception("%s no 'breakpointTime' has been given for current entry" % (prefix))

                if len(self.data['collection']['entry'][self.currentPosition][timeName]) == 0:
                    raise Exception("%s no 'breakpointTime' has been given in current entry" % (prefix))

                nbTime = len(self.data['collection']['entry'][self.currentPosition][timeName][0]['value'])
                if len(value_l) != nbTime:
                    raise Exception("%s number of columns of 'value' (%d) must be equal to number of 'time' (%d)" % (prefix, value.shape[1], nbTime))


            entry = {}

            if isValid:
                if len(value_l):
                    value_l = F_backwardCompatibility(value_l)
                    entry['value'] = value_l
                if len(time_l):
                    time_l = F_backwardCompatibility(time_l)
                    entry['time'] = time_l
                if len(duration_l):
                    duration_l = F_backwardCompatibility(duration_l)
                    entry['duration'] = duration_l
                if len(confidence_l):
                    confidence_l = F_backwardCompatibility(confidence_l)
                    entry['confidence'] = confidence_l
                if len(startFreq_l):
                    startFreq_l = F_backwardCompatibility(startFreq_l)
                    entry['startFreq'] = startFreq_l
                if len(endFreq_l):
                    endFreq_l = F_backwardCompatibility(endFreq_l)
                    entry['endFreq'] = endFreq_l
                if len(comment):
                    entry['comment'] = comment

                self.data['collection']['entry'][self.currentPosition][descriptionName].append(entry)

            else:

                if self.notValidAction == 'filterOut':
                    print("%s 'value'(%s) is not part of dictionary -> filteringOut" % (prefix, value))
                else:
                    raise Exception("%s 'value'(%s) is not part of the dictionary -> add it first in 'descriptiondefinition'" % (prefix, value))
                # --- END: Check validity of the entry



    # ===============================================
    def M_check(self):
        """
        Parse an existing pyjama structure
            Check for ALL entries
                That ALL descriptiondefinition exist
                If not, creates an empty 'value' for this descriptiondefinition
        """

        key_l = self.data['collection']['descriptiondefinition'].keys()

        nbEntry = len(self.data['collection']['entry'])
        for numEntry in range(0, nbEntry):
            for key in key_l:
                if key not in self.data['collection']['entry'][numEntry].keys():
                    self.data['collection']['entry'][numEntry][key] = []
                    self.data['collection']['entry'][numEntry][key].append({'value': ''})
                elif len(self.data['collection']['entry'][numEntry][key]) == 0:
                    self.data['collection']['entry'][numEntry][key] = []
                    self.data['collection']['entry'][numEntry][key].append({'value': ''})
                elif 'value' not in self.data['collection']['entry'][numEntry][key][0].keys():
                    self.data['collection']['entry'][numEntry][key] = []
                    self.data['collection']['entry'][numEntry][key].append({'value': ''})

        return

    # ===============================================
    def M_print(self):
        """
        """

        pp.pprint(self.data)

    # ===============================================
    def M_save(self, fileName):
        """
        """

        print("writting pyjama file: %s" % (fileName))
        with open(fileName, 'w') as f:
            #json.dump(self.data, f, encoding='utf-8', indent=4)
            json.dump(self.data, f, indent=4)
