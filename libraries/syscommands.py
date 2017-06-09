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

import threading

class SysCommand(object):
    def __init__(self, system):
        self._system = system
        self.running = False
        self._sleep_event = threading.Event()
        self._thread = None

    def sleep(self, time=100):
        if self.running:
            time = round(time)
            self._sleep_event.set()
            self._sleep_event = threading.Event()
            print "CMD: sleep for %.3fms"%time
            self._sleep_event.wait(time*self._system._time_multiplier)

    def wait_end(self, add_time=100):
        if self.running:
            time_sleep = self._system.get_time(self._system.get_program_time())+add_time
            print "CMD: wait the end of the program"
            self.sleep(time_sleep)

    def run(self, wait_end=True, add_time=100):
        if self.running:
            print "CMD: run program"
            self._system.set_program()
            valid = self._system.send_program_and_run()
            if not valid:
                print "CMD: ERROR while running program"
            if wait_end:
                self.wait_end(add_time=add_time)

    def load(self, prg_name=None):
        if self.running:
            if prg_name is None:
                print "CMD: load command must specify a program name"
            else:
                self._system.set_program(prg_name)
                print "CMD: load %s"%prg_name

    def stop(self):
        if self._thread is not None and self.running:
            self.running = False
            self._sleep_event.set()
            try:
                self._thread.join()
            except RuntimeError:
                pass
            self._thread = None
            print "CMD: stopped"

    def set_thread(self, thread):
        if self._thread is None:
            self._thread = thread

    def start(self):
        if self._thread is not None and not self.running:
            self.running = True
            print "CMD: started"
            if self._system.main_program is not None:
                action_name = self._system.main_program.name
                self._system.action_list.get_cmd(action_name) #questa è l'azione che esegue i commands
            self.running = False

    def get_var(self, name):
        if name not in self._system.variables.keys():
            self._system.variables[name] = 0
            print "WARNING: program variable \"%s\" not found in system, initialized with %d"%(name, self._system.variables[name])
        return self._system.variables[name]

    def set_var(self, name, value):
        self._system.variables[name] = value
        return value
