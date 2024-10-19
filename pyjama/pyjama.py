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
                    value, confidence, time, duration, start_freq, end_freq
                    Not all this keys are mandatory.
                To store a global (not time specific) description: simply use 'value' (use 'confidence' if you know how reliable is the 'value')
                To store a marker (with null duration, such as beat positions) description: simply use 'value' and 'time'
                To store a segment (such as speech segments in a file): simply use 'value', 'time' and 'duration'
                The keys 'start_freq' and 'end_freq' are used for Audiosculpt musicdescription xml compatibility.

        - 'descriptiondefinition' (which provides the definitions of the description provided for each entry)
            - Each description is defined by a dictionary with the following keys
                - 'type_extent': describes the temporal extent of the value {'global', 'marker', 'segment'}
                - 'type_content': describes the format of the value {'text', 'numeric'}
                - 'typeConstraint': describes whether a constraint has to be applied to validate a value  {'free', 'filepath, 'value_in_dictionary'}
                - 'dictionary': contains the list of possible values (when 'value_in_dictionary' is used)
                The following 'keys' are used for GUI purposes
                - 'is_table'
                - 'is_editable'
                - 'is_filter'

version 1.1
2017/03/08:	Added breakpoint support
        Format is
            time(nb_time): is a vecor
            value((nb_dim,nb_time)): is a matrix

version 1.2
2017/03/14: Following discussion with Diemo Schwarz and Benjamin Matuszewski:
        1) Update breakpoint format -> add column_name key to descriptiondefinition
        2) Add new type_extent 'breakpoint_time' and 'breakpoint_value' -> in order to be able to share time across descriptions
        Other proposals:
            - flip the dimensions of 'value' for breakpoint -> REJECTED: this would lead to a [[][][][][]] when storing a 1-dimensional breakpoint over time
            - change 'entry' with 'entries' -> REJECTED for backward compatibility

2017/03/24: Re-factoring the python code to follow pep8 writing style recommendations

2018/03/06: Added example of meanMfcc output

2024/03/05: Change compatibility to python 3 -> changed print
            Removed 'encoding' in json_dump
2024/10/19: Change orientation of data in breakpoint mode 
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


def F_backward_compatibility(entry):
    """
    to ensure backward compatibility: IF only one value THEN do not use list
    """
    #return entry

    if len(entry) == 1:
        if type(entry[0]) is not list:
            entry = entry[0]
    return entry


def F_numeric_input(numeric_l=[], 
                    check_vector=False, 
                    prefix='', 
                    field_name=''):
    """
    check and transform numerical value to list of float
    """

    if type(numeric_l) not in [float, list, np.ndarray]:
        raise Exception(f"{prefix} '{field_name}' must be float, list or np.ndarray")

    if isinstance(numeric_l, list):
        for numeric in numeric_l:
            if not isinstance(numeric, float):
                raise Exception(f"{prefix} all elements of '{field_name}' list must be float")


    if isinstance(numeric_l, float):
        numeric_l = [numeric_l]

    elif isinstance(numeric_l, np.ndarray):
        if check_vector:
            if numeric_l.ndim == 2:
                if (numeric_l.shape[0] > 1) and (numeric_l.shape[0] > 1):
                    raise Exception(f"{prefix} '{field_name}' cannot be a matrix")
                elif (numeric_l.shape[0] == 1) and (numeric_l.shape[0] > 1):
                    numeric_l = numeric_l[0, :]
                else:
                    numeric_l = numeric_l[:, 0]
            numeric_l = numeric_l.tolist()

    return numeric_l


