#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Copyright (C) 2017 Carmelo Mordini
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from subprocess import call
from xml.etree import cElementTree as ET

ACT_NAME = 'Evaporation'
SUB_NAME = 'Evaporation Ramp.sub'

DDS_PATH = "copyramp"
WRITETABLE = os.path.join(DDS_PATH, 'exec_writetable')

class EvaporationRampGen(object):
    def __init__(self, system):
        self.system = system
        self.act_name = ACT_NAME
        self.sub_name = SUB_NAME
        self.act_dict = self.system.action_list.get_dict(self.act_name).copy()
        self.sub_dict = self.system.action_list.get_dict(self.sub_name).copy()
        
    def build_prg_list(self, times,):
        prg_list = []
        for j, t in enumerate(times):
            d0 = self.act_dict.copy()
            d0['time'] = self.system.set_time(t)
            d0['vars'] = {'n_lut': j}
            prg_list.append(d0)
        return prg_list
    
    def write_prg(self, prg_list):
        self.system.parser.write_program_file(
#                prg_name='Evaporation Ramp new writer',# for testing purpose
                prg_name=self.sub_name,
                prg_list=prg_list,
                categories=self.sub_dict['categories'],
                prg_comment=self.sub_dict['comment'],
                cmd_str=self.sub_dict['cmd'],)
        
    def build_xml_list(self, freqs, amps):
        dds = ET.Element("ad9958s")
        xml_list = []
        for j, (f, a) in enumerate(zip(freqs*1e6, amps)):
            elem = ET.SubElement(dds, 'elem')
            elem.text = str(j)
            ch0 = ET.SubElement(elem, 'ch0')
            ET.SubElement(ch0, 'fr').text = '{:.3f}'.format(f)
            ET.SubElement(ch0, 'am').text = '{:.0f}'.format(a)
            xml_list.append(ET.tostring(elem).decode('ascii'))
        return xml_list
    
    def write_xml(self, xml_list):
        xml_name = os.path.join(DDS_PATH, self.act_name + '.xml')
        print("writing '%s'"%xml_name)
        with open(xml_name, 'w') as f:
            f.write('<?xml version="1.0" encoding="iso-8859-1"?>\n')
            f.write('<ad9958s>\n')
            for e in xml_list:
                f.write('  '+ e +'\n')
            f.write('</ad9958s>')
        return xml_name
        
        
    def write_out(self, times, freqs, amps): #writes subroutine, .xml, and copyramp on the DDS
        print('Writing subroutine')
        prg = self.build_prg_list(times)
        self.write_prg(prg)
        print('Writing xml')
        xml = self.build_xml_list(freqs, amps)
        #path, xml_name = os.path.split(self.write_xml(xml))
        xml_name = self.write_xml(xml)
        call('sh ./%s -w %s'%(WRITETABLE, xml_name), shell=True)
#        print('Verifying xml')        
#        call('sh ./%s -v %s'%(WRITETABLE, xml_name), shell=True)
        pass
