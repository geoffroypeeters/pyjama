# Documentation pyjama format
### Author: geoffroy.peeters@telecom-paris.fr
#### Date: 2024/10/16

# Introduction

.pyjama (*) is a file format based on JSON developed to store music annotations.
A single file allows to store the annotations that correspond to ALL items of a dataset.
The file is also self described:
- one part is about defining the annotations that will be used,
- the second part is about using those to describe all items of the dataset.

.pyjama was developed independently of [`JAMS`](https://github.com/marl/jams), and comes from an an evolution of the .xml definition of `mpeg-7-audio` or the .xml definition of `music-description` developed by ircam.

(*) pyjama stands for python json audio music annotation; It is the protective layer that safeguards your data while it rests on a hard drive.


The top level of the file distingishes
- `schemaversion`: the version of the pyjama specification
- `collection`: the content itself

```python
{
    "schemaversion": 1.31,
    "collection": {
                  ...
                  }
```

The level below `collection` distinguishes
- `descriptiondefinition`: the definition of the annotations that will be used,
- `entry`: the use of the defined annotations to describe all items of the dataset.

`entry` is a list.
Each element of this list describes a single item.

```python
{
    "schemaversion": 1.31,
		"collection": {
        "descriptiondefinition": {
                                  ...
                                  }
        "entry": [
                  {
			$descriptionName: [descriptionAtom , descriptionAtom],
			$descriptionName: [descriptionAtom],
                  },
                  {
			$descriptionName: [descriptionAtom, descriptionAtom, descriptionAtom, descriptionAtom],
			$descriptionName: [descriptionAtom],
                  }
                  ]
```

This single element (single `entry`) is a dictionary, a set of (`key`,`value`)

# descriptionName

Each `key` of this dictionary refers to a specific `descriptionName` (or annotation-type).
In the example below, the `descriptionName` are `filepath`, `structure`, `genre`, `tempo`, `title`, ...

The `value` associated to a `descriptionName` (or annotation-type) is a list of `descriptionAtom`.
The use of a list allows to have several `descriptionAtom` associated to a given `descriptionName` (or annotation-type).

In the example below, when `descriptionName` is `structure`, we have several segments over time defining the music structre. Each segment is defined as a `descriptionAtom` with its `time`,`duration`,`value` field.
We could also have several `genre` associated to the item (multi-label, each one with a `confidence`).


# descriptionAtom

The content of a single `descriptionAtom` is defined in the `descriptiondefinition` part of the .pyjama file.
In the example above,
- the `descriptionName` `structure` is defined as  {"typeContent": "text" and "typeExtent": "segment"} and its `descriptionAtom` has therefore the fields `value`/`time`/`duration`.
- the `descriptionName` `genre` is defined as {"typeContent": "text", "typeExtent": "global"} ans its `descriptionAtom` has therefore only the field `value`.


Example of dummy entry:
```python
"entry": [
            {
                "filepath": [
                    {
                        "value": "Isophonics_01 A Kind Of Magic.mp3"
                    }
                ],
                "structure": [
                    {
                        "value": "silence",
                        "time": 0.0,
                        "duration": 1.09
                    },
                    {
                        "value": "intro",
                        "time": 1.09,
                        "duration": 25.758
                    }
                    ]
                "genre": [
                    {
                        "value": "blues"
                    }
                    ],
                "tempo": [
                    {
                        "value": 125.87
                    }
                    ]
                "title": [
                    {
                        "value": "Come On Let's Go"
                    }
                ],
                "performer": [
                    {
                        "value": "Broadcast"
                    }
                ],
                "release-date": [
                    {
                        "value": "March 20, 2000"
                    }
                ],
}
```

# Description definition

The full description of a `descriptionAtom` contains

```python
{
  'typeExtent':       'global' | 'marker' | 'segment' | 'breakpoint' | 'breakpointTime' | 'breakpointValue'
  'typeContent':      'text' | 'numeric'
  'typeConstraint':   'free' | 'filePath' | 'valueInDictionary'
  'dictionary':       if 'typeContent'=='text'    then 'dictionary' =  [string, string]
                      if 'typeContent'=='numeric' then 'dictionary' =  [minFloatValue, maxFlatValue]
  'columnName':       [string, string, string]
  'generator':
}
```

Depending on the `typeExtent` value, the following validation are performed file:

| typeExtent | Action |
| --- | --- |
| if `typeExtent`==`marker` 				| then `time` must be defined |
| if `typeExtent`==`segment` 				| then both `time`and `duration` must be defined |
| if `typeContent`==`breakpoint`			| then `value`must be a matrix |


The maximum content associated to a `descriptionAtom` is

```python
{
	'value':                 text or float (nbDim, nbTime)
	'confidence':
	'time':                  float-scalar or (nbTime, 1)
	'duration':
	'comment':
}
```

Depending on the `typeConstraint` value, the following validation are performed file:

| typeConstraint | Action |
| --- | --- |
| if `typeConstraint`==`free` 			| then `value` can be whatever you want |
| if `typeConstraint`==`filePath` 		| then `value` must contains a file that exist  |
| if `typeConstraint`==`valueInDictionary`	| then `value` must be included in `dictionary`  |



## Format for storing breakPoint

Storing breakpoint function, i.e. a set of (mono or multi-dimensional) values over time (such as f0 values over time, of multi-f0 values over time) can be done efficiently using the `breakpoint` type.

We consider that the data to be stored is given as a matrix of dimensions (nbTime,nbDim).

In `descriptiondefinition`, we should specify
- `columnName`: indicate the name of the various dimension (such as `f0_midi_violin`, `f0_midi_clarinet`, ... in the example below).
	- len(columnName) = nbDim

For mono-dimensional description, we have the following `key` in `descriptionAtom`
- `time`: 
	- shape: (nbTime,)
	- json: [ time1, time2, time3 ]
- `value`: 
	- shape: (nbTime, 1)
	- json: [ [dimension1(time1)], [dimension1(time2)], [dimension1(time3)]] ]

For multi-dimensional description, we have the following `key` in `descriptionAtom`
- `time`: 
	- shape: (nbTime,)
	- json: [ time1, time2, time3 ]
- `value`: 
	- shape: (nbTime, nbDim)
	- json: [ [dimension1(time1), dimension2(time1), dimension3(time1)], [dimension1(time2), dimension2(time2), dimension3(time2)] ]

For global but multi-dimensional description, we have the following `key` in `descriptionAtom`
- `value`: 
	- shape: (1, nbDim)
	- json: [ [dimension1, dimension2, dimension3 ] ]

It should be noted that `value` is always stored as a matrix.



Example of dummy multi-f0 file:
```python
 "collection": {
    "descriptiondefinition": {
      "f0multi": {
                "typeContent": "numeric",
                "typeExtent": "breakpoint",
                "typeConstraint": "free",
                "dictionary": [],
                "columnName": [
                    "f0_midi_violin",
                    "f0_midi_clarinet",
                    "f0_midi_saxphone",
                    "f0_midi_bassoon"
                ],
                "isTable": true,
                "isEditable": true,
                "isFilter": true
            }
    }
```

# Examples

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

## Example of multi-label tagging

TODO

## Example of marker annotations (beat)

TODO

## Example of break-point values 1

TODO
## Example of break-point values 2

TODO

## Example of global multi-dimensional descriptor

TODO

	
