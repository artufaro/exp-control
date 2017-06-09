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

class Board(object):
    def __init__(self, address, name="", comment=""):
        if address is not None:    
            self.address = int(address)
        else:
            self.address = int(2**8 -1)
        self.name = str(name)
        self.comment = str(comment)

class DigitalBoard(Board):
    def __init__(self, address, tot_ch=16, name="", comment=""):
        super(DigitalBoard, self).__init__(address, name, comment)
        self.channels = dict()
        for chn in range(tot_ch):
            self.channels[chn+1] = {"state": False}

    def set_status(self, channel, status, threshold=None):
        if channel is not None:
            channel = int(channel)
            if self.channels.has_key(channel):
#                print channel, status, threshold
                if threshold is not None:
                    self.channels[channel]["state"] = bool(float(status)>threshold)
                else:
                    self.channels[channel]["state"] = bool(status)
            else:
                print "ERROR: wrong channel selection in Digital board \"%s\", valid channels are %s"%(self.name, str(self.channels.keys()))
        else:
            channels = self.channels.keys()
            for chn in channels:
                self.channels[chn]["state"] = bool(status)

        string_bin = ""
        channels = self.channels.keys()
        channels.sort(reverse=True)
        for chn in channels:
            if self.channels[chn]["state"]:
                string_bin += "1"
            else:
                string_bin += "0"

        return int(string_bin, 2)

class AnalogBoard(Board):
    def __init__(self, address, ang_to_dig, dac_bits=16, name="", comment=""):
        super(AnalogBoard, self).__init__(address, name, comment)
        self.value = None
        self.ang_to_dig = ang_to_dig[1]
        self.dac_bits = int(dac_bits)

    def set_value(self, value):
        value = float(value)
        self.value = value
        data = int(self.ang_to_dig(value))
        return data

class DdsBoard(Board):
    def __init__(self, address,
                 amp_to_lut, freq_to_lut,
                 tot_ch=2, model="AD9958", firmware="S",
                 name="", comment=""):
        super(DdsBoard, self).__init__(address, name, comment)
        self.channels = dict()
        self.amp_to_lut = amp_to_lut
        self.freq_to_lut = freq_to_lut
        self.model = str(model)
        self.firmware = str(firmware)

        for chn in range(tot_ch):
            self.channels[chn+1] = {"freq": None, "amp": None}
        self.channels["lut_n"] = None

    def set_amplitude(self, channel, amplitude):
        channel = int(channel)
        amplitude = float(amplitude)
        self.channels[channel]["amp"] = amplitude
        lut_n = self.amp_to_lut[channel](amplitude)
        return self.set_lut(lut_n)

    def set_frequency(self, channel, frequency):
        channel = int(channel)
        frequency = float(frequency)
        self.channels[channel]["freq"] = frequency
        lut_n = self.freq_to_lut[channel](frequency)
        return self.set_lut(lut_n)

    def set_lut(self, lut_n):
        lut_n = int(lut_n)
        self.channels["lut_n"] = lut_n
        return lut_n