def F_check_value_in_dictionary(value_l,
                                current_type_content,
                                dictionary,
                                not_valid_action):
    """
    """
    if isinstance(value_l, list):
        # --- flatten value: in case it is a list of list, it is changed to a list
        flatten_value_l = [item for sublist in value_l for item in sublist]
    else:
        flatten_value_l = [value_l]

    is_valid = True
    for value in flatten_value_l:

        if current_type_content == 'text':
            if value not in dictionary:
                if not_valid_action == 'add_to_dictionary':
                    print(f"'value'({value}) is not part of dictionary ->  updating dictionary")
                    dictionary.append(value)
                else:
                    is_valid = False

        elif current_type_content == 'numeric':
            min_value = dictionary[0]
            max_value = dictionary[1]
            if (value < min_value) or (max_value < value):
                if not_valid_action == 'add_to_dictionary':
                    if value < min_value:
                        dictionary[0] = value
                    if value > max_value:
                        dictionary[1] = value
            else:
                is_valid = False

    return is_valid, dictionary



class C_pyjama():
    """
    """

    data = {}
    current_position = -1
    not_valid_action = '' # ---- decide how to deal with values which are not in dictionary


    # ===============================================
    def __init__(self, not_valid_action='add_to_dictionary'):
        """
        """

        self.data['schemaversion'] = 1.4
        self.data['collection'] = {'descriptiondefinition': {}, 'entry': []}
        if not_valid_action in ['add_to_dictionary', 'filter_out', 'reject']:
            self.not_valid_action = not_valid_action
        else:
            raise Exception(f'Problem creating "pyjama" structure: unknown type "{not_valid_action}" for not_valid_action')


    # ===============================================
    def __setattr__(self, attr_name, attr_val):
        """
        """

        if hasattr(self, attr_name):
            self.__dict__[attr_name] = attr_val
        else:
            raise Exception(f"self.{attr_name} note part of the fields")


    # ===============================================
    def M_add_definition(self, 
                        description_name, 
                        type_constraint='free', 
                        type_content='text',
                        type_extent='global', 
                        #column_name=[],  # --- 2024/10/19
                        row_name=[], # --- 2024/10/19
                        generator={},
                        dictionary=[], 
                        is_table=True, 
                        is_editable=True,
                        is_filter=True):
        """
        """

        self.data['collection']['descriptiondefinition'][description_name] = collections.OrderedDict()

        if type_content in ['text', 'numeric']:
            self.data['collection']['descriptiondefinition'][description_name]['type_content'] = type_content
        else:
            raise Exception(f'unknown type "{type_content}" for type_content')

        if type_extent in ['global', 'segment', 'marker', 'breakpoint', 'breakpoint_time', 'breakpoint_value']:
            self.data['collection']['descriptiondefinition'][description_name]['type_extent'] = type_extent
        else:
            raise Exception(f'unknown type "{type_extent}" for type_extent')

        if type_constraint in ['filepath', 'free', 'value_in_dictionary']:
            self.data['collection']['descriptiondefinition'][description_name]['type_constraint'] = type_constraint
        else:
            raise Exception(f'unknown type "{type_constraint}" for type_constraint')

        self.data['collection']['descriptiondefinition'][description_name]['dictionary'] = copy.copy(dictionary)
        #self.data['collection']['descriptiondefinition'][description_name]['column_name'] = copy.copy(column_name) # --- 2024/10/19
        self.data['collection']['descriptiondefinition'][description_name]['row_name'] = copy.copy(row_name) # --- 2024/10/19
        self.data['collection']['descriptiondefinition'][description_name]['is_table'] = is_table
        self.data['collection']['descriptiondefinition'][description_name]['is_editable'] = is_editable
        self.data['collection']['descriptiondefinition'][description_name]['is_filter'] = is_filter
        if len(generator):
            self.data['collection']['descriptiondefinition'][description_name]['generator'] = generator


    # ===============================================
    def M_add_entry(self):
        """
        """

        entry = {}
        for description_name in self.data['collection']['descriptiondefinition'].keys():
            entry[description_name] = []
        self.data['collection']['entry'].append(entry)
        self.current_position += 1


    # ===============================================
    def M_update_entry(self, 
                        description_name,
                        value_l=[],
                        confidence_l=[],
                        time_l=[],
                        duration_l=[],
                        start_freq_l=[], 
                        end_freq_l=[], 
                        comment=''):
        """
        """
        prefix = f"ERROR updating self.data['collection']['entry'][{len(self.data['collection']['entry'])}]['{description_name}']:\n\t"

        if description_name not in self.data['collection']['descriptiondefinition'].keys():

            raise Exception(f"{prefix} '{description_name}' is not part of 'descriptiondefinition' -> add it first in 'descriptiondefinition'")

        else:

            current_type_extent = self.data['collection']['descriptiondefinition'][description_name]['type_extent']
            current_type_content = self.data['collection']['descriptiondefinition'][description_name]['type_content']
            current_type_constraint = self.data['collection']['descriptiondefinition'][description_name]['type_constraint']

            if current_type_extent in ['global', 'marker', 'segment', 'breakpoint', 'breakpoint_time', 'breakpoint_value']:
                # --- check VALUE

                if type(value_l) not in [str, int, float, list, np.ndarray]:
                    raise Exception(f"{prefix} 'value' must be str, int, float, list or np.ndarray")

                if type(value_l) in [str, float, int]:
                    value_l = [value_l]

                elif type(value_l) is np.ndarray:
                    if value_l.ndim != 2:
                        raise Exception(f"{prefix} IF 'value' is np.ndarray THEN it must be have value.ndim == 2")
                    # --- value (nb_dim, nb_time) -> [ [allDim(Time1)] [allDim(Time2)] [allDim(Time3)] [allDim(Time4)] ]
                    #value_l = value_l.T.tolist() # --- 2024/10/19
                    value_l = value_l.tolist() # --- 2024/10/19

                if current_type_extent in ['breakpoint', 'breakpoint_value']:
