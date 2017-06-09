#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 08 10:21:57 2015

@author: simone
"""

VERBOSE = True

import csv
import os, sys
#change working path to the module one
#os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))


for fname in os.listdir("/home/stronzio/exp-control/copyramp"):
    if fname == "Evaporation Ramp.sub" and fname.endswith((".prg", ".sub")):
        with open("/home/stronzio/exp-control/copyramp/" + fname, "r") as fid:
            if VERBOSE:
                print "converting '%s'"%fname
            #if fname.endswith(".prg"):
            #    fname = "programs/"+fname
            #elif fname.endswith(".sub"):
            #    fname = "subroutines/"+fname

            program = """\
prg_comment = \"\"
PRG_VERSION = \"0.6\"
def program(prg, cmd):
"""

            reader = csv.reader(fid, delimiter="\t")
            for row_n, row in enumerate(reader):
                #count if columns are right
                if len(row) < 5:
                    print "ERROR: program format error in %s at row %d"%(os.path.basename(fname), row_n)
                    continue

                #time, action name, action disables
                time = int(float(row[0].replace(",", "."))*10000)
                action = row[1]
                enable = row[4] != "x"

                #uppercase breakpoint action
                if action == "breakpoint":
                    action = "BREAKPOINT"

                #remove comments from action name
                sign_chars = ["(+)", "(-)"]
                for sign_c in sign_chars:
                    if len(action.split(sign_c)) == 2:
                        action = action.split(sign_c)[0] + sign_c + action.split(sign_c)[1].split(" (")[0]
                    elif len(action.split(sign_c)) > 2:
                        print "ERROR: program format error in %s at row %d"%(os.path.basename(fname), row_n)
                if sign_chars[0] not in action and sign_chars[1] not in action:
                    action = action.split(" (")[0]

                #get the parameter value, convert it into float or int as needed
                if row[2] != "":
					value = int(row_n)
                    #if "," in row[2]:
                    #    value = float(row[2].replace(",", "."))
                    #else:
                    #    value = int(row[2])
                else:
                    value = None

                #print time, action
                program += "    prg.add(%d, \"%s\""%(time, action.strip())
                #print value, enable
                if value is not None:
                    if type(value) == int:
                        program += ", %d"%(value)
                    elif type(value) == float:
                        program += ", %f"%(value)
                    else:
                        print "ERROR: program format error in %s at row %d"%(os.path.basename(fname), row_n)
                if enable is False:
                    program += ", enable=False"
                program += ")\n"

        program += "    return prg\n"

        fname = fname + ".py"
        #fname = os.path.join("data", "programs", "subroutines", fname)
        directory = "/home/stronzio/exp-control/data/programs/subroutines"
        
        #check if save directory exist or create it
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, fname), "w") as fid:
            print os.path.join(directory, fname)
            fid.write(program)
