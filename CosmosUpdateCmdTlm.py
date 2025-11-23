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
import argparse, json, os

# Column widths to ensure packets are readable
COLUMN_INDICES = [2, 20, 50, 60, 70, 80, 90, 100]

# Keys to parse and replace templates on
TARGET = '<<TARGET>>'
PACKET_NAME = '<<PACKET_NAME>>'
ENDIANNESS = '<<ENDIANNESS>>'
DESCRIPTION = '<<DESCRIPTION>>'
APID = '<<APID>>'
ADDITIONAL_FIELDS = '<<ADDITIONAL_FIELDS>>'
SIZE = '<<SIZE>>'

VALID_TYPES = ['UINT', 'INT', 'FLOAT', 'DOUBLE', 'CHAR']

TLM_CHECKSUM_STR = '  APPEND_ITEM      CRC                           16        UINT                "CRC16 checksum"\n'
CMD_CHECKSUM_STR = '  APPEND_PARAMETER CRC                           16        UINT      MIN       MAX       0         "CRC16 Checksum"\n'

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
            self._cmd_str += self.parseCommand(self._cmd_template, cmd)
            self._cmd_str += "\n"
        
        # Parse telemetry
        for tlm in self._cmd_tlm['tlm']:
            self._tlm_str += self.parseTelemetry(self._tlm_template, tlm)
            self._tlm_str += "\n"
        
        # Write both to file
        os.makedirs(self._cmd_out[:-7], exist_ok=True)
        with open(self._cmd_out, 'w') as file:
            file.write(self._cmd_str)
        os.makedirs(self._tlm_out[:-7], exist_ok=True)
        with open(self._tlm_out, 'w') as file:
            file.write(self._tlm_str)

    def parseTelemetry(self, template, dictval, append_key='APPEND_ITEM'):
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
        float_str = "    READ_CONVERSION half_float_conversion.py"
        pkt_str = template
        apid_num = dictval['apid']
        apid_num |= 0x800
        apid_str = str(apid_num)
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
                    (ftype, fsize, f16) = self.resolveField(field)
                    
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
                    if f16:
                        fields += float_str + '\n'
            else:
                field_str = ''
                
                # Write append key
                field_str += '  ' + append_key + ' '*(COLUMN_INDICES[1] - 3 - len(append_key))
                
                # Write name
                field_str += field['name']
                (ftype, fsize, f16) = self.resolveField(field)
                
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
                if f16:
                        fields += float_str + '\n'
            
        # Add our checksum
        fields += TLM_CHECKSUM_STR
            
        # And finally insert fields
        pkt_str = pkt_str.replace(ADDITIONAL_FIELDS, fields)
        
        return pkt_str

    def parseCommand(self, template, dictval, append_key='APPEND_PARAMETER'):
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
        apid_num = dictval['apid']
        apid_num |= 0x1800
        apid_str = str(apid_num)
        pkt_str = pkt_str.replace(APID, apid_str + ' '*(8 - len(apid_str)))
        pkt_str = pkt_str.replace(SIZE, str(dictval['size'] + 10) + ' '*(8 - len(str(dictval['size'] + 10))))
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
                    (ftype, fsize, f16) = self.resolveField(field)
                    
                    # Write size
                    field_str += ' '*(COLUMN_INDICES[2] - len(field_str) - 1)
                    field_str += fsize
                    
                    # Write type
                    field_str += ' '*(COLUMN_INDICES[3] - len(field_str) - 1)
                    field_str += ftype

                    # Write min
                    field_str += ' '*(COLUMN_INDICES[4] - len(field_str) - 1)
                    field_str += 'MIN'

                    # Write max
                    field_str += ' '*(COLUMN_INDICES[5] - len(field_str) - 1)
                    field_str += 'MAX'

                    # Write default
                    field_str += ' '*(COLUMN_INDICES[6] - len(field_str) - 1)
                    field_str += '0'
                    
                    # Write description
                    field_str += ' '*(COLUMN_INDICES[7] - len(field_str) - 1)
                    field_str += '" "'
                    
                    fields += field_str + '\n'
            else:
                field_str = ''
                
                # Write append key
                field_str += '  ' + append_key + ' '*(COLUMN_INDICES[1] - 3 - len(append_key))
                
                # Write name
                field_str += field['name']
                (ftype, fsize, f16) = self.resolveField(field)
                
                # Write size
                field_str += ' '*(COLUMN_INDICES[2] - len(field_str) - 1)
                field_str += fsize
                
                # Write type
                field_str += ' '*(COLUMN_INDICES[3] - len(field_str) - 1)
                field_str += ftype
                
                # Write min
                field_str += ' '*(COLUMN_INDICES[4] - len(field_str) - 1)
                field_str += 'MIN'

                # Write max
                field_str += ' '*(COLUMN_INDICES[5] - len(field_str) - 1)
                field_str += 'MAX'

                # Write default
                field_str += ' '*(COLUMN_INDICES[6] - len(field_str) - 1)
                field_str += '0'
                
                # Write description
                field_str += ' '*(COLUMN_INDICES[7] - len(field_str) - 1)
                field_str += '" "'
                
                fields += field_str + '\n'

        # Add our checksum
        fields += CMD_CHECKSUM_STR
            
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
        f16 = False
        
        # Identify field type. If it's not in our valid types will say 'INVALID'
        # but continue (maybe a person can fill it in)
        for tp in VALID_TYPES:
            if tp in field['type']:
                ftype = tp
                break
            elif 'BOOL' in field['type']:
                ftype = 'UINT'
                field['type'] = 'UINT8'
                break
            elif 'FLOATING_POINT' in field['type']:
                print('WARNING: TYPE ' + field['type'] + ' NOT RECOGNIZED. SETTING DEFAULT AS FLOAT')
                ftype = 'FLOAT'
                break
            elif 'FLOAT16' in field['type']:
                ftype = 'F16'
                f16 = True
                break
            
        # Identify field size, in bits. For ints this is easy. For float/double
        # it's a hardcode
        if 'UINT' in ftype:
            vals = field['type'].split('UINT')
            size = (vals[1].split('_'))[0]
        elif 'INT' in ftype:
            vals = field['type'].split('INT')
            size = (vals[1].split('_'))[0]
        elif 'F16' in ftype:
            size = '16'
            ftype = 'UINT'
        elif 'FLOAT' in ftype:
            size = '32'
        elif 'DOUBLE' in ftype:
            size = '64'
        elif 'CHAR' in ftype:
            size = '8'
        else:
            print('WARNING: TYPE ' + field['type'] + ' NOT RECOGNIZED. SETTING DEFAULTS')
            size = '0'
            
        return (ftype, size, f16)

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