#                    nb_column_name = len(self.data['collection']['descriptiondefinition'][description_name]['column_name'])
#                    if len(value_l[0]) != nb_column_name:
#                        raise Exception("%s nb_dim of 'value' (%d) must be equal to nb_column_name' (%d)" % (prefix, len(value_l[0]), nb_column_name))
                    nb_row_name = len(self.data['collection']['descriptiondefinition'][description_name]['row_name'])
                    if len(value_l) != nb_row_name: # --- 2024/10/19
                        raise Exception(f"{prefix} nb_dim of 'value' ({len(value_l[0])}) must be equal to nb_row_name' ({nb_row_name})")

                if current_type_constraint == 'free':
                    is_valid = True

                elif current_type_constraint == 'filepath':
                    is_valid = True
                    for value in value_l:
                        if not(os.path.isfile(value)):
                            is_valid = False
                elif current_type_constraint == 'value_in_dictionary':
                    is_valid, dictionary = F_check_value_in_dictionary(value_l, current_type_content, self.data['collection']['descriptiondefinition'][description_name]['dictionary'], self.not_valid_action)



            if current_type_extent in ['marker', 'segment', 'breakpoint']:
                """ check TIME """

                time_l = F_numeric_input(numeric_l=time_l, check_vector=True, prefix=prefix, field_name='time')
                if len(time_l) > 1: # WASABI exception
                    #if len(time_l) != len(value_l): # --- 2024/10/19
