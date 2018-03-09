# Documentation pyjama format
### Author: peeters@ircam.fr
#### Date: 2018/03/06

# Introduction

`pyjama`is a JSON format for storing the descriptions of entries belonging to a collection of entries.
While usual description-format aims at storing the description of a single entry, the goal is here to store the descriptions of all entries of a collection.
It is also a self-defined format since it includes a `descriptiondefinition` part which goal is to define the `description`used.

The `pyjama` specifications are based on
- IRCAM `musicdescription` XML format 
- Brian McFee JAM format

# Global structure:

### descriptionAtom

	{
		'value':			text or float (nbDim, nbTime)
		'confidence':
		'time':			float-scalar or (nbTime, 1)
		'duration':
		'comment':
		'startFreq':
		'endFreq'
	}

- A `descriptionAtom ` is the basis unit for describing data
- It is a `dictionary`


### descriptionContent

	[ 
		$descriptionAtom, 
		$descriptionAtom, 
		$descriptionAtom 
	] 

- A `description` groups the set of `descriptionAtom` related to the same `descriptionName`
- It is a `list` (since the same `descriptionName` can potentially have several values)
- **Example**: to store several chord segments over time or several genres associated to a track) 

### entry (could also have been named allDescriptions)

	{
		$descriptionName: $descriptionContent,
		$descriptionName: $descriptionContent
	}

- An `entry` groups the set of `descriptionName`/`descriptionContent ` related to a file
- It is a dictionary (in order to avoid having twice the same `descriptionName`)
- **Example**: store the various description associated to an entry


### allEntries
					
	[
		$entry,
		$entry
	]

- A `allEntries` stores the various `entry` of a collection
- It is a list


### descriptionDefinitionAtom

	{
		'typeExtent':		'global' | 'marker' | 'segment' | 'breakpoint' | 'breakpointTime' | 'breakpointValue'
		'typeContent':		'text' | 'numeric'
		'typeConstraint':	'free' | 'filePath' | 'valueInDictionary'
		'dictionary':		if 'typeContent'=='text'    then 'dictionary' =  [string, string] 
							if 'typeContent'=='numeric' then 'dictionary' =  [minFloatValue, maxFlatValue]
		'columnName':		[string, sring, string]
		'generator':			
		'isTable':			true | false
		'isFilter':			true | false
		'isEditable':		true | false
	}

- A `descriptionDefinitionAtom` stores the definition related to a `descriptionName`
- It is a dictionay

### allDescriptionDefinitions

	{
		$descriptionName: $descriptionDefinitionAtom,
		$descriptionName: $descriptionDefinitionAtom
	}


### all
			
	{
	    "schemaversion": 1.2, 
	    "collection": 
	    		{
				'entry': $allEntries
				'descriptiondefinition': $allDescriptionDefinitions
			}
	}



# Validity checking


| aaa | aaa |
| --- | --- |
| if `typeConstraint`==`free` 			| then `value` can be whatever you want |
| if `typeConstraint`==`filePath` 		| then `value` must contains a file that exist  |
| if `typeConstraint`==`valueInDictionary`	| then `value` must be included in `dictionary`  |
| if `typeExtent`==`marker` 				| then `time` must be defined |
| if `typeExtent`==`segment` 				| then both `time`and `duration` must be defined |
| if `typeContent`==`breakpoint`			| then `value`must be a matrix |

# Format for storing breakPoint

- 'columnName':
	- len(columnName) = nbDim

- 'time': 
	- python: time.shape -> (nbTime,)
	- json: [ time1, time2, time3 ]
- 'value': 
	- python: value.shape -> (nbDim, nbTime)
	- json: [ [dimension1(time1), dimension1(time2), dimension1(time3)], [dimension2(time1), dimension2(time2), dimension2(time3)] ]

For global but multi-dimensional description

- 'value': 
	- python: value.shape (nbDim, 1)
	- json: [ [dimension1], [dimension2] ]

'value' is always a matrix


------------------------
time 
- float
- list of float
- 


# Examples

## Example of multi-label tagging

## Example of segment annotations (structure)

	{
	    "schemaversion": 1.2, 
	    "collection": {
	        "entry": [
	            {
	                "structtype": [
	                    {
	                        "duration": 0.223492063, 
	                        "value": "Silence", 
	                        "time": 0.0
	                    }, 
	                    {
	                        "duration": 52.938730158999995, 
	                        "value": "A", 
	                        "time": 0.223492063
	                    }, 
	                    {
	                        "duration": 39.658231291999996, 
	                        "value": "B", 
	                        "time": 53.162222222
	                    }
	                ], 
	                "filepath": [
	                    {
	                        "value": "/Users/peeters/_work/_sound/_collection/local_structure/2014_Salami/_audio/10/audio.mp3"
	                    }
	                ]
	            }, 
	            {
	                "structtype": [
	                    {
	                        "duration": 0.946938775, 
	                        "value": "Silence", 
	                        "time": 0.0
	                    }, 
	                    {
	                        "duration": 142.584648526, 
	                        "value": "A", 
	                        "time": 0.946938775
	                    }, 
	                    {
	                        "duration": 4.301360544000005, 
	                        "value": "Silence", 
	                        "time": 143.531587301
	                    }
	                ], 
	                "filepath": [
	                    {
	                        "value": "/Users/peeters/_work/_sound/_collection/local_structure/2014_Salami/_audio/100/audio.mp3"
	                    }
	                ]
	            }
	        ], 
	        "descriptiondefinition": {
	            "structtype": {
	                "typeContent": "text", 
	                "typeExtent": "segment", 
	                "typeConstraint": "valueInDictionary", 
	                "dictionary": [
	                    "Silence", 
	                    "A", 
	                    "B", 
	                    "C", 
	                    "D", 
	                    "E", 
	                    "F", 
	                    "I", 
	                    "V", 
	                    "End"
	                ], 
	                "columnName": [], 
	                "isTable": true, 
	                "isEditable": true, 
	                "isFilter": true, 
	                "generator": {
	                    "date": "", 
	                    "version": "", 
	                    "name": ""
	                }
	            }, 
	            "filepath": {
	                "typeContent": "text", 
	                "typeExtent": "global", 
	                "typeConstraint": "filePath", 
	                "dictionary": [], 
	                "columnName": [], 
	                "isTable": true, 
	                "isEditable": true, 
	                "isFilter": true
	            }
	        }
	    }
	}

## Example of marker annotations (beat)

## Example of break-point values 1

## Example of break-point values 2

## Example of global multi-dimensional descriptor

	