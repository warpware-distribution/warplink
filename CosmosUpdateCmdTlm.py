#!/usr/bin/env python3 
###############################################################################
# Copyright (c) ATTX LLC 2024. All Rights Reserved.
#
# This software and associated documentation (the "Software") are the 
# proprietary and confidential information of ATTX, LLC. The Software is 
# furnished under a license agreement between ATTX and the user organization 
# and may be used or copied only in accordance with the terms of the agreement.
# Refer to 'license/attx_license.adoc' for standard license terms.
#
# EXPORT CONTROL NOTICE: THIS SOFTWARE MAY INCLUDE CONTENT CONTROLLED UNDER THE
# INTERNATIONAL TRAFFIC IN ARMS REGULATIONS (ITAR) OR THE EXPORT ADMINISTRATION 
# REGULATIONS (EAR99). No part of the Software may be used, reproduced, or 
# transmitted in any form or by any means, for any purpose, without the express 
# written permission of ATTX, LLC.
###############################################################################
import argparse, json

# Column widths to ensure packets are readable
COLUMN_INDICES = [2, 20, 50, 60, 70, 80]

# Keys to parse and replace templates on
TARGET = '<<TARGET>>'
PACKET_NAME = '<<PACKET_NAME>>'
ENDIANNESS = '<<ENDIANNESS>>'
DESCRIPTION = '<<DESCRIPTION>>'
APID = '<<APID>>'
ADDITIONAL_FIELDS = '<<ADDITIONAL_FIELDS>>'

VALID_TYPES = ['UINT', 'INT', 'FLOAT', 'DOUBLE', 'CHAR']

CHECKSUM_STR = '  APPEND_ITEM      CRC                           16        UINT                "CRC16 checksum"\n'

