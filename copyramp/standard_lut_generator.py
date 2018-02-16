"""
* File Name : standard_lut_generator.py
* Creation Date : 28-09-2017
* Last Modified : Fri 29 Sep 2017 12:24:03 BST
* Created By : Matteo Barbiero
*
* Purpouse: standard and uniform LUT.xml board generator for AD9958 board.
* References:
"""

#libraries
import numpy  as np
import argparse as ap
import sys


#global variables
N_ELEMENT = 1000
N_AMP = 101
N_FREQ = 399


# start code


def main():
    parser = ap.ArgumentParser(usage="standard lut generation for AD9958")
    
    parser.add_argument("filename_lut",nargs=1, help="insert the lut filename" )    
    parser.add_argument("f0_ch1", nargs=1,help="start frequency channel 1 [MHz]", type=float)
    parser.add_argument("fn_ch1", nargs=1,help="stop frequency channel 1 [MHz]", type=float)
    parser.add_argument("f0_ch2", nargs=1,help="start frequency channel 2 [MHz]", type=float)
    parser.add_argument("fn_ch2", nargs=1,help="stop frequency channel 2 [MHz]", type=float)

    parser.add_argument("-lut0", nargs=2, default=[60.0, 60.0], 
            help="f1 and f2 in the n_lut=0 element [MHz]", type=float)
    
    args = parser.parse_args()
    

    if(N_ELEMENT==2.0*(N_AMP + N_FREQ)):
        create_xml_lut(args)
    else:
        raise SystemExit("ERROR: Dimension is not clear. N_ELEMENT is not 2x(N_ARG + N_FREQ)")    



def create_xml_lut(args): 
    
    filename = args.__dict__["filename_lut"] + ['.xml']
    filename = ''.join(filename)
    fp = open(filename ,'w')
    
    amp = np.linspace(0,1000,N_AMP)
    freq_ch1  = 1e6*np.linspace(args.__dict__["f0_ch1"], args.__dict__["fn_ch1"], N_FREQ)
    freq_ch2  = 1e6*np.linspace(args.__dict__["f0_ch2"], args.__dict__["fn_ch2"], N_FREQ)
    f0_header = 1e6*args.__dict__["lut0"][0]
    f1_header = 1e6*args.__dict__["lut0"][1]
    
    
    for i in range(N_ELEMENT+2):
	#header
	if(i==0):
	    string  = "<ad9958s>\n"
	    string += "\t<elem>0" 
	    string += "<ch0><fr>"+str(f0_header)+"</fr><am>1000</am><ph>0</ph></ch0>"
	    string += "<ch1><fr>"+str(f1_header)+"</fr><am>1000</am><ph>0</ph></ch1>"
	    string += "</elem>"

	#elements
	elif((i>0) and (i<= N_FREQ)):
	    j= i -1
	    string = "\t" + "<elem>" + str(i) + "<ch0><fr>"+str(freq_ch1[j])+"</fr></ch0></elem>"

	elif((i>N_FREQ) and (i<= N_FREQ + N_AMP)):
	    j = i - N_FREQ -1
	    string = "\t" + "<elem>" + str(i) + "<ch0><am>"+str(amp[j])+"</am></ch0></elem>"

	elif((i>N_FREQ+N_AMP) and (i<= N_FREQ*2 + N_AMP)):
	    j = i - (N_FREQ + N_AMP)  -1
	    string = "\t" + "<elem>" + str(i) + "<ch0><fr>"+str(freq_ch2[j])+"</fr></ch0></elem>"

	elif((i>N_FREQ) and (i<= N_FREQ*2 + N_AMP*2)):
	    j = i - (N_FREQ*2 + N_AMP) -1
	    string = "\t" + "<elem>" + str(i) + "<ch0><am>"+str(amp[j])+"</am></ch0></elem>"
	
	#end file
	elif(i==(N_ELEMENT +1)):
	    string = "</ad9958s>"
	    
	else:
            raise SystemExit("ERROR: LUT generation. index i exceed the N_ELEMENT+2")

        fp.write(string + "\n") 
    
    fp.close()


if __name__=="__main__":
    main()