#                        raise Exception(f"{prefix} len('time'): {len(time_l)} must be equal to len('value'): {len(value_l)}")
                    if len(time_l) != len(value_l[0]):
                        raise Exception(f"{prefix} len('time'): {len(time_l)} must be equal to len('value'): {len(value_l[0])}")



            if current_type_extent in ['segment']:
                """ check DURATION """

                duration_l = F_numeric_input(numeric_l=duration_l, check_vector=True, prefix=prefix, field_name='duration')

                if len(time_l) > 1: # WASABI exception
                    if len(time_l) != len(duration_l):
                        raise Exception(f"{prefix} len('time') must be equal to len('duration')")

            confidence_l = F_numeric_input(numeric_l=confidence_l, check_vector=True, prefix=prefix, field_name='confidence')
            start_freq_l = F_numeric_input(numeric_l=start_freq_l, check_vector=True, prefix=prefix, field_name='start_freq')
            end_freq_l = F_numeric_input(numeric_l=end_freq_l, check_vector=True, prefix=prefix, field_name='end_freq')

            if confidence_l:
                if time_l:
                    if len(time_l) != len(confidence_l):
                        raise Exception(f"{prefix} len('time') must be equal to len('confidence')")

            if start_freq_l:
                if time_l:
                    if len(time_l) != len(start_freq_l):
                        raise Exception(f"{prefix} len('time') must be equal to len('start_freq')")

            if end_freq_l:
                if time_l:
                    if len(time_l) != len(end_freq_l):
                        raise Exception(f"{prefix} len('time') must be equal to len('end_freq')")


            if current_type_extent == 'breakpoint_value':

                # --- Look for the name of the corresponding breakpoint_time
                # -- in descriptiondefinition
                time_name = ''
                for key in self.data['collection']['descriptiondefinition'].keys():
                    if self.data['collection']['descriptiondefinition'][key]['type_extent'] == 'breakpoint_time':
                        time_name = key

                if len(time_name) == 0:
                    raise Exception(f"{prefix} no 'breakpoint_time' has been defined in 'descriptiondefinition'")

                if time_name not in self.data['collection']['entry'][self.current_position].keys():
                    raise Exception(f"{prefix} no 'breakpoint_time' has been given for current entry")

                if len(self.data['collection']['entry'][self.current_position][time_name]) == 0:
                    raise Exception(f"{prefix} no 'breakpoint_time' has been given in current entry")

                time_v = self.data['collection']['entry'][self.current_position][time_name][0]['value']  # --- 2024/10/19
                nb_time = len(time_v[0])  # --- 2024/10/19
                if len(value_l[0]) != nb_time: # --- 2024/10/19
                    raise Exception(f"{prefix} number of rows of 'value' {len(value_l[0])} must be equal to number of 'time' {nb_time}")


            entry = {}

            if is_valid:
                if value_l:
                    value_l = F_backward_compatibility(value_l)
                    entry['value'] = value_l
                if time_l:
                    time_l = F_backward_compatibility(time_l)
                    entry['time'] = time_l
                if duration_l:
                    duration_l = F_backward_compatibility(duration_l)
                    entry['duration'] = duration_l
                if confidence_l:
                    confidence_l = F_backward_compatibility(confidence_l)
                    entry['confidence'] = confidence_l
                if start_freq_l:
                    start_freq_l = F_backward_compatibility(start_freq_l)
                    entry['start_freq'] = start_freq_l
                if end_freq_l:
                    end_freq_l = F_backward_compatibility(end_freq_l)
                    entry['end_freq'] = end_freq_l
                if comment:
                    entry['comment'] = comment

                self.data['collection']['entry'][self.current_position][description_name].append(entry)

            else:

                if self.not_valid_action == 'filter_out':
                    print(f"{prefix} 'value'({value}) is not part of dictionary -> filtering-out")
                else:
                    raise Exception(f"{prefix} 'value'({value}) is not part of the dictionary -> add it first in 'descriptiondefinition'")
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

        nb_entry = len(self.data['collection']['entry'])
        for num_entry in range(0, nb_entry):
            for key in key_l:
                if key not in self.data['collection']['entry'][num_entry].keys():
                    self.data['collection']['entry'][num_entry][key] = []
                    self.data['collection']['entry'][num_entry][key].append({'value': ''})
                elif len(self.data['collection']['entry'][num_entry][key]) == 0:
                    self.data['collection']['entry'][num_entry][key] = []
                    self.data['collection']['entry'][num_entry][key].append({'value': ''})
                elif 'value' not in self.data['collection']['entry'][num_entry][key][0].keys():
                    self.data['collection']['entry'][num_entry][key] = []
                    self.data['collection']['entry'][num_entry][key].append({'value': ''})

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
