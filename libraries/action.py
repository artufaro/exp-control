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

import board as lib_board

class Action(object):
    def __init__(self, system, name, comment=""):
        self.command_bits = None
        self.name = str(name)
        self.comment = str(comment)
        self.system = system

    def do_action(self):
        pass

class DataAction(Action):
    def __init__(self, system, board, name="", comment=""):
        super(DataAction, self).__init__(system, name, comment)

        if not isinstance(board, lib_board.Board):
            print "WARNING: action \"%s\" does not specify a valid board"%self.name
        self.board = board
        self.command_bits = 0b00000000

class DigitalAction(DataAction):
    def __init__(self, system, board, channel=None, status=None, name="", comment=""):
        super(DigitalAction, self).__init__(system, board, name, comment)

        if type(channel) is not list:
            channel = [channel]
        if type(status) is not list:
            status = [status]

        self.channel = []
        self.status = []
        if len(channel) == len(status):
            for chn in channel:
                self.channel.append(int(chn))
            for stt in status:
                self.status.append(bool(stt))
        else:
            print "ERROR: digital action \"%s\" does not have corrinspondence between channels and states"%self.name

    def do_action(self):
        data = 0
        if len(self.status) == 0:
            print "WARNING: digital action \"%s\" does not specify any channel, data is initialized to %d"%(self.name, data)

        for ch_st in zip(self.channel, self.status):
            data = self.board.set_status(ch_st[0], ch_st[1])
        return data

class DigitalThresholdAction(DataAction):
    def __init__(self, system, board, channel=None, status=None, threshold=None, name="", comment=""):
        super(DigitalThresholdAction, self).__init__(system, board, name, comment)

        if type(channel) is not list:
            channel = [channel]
        if type(status) is not list:
            status = [status]
        if type(threshold) is not list:
            threshold = [threshold]

        self.channel = []
        self.status = []      
        # Mannaia la miseria
        self.threshold = [] #[float(thr) if thr is not None else None for thr in threshold]

        if len(channel) == len(status):
            for chn in channel:
                self.channel.append(int(chn))
            for stt in status:
                self.status.append(stt)
            for thr in threshold:
                if thr is not None:
                    self.threshold.append(float(thr))
                else:
                    self.threshold.append(None)
        else:
            print "ERROR: digital action \"%s\" does not have corrinspondence between channels and states"%self.name

    def do_action(self):
        data = 0
        if len(self.status) == 0:
            print "WARNING: digital action \"%s\" does not specify any channel, data is initialized to %d"%(self.name, data)

        for ch_st in zip(self.channel, self.status, self.threshold):
            data = self.board.set_status(ch_st[0], ch_st[1], ch_st[2])
        return data

class DdsAction(DataAction):
    def __init__(self, system, board,
                 channel=None, amplitude=None, frequency=None, n_lut=None,
                 realtime=False, trigger=False, read_data=True,
                 name="", comment=""):
        super(DdsAction, self).__init__(system, board, name, comment)

        if channel is not None:
            channel = int(channel)
        self.channel = channel

        if amplitude is not None:
            amplitude = float(amplitude)
        self.amplitude = amplitude

        if frequency is not None:
            frequency = float(frequency)
        self.frequency = frequency

        if n_lut is not None:
            n_lut = int(n_lut)
        self.n_lut = n_lut

        self.realtime = bool(realtime)
        self.trigger = bool(trigger)
        self.read_data = bool(read_data)

    def do_action(self):
        if self.amplitude is not None and \
                self.frequency is None and self.n_lut is None:
            data = self.board.set_amplitude(self.channel, self.amplitude)
        elif self.amplitude is None and \
                self.frequency is not None and self.n_lut is None:
            data = self.board.set_frequency(self.channel, self.frequency)
        elif self.amplitude is None and \
                self.frequency is None and self.n_lut is not None:
            data = self.board.set_lut(self.n_lut)
        else:
            data = 0
            print "WARNING: call to DDS action \"%s\" is not implemented, data is initialized to %d"%(self.name, data)

        if self.board.model == "AD9958" and self.board.firmware == "S":
            if data > 0b0000001111111111:
                data = 0
                print "ERROR: data in DDS action \"%s\" is out of range, data is initialized to %d"%(self.name, data)
            if not self.realtime:
                data += 0b0000010000000000 #TODO: check if it works
            if self.trigger:
                data += 0b1000000000000000 #TODO: check if data is needed in these cases
            if self.read_data:
                data += 0b0100000000000000
        else:
            print "ERROR: DDS action \"%s\" is not completed since DDS model \"%s\" with firmware \"%s\" is not implemented"%(self.name, self.board.model, self.board.firmware)

        return data

class AnalogAction(DataAction):
    def __init__(self, system, board, value=None, bipolar=True, name="", comment=""):
        super(AnalogAction, self).__init__(system, board, name, comment)

        if value is not None:
            value = float(value)
        self.value = value

        self.bipolar = bool(bipolar)

    def do_action(self):
        if self.value is not None:
            data = self.board.set_value(self.value)
        else:
            data = 0
            print "WARNING: call to analog action \"%s\" is not implemented, data is initialized to %d"%(self.name, data)

        if self.bipolar:
            #TODO: check two's complement
            data = data&(2**self.board.dac_bits-1)
        else:
            #TODO: limit max also here
            pass

        if data > (2**self.board.dac_bits-1):
            data = (2**self.board.dac_bits-1)
            print "ERROR: data in analog action \"%s\" is out of range, data is initialized to %d"%(self.name, data)

        return data

###### FIXME: the address of the (fake) board associated with these actions cannot be the same as a true board
###### Fixed: in board.py a None address is translated into the highest possible value (2**8 - 1)

class EmptyAction(Action):
    def __init__(self, system, name="EMPTY"):
        super(EmptyAction, self).__init__(system, name)
        self.command_bits = 0b00000000
        self.board = lib_board.Board(None)

    def do_action(self):
        return 0

class NopAction(Action):
    def __init__(self, system, name="NOP"):
        super(NopAction, self).__init__(system, name)
        self.command_bits = 0b00100000
        self.board = lib_board.Board(None)

    def do_action(self):
        return 0

class BreakpointAction(Action):
    def __init__(self, system, name="BREAKPOINT"):
        super(BreakpointAction, self).__init__(system, name)
        self.command_bits = 0b00010000
        self.board = lib_board.Board(None)

    def do_action(self):
        return 0

class EndAction(Action):
    def __init__(self, system, name="END"):
        super(EndAction, self).__init__(system, name)
        self.command_bits = 0b10000000
        self.board = lib_board.Board(None)

    def do_action(self):
        return 0

class ForAction(Action):
    #TODO: implement
    pass
