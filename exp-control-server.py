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
import sys
import Pyro4

from libraries.system import System

def main(args):
    # expose the class from the library using @expose as wrapper function:
    PyroSystem = Pyro4.expose(System)
    
#    daemon.register(ExposedClass)    # register the exposed class rather than the library class itself
#    
#                   # ------ normal code ------
#    daemon = Pyro4.Daemon()
#    uri = daemon.register(Thing)
#    print("uri=",uri)
#    daemon.requestLoop()
    # ------ alternatively, using serveSimple -----
    Pyro4.Daemon.serveSimple(
        {
            PyroSystem: "PyroSystem"
        },
        ns=True, verbose=True, host="yourhostname")

if __name__ == "__main__":
    main(sys.argv)
