#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2016  Simone Donadello
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

#pylint: disable-msg=E1101

import bit as lib_bit

class FpgaCommand(object):
    def __init__(self, cmd):
        cmd = str(cmd)
        if not cmd.startswith("0x"):
            print "ERROR: wrong call to command \"%s\" with string \"%s\""%(str(type(self)), cmd)
        self.bits = [lib_bit.CommandBits(hex_bits=cmd)]

    def get_hex(self):
        hex_str = ""
        for bit in self.bits:
            hex_str += bit.hex_bits
        return hex_str

    def get_bin(self):
        bin_str = ""
        for bit in self.bits:
            bin_str += bit.bin_bits
        return bin_str

class LoadCommand(FpgaCommand):
    def __init__(self, memory, command, time, address, data):
        super(LoadCommand, self).__init__("0x02")
        self.bits.append(lib_bit.MemoryLoadBits(int_bits=int(memory)))
        self.bits.append(lib_bit.CommandLoadBits(int_bits=int(command)))
        self.bits.append(lib_bit.TimeLoadBits(int_bits=int(time)))
        self.bits.append(lib_bit.AddressLoadBits(int_bits=int(address)))
        self.bits.append(lib_bit.DataLoadBits(int_bits=int(data)))

class LoadDoneCommand(FpgaCommand):
    def __init__(self):
        super(LoadDoneCommand, self).__init__("0x04")

class RunCommand(FpgaCommand):
    def __init__(self):
        super(RunCommand, self).__init__("0x0B")

class StopCommand(FpgaCommand):
    def __init__(self):
        super(StopCommand, self).__init__("0x0A")

class StatusCommand(FpgaCommand):
    def __init__(self):
        super(StatusCommand, self).__init__("0x08")

class ExtTriggerOnCommand(FpgaCommand):
    def __init__(self):
        super(ExtTriggerOnCommand, self).__init__("0x07")

class ExtTriggerOffCommand(FpgaCommand):
    def __init__(self):
        super(ExtTriggerOffCommand, self).__init__("0x06")
