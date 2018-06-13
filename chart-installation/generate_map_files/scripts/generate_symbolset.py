#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# by Will Kamp <manimaul!gmail.com>
# use this anyway you want

# Add Mapserver symbolset fil creation
# Simon Mercier

# python3 gen_symbolset.py [day|dark|dusk] [output_directory]
from __future__ import print_function

import argparse
import os
from subprocess import call
import xml.dom.minidom

from wand.image import Image

parser = argparse.ArgumentParser()
parser.add_argument('--update', '-u',
                    help='Update the symbol definition files',
                    action='store_true')
parser.add_argument('symbolset', help='Symbolset to generate',
                    choices=('day', 'dusk', 'dark'))
parser.add_argument('destination', help='Dataset destination folder')

args = parser.parse_args()

S57_FILES = (
    'rastersymbols-day.png', 'rastersymbols-dark.png',
    'rastersymbols-dusk.png', 'chartsymbols.xml',
)

url = "https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/"
if args.update or not all(os.path.exists(f) for f in S57_FILES):
    for f in S57_FILES:
        call(["wget", url + f, "-O", f])

symboltype = args.symbolset
output_directory = args.destination

if symboltype == "day":
    OCPN_source_symbol_file = "rastersymbols-day.png"
elif symboltype == "dark":
    OCPN_source_symbol_file = "rastersymbols-dark.png"
elif symboltype == "dusk":
    OCPN_source_symbol_file = "rastersymbols-dusk.png"

# Init variables
OCPN_lookuptable = "chartsymbols.xml"
symbolefile = "%s/symbols-%s.map" % (output_directory, symboltype)

# Create output directory
try:
    os.makedirs("%s/symbols-%s" % (output_directory, symboltype))
except os.error:
    pass

# our mapfile symbol template
symbol_template = """
SYMBOL
     NAME "[symname]"
     TYPE PIXMAP
     IMAGE "symbols-%s/[symname].png"
END""" % (symboltype)

f_symbols = open(symbolefile, "w")

f_symbols.write("SYMBOLSET\n")

dom = xml.dom.minidom.parse(OCPN_lookuptable)
with Image(filename=OCPN_source_symbol_file) as source_symbols:
    for symEle in dom.getElementsByTagName("symbol"):
        name = symEle.getElementsByTagName("name")[0].firstChild.nodeValue
        btmEle = symEle.getElementsByTagName("bitmap")
        if len(btmEle):
            locEle = btmEle[0].getElementsByTagName("graphics-location")
            width = int(btmEle[0].attributes["width"].value)
            height = int(btmEle[0].attributes["height"].value)
            x = locEle[0].attributes["x"].value
            y = locEle[0].attributes["y"].value
            print("creating: %s" % (name), end='\r', flush=True)
            # imagemagick to the rescue
            left = int(x)
            top = int(y)
            right = left + int(width)
            bottom = top + int(height)
            with source_symbols[left:right, top:bottom] as symbol:
                symbol_path = '{}/symbols-{}/{}.png'.format(output_directory,
                                                            symboltype,
                                                            name)
                symbol.save(filename=symbol_path)

            str_to_add = symbol_template.replace("[symname]", name)
            f_symbols.write(str_to_add)

# Include original symbols file
f_symbols.write("""

INCLUDE "symbols/symbols.sym"
""")

f_symbols.write("\nEND")
f_symbols.close()