class CosmosUpdateCmdTlm():
    """
    Generate cosmos cmd/tlm files from cFS++ cmd/tlm json
    
    Params
        cmd_tlm_json: The command/telemetry json output from cFS++
        tlm_template: Template for telemetry creation
        cmd_template: Template for command creation
        cmd_out: Output command file name
        tlm_out: Output telemetry file name
    """
    def __init__(self, cmd_tlm_json, 
                 tlm_template, cmd_template, 
                 cmd_out, tlm_out):
        
        # Load our cmd_tlm json
        self._cmd_tlm = {}
        with open(cmd_tlm_json, 'r') as file:
            self._cmd_tlm = json.load(file)
            
        # Load our templates
        with open(tlm_template, 'r') as file:
            self._tlm_template = file.read()
        with open(cmd_template, 'r') as file:
            self._cmd_template = file.read()
            
        # Set our out files
        self._cmd_out = cmd_out
        self._tlm_out = tlm_out

    def __call__(self):
        """
        Run the end to end build system to generate our telemetry packets
        """
        # Build strings for command and telemetry files
        self._cmd_str = ""
        self._tlm_str = ""
        
        # Parse commands
        for cmd in self._cmd_tlm['cmd']:
            self._cmd_str += self.parsePacket(self._cmd_template, cmd, 'APPEND_PAREMETER')
            self._cmd_str += "\n"
        
        # Parse telemetry
        for tlm in self._cmd_tlm['tlm']:
            self._tlm_str += self.parsePacket(self._tlm_template, tlm, 'APPEND_ITEM')
            self._tlm_str += "\n"
        
        # Write both to file
        with open(self._cmd_out, 'w') as file:
            file.write(self._cmd_str)
        with open(self._tlm_out, 'w') as file:
            file.write(self._tlm_str)

    def parsePacket(self, template, dictval, append_key):
        """
        Receive a single dictionary with telemetry packet info and parse
        into output format for cosmos

        Args:
            template (str): String with file template
            dictval (dict): Dictionary containing cmd/tlm info
            append_key (str): String indicating additional tlm packet
        """
        # Find and replace information keys in our template with
        # packet information
        pkt_str = template
        apid_str = str(dictval['apid'])
        pkt_str = pkt_str.replace(APID, apid_str + ' '*(8 - len(apid_str)))
        pkt_str = pkt_str.replace(TARGET, 'CFSPP')
        pkt_str = pkt_str.replace(PACKET_NAME, dictval['name'])
        pkt_str = pkt_str.replace(ENDIANNESS, 'BIG_ENDIAN')
        pkt_str = pkt_str.replace(DESCRIPTION, ' ')
        
        # Loop through each field in the telemetry and add it
        fields = ''
        for field in dictval['fields']:
            flen = field['size']
            if type(flen) is str:
                flen = int(flen)
            if flen:
                for i in range(flen):
                    field_str = ''
                    # Write append key
                    field_str += '  ' + append_key + ' '*(COLUMN_INDICES[1] - 3 - len(append_key))
                    
                    # Write name
                    field_str += field['name'] + '_' + str(i)
                    (ftype, fsize) = self.resolveField(field)
                    
                    # Write size
                    field_str += ' '*(COLUMN_INDICES[2] - len(field_str) - 1)
                    field_str += fsize
                    
                    # Write type
                    field_str += ' '*(COLUMN_INDICES[3] - len(field_str) - 1)
                    field_str += ftype
                    
                    # Write description
                    field_str += ' '*(COLUMN_INDICES[5] - len(field_str) - 1)
                    field_str += '" "'
                    
                    fields += field_str + '\n'
            else:
                field_str = ''
                
                # Write append key
                field_str += '  ' + append_key + ' '*(COLUMN_INDICES[1] - 3 - len(append_key))
                
                # Write name
                field_str += field['name']
                (ftype, fsize) = self.resolveField(field)
                
                # Write size
                field_str += ' '*(COLUMN_INDICES[2] - len(field_str) - 1)
                field_str += fsize
                
                # Write type
                field_str += ' '*(COLUMN_INDICES[3] - len(field_str) - 1)
                field_str += ftype
                
                # Write description
                field_str += ' '*(COLUMN_INDICES[5] - len(field_str) - 1)
                field_str += '" "'
                
                fields += field_str + '\n'
            
        # Add our checksum
        fields += CHECKSUM_STR
            
        # And finally insert fields
        pkt_str = pkt_str.replace(ADDITIONAL_FIELDS, fields)
        
        return pkt_str
    
    def resolveField(self, field):
        """
        Resolve field data into a cmd/tlm line

        Args:
            field (dict): Dictionary containing information on field
            
        Return:
            Tuple with field type, field size
        """
        ftype = 'INVALID'
        size = 0
        
        # Identify field type. If it's not in our valid types will say 'INVALID'
        # but continue (maybe a person can fill it in)
        for tp in VALID_TYPES:
            if tp in field['type']:
                ftype = tp
                break
            
        # Identify field size, in bits. For ints this is easy. For float/double
        # it's a hardcode
        if 'UINT' in ftype:
            vals = field['type'].split('UINT')
            size = (vals[1].split('_'))[0]
        elif 'INT' in ftype:
            vals = field['type'].split('INT')
            size = (vals[1].split('_'))[0]
        elif 'FLOAT' in ftype:
            size = '32'
        elif 'DOUBLE' in ftype:
            size = '64'
        elif 'CHAR' in ftype:
            size = '8'
        else:
            print('WARNING: TYPE ' + field['type'] + ' NOT RECOGNIZED. SETTING DEFAULTS')
            size = '0'
            
        return (ftype, size)

if __name__ == "__main__":
    # Create our argument parser
    parser = argparse.ArgumentParser(prog='Build pre-processor')
    
    # Add our arguments for input
    parser.add_argument('--cmd-tlm-json', default='./cmd_tlm.json')
    parser.add_argument('--tlm-template', default='templates/telemetry.txt')
    parser.add_argument('--cmd-template', default='templates/command.txt')
    parser.add_argument('--tlm-out', default='./openc3-cosmos-cfspp/targets/CFSPP/cmd_tlm/tlm.txt')
    parser.add_argument('--cmd-out', default='./openc3-cosmos-cfspp/targets/CFSPP/cmd_tlm/cmd.txt')
    args = parser.parse_args()
    
    bp = CosmosUpdateCmdTlm(args.cmd_tlm_json, 
                            args.tlm_template, 
                            args.cmd_template,
                            args.cmd_out,
                            args.tlm_out)
    bp()