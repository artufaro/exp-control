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

class FpgaBits(object):
    def __init__(self, bit_num, int_bits=None, bin_bits=None, hex_bits=None):
        self.bit_num = int(bit_num)
        self.bin_bits = None
        self.int_bits = None
        self.hex_bits = None

        if int_bits is not None and bin_bits is None and hex_bits is None:
            self._set_bits_int(int_bits)
        elif int_bits is None and bin_bits is not None and hex_bits is None:
            self._set_bits_bin(bin_bits)
        elif int_bits is None and bin_bits is None and hex_bits is not None:
            self._set_bits_hex(hex_bits)
        else:
            print "ERROR: wrong call to bit \"%s\""%str(type(self))

        if self.int_bits > 2**self.bit_num-1:
            print "ERROR: bit overflow for \"%s\" with string 0x%s"%(str(type(self)), self.hex_bits)

    def _set_bits_bin(self, bin_bits):
        self.int_bits = int(bin_bits, 2)
        self.bin_bits = bin(self.int_bits)[2:].zfill(self.bit_num)
        self.hex_bits = hex(self.int_bits)[2:].zfill(int(self.bit_num/4))

    def _set_bits_int(self, int_bits):
        self.int_bits = int(int_bits)
        self.bin_bits = bin(self.int_bits)[2:].zfill(self.bit_num)
        self.hex_bits = hex(self.int_bits)[2:].zfill(int(self.bit_num/4))

    def _set_bits_hex(self, hex_bits):
        self.int_bits = int(hex_bits, 16)
        self.bin_bits = bin(self.int_bits)[2:].zfill(self.bit_num)
        self.hex_bits = hex(self.int_bits)[2:].zfill(int(self.bit_num/4))

class DataLoadBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(DataLoadBits, self).__init__(16, int_bits, bin_bits, hex_bits)

class AddressLoadBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(AddressLoadBits, self).__init__(8, int_bits, bin_bits, hex_bits)

class TimeLoadBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(TimeLoadBits, self).__init__(32, int_bits, bin_bits, hex_bits)

class MemoryLoadBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(MemoryLoadBits, self).__init__(16, int_bits, bin_bits, hex_bits)

class CommandLoadBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(CommandLoadBits, self).__init__(8, int_bits, bin_bits, hex_bits)

class CommandBits(FpgaBits):
    def __init__(self, int_bits=None, bin_bits=None, hex_bits=None):
        super(CommandBits, self).__init__(8, int_bits, bin_bits, hex_bits)
