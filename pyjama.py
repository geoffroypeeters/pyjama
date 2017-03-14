# -*- coding: utf-8 -*-
"""
@date: 2017/03/08

@author: peeters

@description:
This file contains the definition and methods of the class pyjama 1.0.

pyJAMA (python Json Audio Music Annotation) is a json format for storing annotations.
Its main differences with other proposals is that a pyjama file describes the whole collection of (audio) files not only a single file.
A pyjama file is a dictionay with three main keys:
- 'schemaversion': gives the version of the pyjama schema used (currently 1.0)
- 'collection' (which contains a list of entries, each describing a single (audio file)
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
2017/03/14: 	Following discussion with Diemo Schwarz and Benjamin Matuszewski:
			1) Update breakpoint format -> add columnName key to descriptiondefinition
			2) Add new typeExtent 'breakpointTime' and 'breakpointValue' -> in order to be able to share time across descriptions
			Other proposals: 
				- flip the dimensions of 'value' for breakpoint -> REJECTED: this would lead to a [[][][][][]] when storing a 1-dimensional breakpoint over time
				- change 'entry' with 'entries' -> REJECTED for backward compatibility
"""

import sys
import os
import json
import glob
import pprint as pp
import ipdb
import copy
import numpy as np

class C_pyjama():
	data 			= {}
	currentPosition 	= -1
	notValidAction 	= ''
	
	# ===============================================
	def __init__(self, notValidAction='addToDictionary'):
		self.data['schemaversion'] 	= 1.2
		self.data['collection'] 	= {'descriptiondefinition':{}, 'entry':[]}
		if notValidAction in ['addToDictionary', 'filterOut', 'reject']:
			self.notValidAction = notValidAction
		else:
			raise Exception('unknown type "%s" for notValidAction' % (notValidAction))
			

	# ===============================================
	def __setattr__(self, attrName, val):
		if hasattr(self, attrName):		self.__dict__[attrName] = val
		else:						raise Exception("self.%s note part of the fields" % attrName)


	# ===============================================
	def M_addDefinition(self, name, typeConstraint='free', typeContent='text', typeExtent='global', columnName=[], generator={}, dictionary=[], isTable=True, isEditable=True, isFilter=True):
		
		self.data['collection']['descriptiondefinition'][name] = {}
			
		if typeContent in ['text', 'numeric']:
			self.data['collection']['descriptiondefinition'][name]['typeContent'] = typeContent
		else:
			raise Exception('unknown type "%s" for typeContent' % (typeContent))

		if typeExtent in ['global', 'segment', 'marker', 'breakpoint', 'breakpointTime', 'breakpointValue']:
			self.data['collection']['descriptiondefinition'][name]['typeExtent'] = typeExtent
		else:
			raise Exception('unknown type "%s" for typeExtent' % (typeExtent))
			
		if typeConstraint in ['filePath', 'free', 'valueInDictionary']:
			self.data['collection']['descriptiondefinition'][name]['typeConstraint'] = typeConstraint
		else:
			raise Exception('unknown type "%s" for typeConstraint' % (typeConstraint))
			
		self.data['collection']['descriptiondefinition'][name]['dictionary']	= copy.copy(dictionary)
		self.data['collection']['descriptiondefinition'][name]['columnName']	= copy.copy(columnName)
		self.data['collection']['descriptiondefinition'][name]['isTable'] 	= isTable 
		self.data['collection']['descriptiondefinition'][name]['isEditable']	= isEditable 
		self.data['collection']['descriptiondefinition'][name]['isFilter'] 	= isFilter 
		if len(generator): 	self.data['collection']['descriptiondefinition'][name]['generator'] 	= generator


	# ===============================================
	def M_addEntry(self):
		entry = {}
		for name in self.data['collection']['descriptiondefinition'].keys():
			entry[name] = []
		self.data['collection']['entry'].append(entry)
		self.currentPosition += 1


	# ===============================================
	def M_updateEntry(self, name, value='', time=-1, duration=-1, confidence=-1, startFreq=-1, endFreq=-1):
	
		if name in self.data['collection']['descriptiondefinition'].keys():
			entry = {}
			is_ok = False
			if type(value)==float: 
				is_ok=True
			else: 
				if len(value): 
					is_ok=True
					
			if is_ok:
				# --- BEGIN: Check validity of the entry
				isValid = False				
				currentTypeContent 	= self.data['collection']['descriptiondefinition'][name]['typeContent']
				currentTypeConstraint 	= self.data['collection']['descriptiondefinition'][name]['typeConstraint']
				currentTypeExtent 		= self.data['collection']['descriptiondefinition'][name]['typeExtent']
				print currentTypeExtent
				
				if currentTypeExtent=='breakpoint':
					if value.ndim!=2: 
						raise Exception('value must be a matrix not a vector')
					nbColumnName = len(self.data['collection']['descriptiondefinition'][name]['columnName'])
					if value.shape[0]!=nbColumnName: 
						raise Exception('number of rows of value (%d) must be equal to number of columnName (%d)' % (value.shape[0], nbColumnName))

					if time.ndim>1: 
						raise Exception('time must be a vector not a matrix')
					if value.shape[1]!=time.shape[0]: 
						raise Exception('number of columns of value (%d) must be equal to number of times (%d)' % (value.shape[1], time.shape[0]))

					# --- convert numpy array to list
					# --- Note: convert back to numpy: np.array( np.zeros((3,10)).tolist() )
					time = time.tolist()					
					value = value.tolist()
					entry['value'] = value
					entry['time'] = time
					self.data['collection']['entry'][self.currentPosition][name].append(entry)
					
				elif currentTypeExtent=='breakpointTime':
					# --- in the specific case of 'breakpointTime', the times are given through the value variable
					if value.ndim>1: 
						raise Exception('time must be a vector not a matrix')
					value = value.tolist()					
					entry['value'] = value
					self.data['collection']['entry'][self.currentPosition][name].append(entry)
					
				elif currentTypeExtent=='breakpointValue':
					if value.ndim!=2: 
						raise Exception('value must be a matrix not a vector')
					nbColumnName = len(self.data['collection']['descriptiondefinition'][name]['columnName'])
					if value.shape[0]!=nbColumnName: 
						raise Exception('number of rows of value (%d) must be equal to number of columnName (%d)' % (value.shape[0], nbColumnName))
					
					# --- Look for the name of the corresponding breakpointTime in descriptiondefinition
					timeName = ''
					for key in self.data['collection']['descriptiondefinition'].keys():
						if self.data['collection']['descriptiondefinition'][key]['typeExtent']=='breakpointTime':
							timeName=key
					if len(timeName)==0: 
						raise Exception('no breakpointTime has been defined in descriptiondefinition')
					if timeName not in self.data['collection']['entry'][self.currentPosition].keys(): 
						raise Exception('no breakpointTime has been given in current entry')
					if len(self.data['collection']['entry'][self.currentPosition][timeName])==0: 
						raise Exception('no breakpointTime has been given in current entry')
					nbTime = len(self.data['collection']['entry'][self.currentPosition][timeName][0]['value'])
					if value.shape[1]!=nbTime: 
						raise Exception('number of columns of value (%d) must be equal to number of times (%d)' % (value.shape[1], nbTime))

						
					value = value.tolist()
					entry['value'] = value
					self.data['collection']['entry'][self.currentPosition][name].append(entry)

				else:
					if currentTypeConstraint=='free':		
						isValid = True
					elif currentTypeConstraint=='filePath':
						if os.path.isfile(value):
							isValid = True
					elif currentTypeConstraint=='valueInDictionary':
						if currentTypeContent=='text':
							if value in self.data['collection']['descriptiondefinition'][name]['dictionary']:
								isValid = True
							else:
								if self.notValidAction=='addToDictionary':	
									print 'addToDictionary "%s" to "%s"' % (value, name)
									self.data['collection']['descriptiondefinition'][name]['dictionary'].append(value)
									isValid = True
						elif currentTypeContent=='numeric':
							minValue = self.data['collection']['descriptiondefinition'][name]['dictionary'][0]
							maxValue = self.data['collection']['descriptiondefinition'][name]['dictionary'][1]
							if minValue <= value & value <= maxValue:
								isValid = True
							else:
								if self.notValidAction=='addToDictionary':
									if value<minValue: self.data['collection']['descriptiondefinition'][name]['dictionary'][0] = value
									if value>minValue: self.data['collection']['descriptiondefinition'][name]['dictionary'][1] = value
										
						
					if isValid:
						entry['value'] = value
						if time>-1: 		entry['time'] 		= time
						if duration>-1: 	entry['duration'] 		= duration
						if confidence>-1: 	entry['confidence'] 	= confidence
						if startFreq>-1: 	entry['startFreq']		= startFreq
						if endFreq>-1: 	entry['endFreq'] 		= endFreq					
						self.data['collection']['entry'][self.currentPosition][name].append(entry)					
					else:
						if self.notValidAction=='filterOut':
							print 'filterOut "%s" of "%s"' % (value, name)
						else:
							raise Exception('value "%s" not valid for entry "%s" -> add first in description definition' % (value, name))
					# --- END: Check validity of the entry
					
				
		else:
			raise Exception('name "%s" not is descriptiondefinition -> add first in description definition' % (name))


	# ===============================================
	def M_check(self):
		key_l = self.data['collection']['descriptiondefinition'].keys()

		nbEntry = len(self.data['collection']['entry'])
		for numEntry in range(0, nbEntry):
			for key in key_l:
				notOK = False
				if key not in self.data['collection']['entry'][numEntry].keys():
					self.data['collection']['entry'][numEntry][key]=[]
					self.data['collection']['entry'][numEntry][key].append({'value': ''})
				elif len(self.data['collection']['entry'][numEntry][key])==0:
					self.data['collection']['entry'][numEntry][key]=[]
					self.data['collection']['entry'][numEntry][key].append({'value': ''})
				elif 'value' not in self.data['collection']['entry'][numEntry][key][0].keys():
					self.data['collection']['entry'][numEntry][key]=[]
					self.data['collection']['entry'][numEntry][key].append({'value': ''})
					
		return
		
		
	# ===============================================
	def M_print(self):
		pp.pprint(self.data)


	# ===============================================
	def M_save(self, fileName):
		print "writting pyjama file: %s" % (fileName)
		with open(fileName, 'w') as f: json.dump(self.data, f, encoding='utf-8', indent=4)


