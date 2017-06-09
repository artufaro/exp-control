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

import pylibftdi
import time
import command as lib_command

class Fpga(object):
    def __init__(self, device_index=0):
        self.device_index = int(device_index)
        self.device = pylibftdi.Device(device_index=device_index,
                                       interface_select=pylibftdi.INTERFACE_B)
        self.device.baudrate = 115200

    def send_commands(self, hex_cmd_string):
        hex_cmd_string = str(hex_cmd_string)

        valid = False
        if len(hex_cmd_string)%2 != 0:
            print "ERROR: commands are not well formatted, length of the hex string must be even (%d instead)"%len(hex_cmd_string)
        else:
            comm_encoded = ""
            n_bytes = int(len(hex_cmd_string)/2)
            for n_b in range(n_bytes):
                comm_encoded += chr(int(hex_cmd_string[n_b*2:n_b*2+2], 16))

            try:
                self.device.flush()
                self.device.write(comm_encoded)
                valid = True
            except pylibftdi.FtdiError:
                print "ERROR: FPGA not found, reload the list"
        return valid

    def send_program_and_run(self, commands):
        cmd_str = ""
        for cmd in commands:
            cmd_str += cmd.get_hex()

        valid1 = valid2 = self.send_commands(cmd_str)
        if valid1:
            #fill the FPGA FIFO
            time.sleep(0.05)
            valid2 = self.send_commands(lib_command.RunCommand().get_hex())
        return valid1 and valid2

    def get_status(self):
        valid = self.send_commands(lib_command.StatusCommand().get_hex())

        renspose = ""
        n_iter = 0
        while renspose == "":
            if n_iter > 100:
                print "WARNING: FPGA is not rensponding to status request"
                renspose = chr(0)
                break
            try:
                renspose = self.device.read(6)
            except pylibftdi.FtdiError:
                if valid:
                    print "ERROR: FPGA not found, reload the list"
                renspose = chr(0)
            n_iter += 1

        return FpgaStatus(renspose.encode("hex"))

class FpgaStatus(object):
    def __init__(self, hex_str):
        self.hex_str = str(hex_str)

        n_bits = 6*8
        bin_str = bin(int(self.hex_str, 16))[2:].zfill(n_bits)
        self.valid_prg = bin_str[7] == "1"
        self.ext_trigger = bin_str[6] == "1"
        self.soft_trigger = bin_str[5] == "1"
        self.running = bin_str[4] == "1"

    def __repr__(self):
        out_str = "Valid program loaded: " + str(self.valid_prg)
        out_str += "\nExternal trigger activated: " + str(self.ext_trigger)
        out_str += "\nTrigger received: " + str(self.soft_trigger)
        out_str += "\nRunning: " + str(self.running)
        return out_str
