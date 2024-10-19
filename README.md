# Documentation pyjama format
### Author: geoffroy.peeters@telecom-paris.fr
#### Date: 2024/10/19

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
    "schemaversion": 1.4,
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
    "schemaversion": 1.4,
		"collection": {
        "descriptiondefinition": {
                                  ...
                                  }
        "entry": [
                  {
			$description_name: [description_atom , description_atom],
			$description_name: [description_atom],
                  },
                  {
			$description_name: [description_atom, description_atom, description_atom, description_atom],
			$description_name: [description_atom],
                  }
                  ]
```

This single element (single `entry`) is a dictionary, a set of (`key`,`value`)

# description_name

Each `key` of this dictionary refers to a specific `description_name` (or annotation-type).
In the example below, the `description_name` are `filepath`, `structure`, `genre`, `tempo`, `title`, ...

The `value` associated to a `description_name` (or annotation-type) is a list of `description_atom`.
The use of a list allows to have several `description_atom` associated to a given `description_name` (or annotation-type).

In the example below, when `description_name` is `structure`, we have several segments over time defining the music structre. Each segment is defined as a `description_atom` with its `time`,`duration`,`value` field.
We could also have several `genre` associated to the item (multi-label, each one with a `confidence`).


# description_atom

The content of a single `description_atom` is defined in the `descriptiondefinition` part of the .pyjama file.
In the example above,
- the `description_name` `structure` is defined as  {"typeContent": "text" and "typeExtent": "segment"} and its `description_atom` has therefore the fields `value`/`time`/`duration`.
- the `description_name` `genre` is defined as {"typeContent": "text", "typeExtent": "global"} ans its `description_atom` has therefore only the field `value`.


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

The full description of a `description_atom` contains

```python
{
  'type_extent':       'global' | 'marker' | 'segment' | 'breakpoint' | 'breakpointTime' | 'breakpointValue'
  'type_content':      'text' | 'numeric'
  'type_constraint':   'free' | 'filepath' | 'value_in_dictionary'
  'dictionary':       if 'type_content'=='text'    then 'dictionary' =  [string, string]
                      if 'type_content'=='numeric' then 'dictionary' =  [minFloatValue, maxFlatValue]
  'row_name':       [string, string, string]
  'generator':
}
```

Depending on the `typeExtent` value, the following validation are performed file:

| typeExtent | Action |
| --- | --- |
| if `type_extent`==`marker` 				| then `time` must be defined |
| if `type_extent`==`segment` 				| then both `time`and `duration` must be defined |
| if `type_content`==`breakpoint`			| then `value`must be a matrix |


The maximum content associated to a `description_atom` is

```python
{
	'value':                 text or float (nbDim, nbTime)
	'confidence':
	'time':                  float-scalar or (nbTime, 1)
	'duration':
	'comment':
}
```

Depending on the `type_constraint` value, the following validation are performed file:

| typeConstraint | Action |
| --- | --- |
| if `type_constraint`==`free` 			| then `value` can be whatever you want |
| if `type_constraint`==`filepath` 		| then `value` must contains a file that exist  |
| if `type_constraint`==`value_in_dictionary`	| then `value` must be included in `dictionary`  |



## Format for storing breakPoint

Storing breakpoint function, i.e. a set of (mono or multi-dimensional) values over time (such as f0 values over time, of multi-f0 values over time) can be done efficiently using the `breakpoint` type.

We consider that the data to be stored is given as a matrix of dimensions (nbTime,nbDim).

In `descriptiondefinition`, we should specify
- `row_name`: indicate the name of the various dimension (such as `f0_midi_violin`, `f0_midi_clarinet`, ... in the example below).
	- len(row_name) = nb_dim

For mono-dimensional description, we have the following `key` in `description_atom`
- `time`: 
	- shape: (nbTime,)
	- json: [ time1, time2, time3 ]
- `value`: 
	- shape: (1, nbTime)
	- json: [ [dimension1(time1), dimension1(time2), dimension1(time3)] ]

For multi-dimensional description, we have the following `key` in `description_atom`
- `time`: 
	- shape: (nbTime,)
	- json: [ time1, time2, time3 ]
- `value`: 
	- shape: (nbDim, nbTime)
	- json: [ [dimension1(time1), dimension1(time2), dimension1(time3)], [dimension2(time1), dimension2(time2), dimension2(time3)] ]

For global but multi-dimensional description, we have the following `key` in `description_atom`
- `value`: 
	- shape: (1, nbDim)
	- json: [ [dimension1], [dimension2], [dimension3] ] ]

It should be noted that `value` is always stored as a matrix.



Example of dummy multi-f0 file:
```python
 "collection": {
    "descriptiondefinition": {
      "f0multi": {
                "type_content": "numeric",
                "type_extent": "breakpoint",
                "type_constraint": "free",
                "dictionary": [],
                "row_name": [
                    "f0_midi_violin",
                    "f0_midi_clarinet",
                    "f0_midi_saxphone",
                    "f0_midi_bassoon"
                ],
                "is_table": true,
                "is_editable": true,
                "is_filter": true
            }
    }
```