# ===============================================
def F_readCsv2(annotFile):
	"""
	annotTime_l, annotLabel_l = F_readCsv2(annotFile)
	"""
	
	text_file 	= open(annotFile, 'r')
	lines 		= text_file.readlines()
	text_file.close()
	annotTime_l = []
	annotLabel_l =[]
	for line in lines:
		line	= line.strip( '\n' )
		a 	= line.split('\t')
		annotTime_l.append( float(a[0]) )
		annotLabel_l.append(a[1])
	return annotTime_l, annotLabel_l


# ==========================	
def main(argv):
	"""
	Example of usage for storing structural segments corresponding to the SALAMI collection
	"""
	
	audioFile_l = glob.glob('/Users/peeters/_work/_sound/_collection/local_structure/2014_Salami/_audio/*/*.mp3')

	doInit = True
	for audioFile in audioFile_l:
		if doInit:
			myPyjama = C_pyjama(notValidAction='addToDictionary')
			myPyjama.M_addDefinition(name='filepath', typeConstraint='filePath')
			myPyjama.M_addDefinition(name='structtype', typeExtent='segment', typeConstraint='valueInDictionary', generator={'name':'', 'version':'', 'date':''}, dictionary=['Silence', 'A', 'B', 'C', 'D', 'E', 'F', 'I', 'V', 'End'] )
			doInit = False

		annotFile 	= audioFile.replace('/_audio/', '/salami-data-public-master/annotations/').replace('audio.mp3', 'parsed/textfile1_uppercase.txt')
		if os.path.isfile(annotFile):
			myPyjama.M_addEntry()
			myPyjama.M_updateEntry('filepath', audioFile)

			annotTime_l, annotLabel_l 	= F_readCsv2(annotFile)
			for num in range(0,len(annotTime_l)-1):
				myPyjama.M_updateEntry('structtype', annotLabel_l[num], annotTime_l[num], annotTime_l[num+1]-annotTime_l[num])
	
	# --- collect all the labels that have been used all over the files
	myPyjama.M_check()
	myPyjama.M_save('./dataSet_SALAMI.json')
	return


# ==========================
def exampleBreakPoint(argv):
	"""
	in breakpoint
		time must be a vector (not a matrix)
		value must be a matrix with (nbDim, nbTime)
	"""
	
	import numpy as np
	my = C_pyjama()
	my.M_addDefinition(name='f0',typeExtent='breakpoint',columnName=['f0','harmonicity'])
	my.M_addEntry()
	my.M_updateEntry(name='f0', value=np.zeros((2,10)), time=np.zeros(10))
	my.M_save('test.pyjama')
	
	with open('test.pyjama') as f: my=json.load(f)
	np.array(my['collection']['entry'][0]['f0'][0]['time'])
	np.array(my['collection']['entry'][0]['f0'][0]['value'])
	ipdb.set_trace()
	
# ==========================
def exampleBreakPointTimeValue(argv):
	"""
	in breakpointtime
		time must be a vector (not a matrix)
	in breakpointvalue
		value must be a matrix with (nbDim, nbTime)
	"""
	
	import numpy as np
	my = C_pyjama()
	my.M_addDefinition(name='blu',			typeExtent='breakpointTime')
	my.M_addDefinition(name='alldescriptors',typeExtent='breakpointValue', 	columnName=['f0','harmonicity'])
	my.M_addDefinition(name='loudness',		typeExtent='breakpointValue', 	columnName=['loudness'])
	my.M_addEntry()
	my.M_updateEntry(name='blu', 			value=np.zeros(10))
	my.M_updateEntry(name='alldescriptors', 	value=np.zeros((2,10)))
	my.M_updateEntry(name='loudness', 		value=np.zeros((1,10)))
	my.M_save('test.pyjama')
	
	with open('test.pyjama') as f: my=json.load(f)
	ipdb.set_trace()
	
# ==========================	
if __name__ == '__main__':
	#main(sys.argv[1:])
	#exampleBreakPoint(sys.argv[1:])
	exampleBreakPointTimeValue(sys.argv[1:])