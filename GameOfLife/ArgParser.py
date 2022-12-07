import sys
import os
import argparse
from PIL.ImageColor import getcolor

def parseArgs():
    parser = argparse.ArgumentParser(
        description='Generate a Game-of-Life Image')

    parser.add_argument("-p", "-path", action="store", default=[os.path.abspath(os.path.join(__file__,  '..'))],
                        nargs=1, help="output folder", dest="path")
    parser.add_argument("-cdead", action="store", default=["#FFFEFEFF,#141321FF"],
                        nargs=1, help="the colors for dead cells, format: #light,#dark")
    parser.add_argument("-cdying", action="store", default=["#28394AFF,#F7D747FF"],
                        nargs=1, help="the colors for dying cells, format: #light,#dark")
    parser.add_argument("-calive", action="store", default=["#41B782FF,#D83A7DFF"],
                        nargs=1, help="the colors for alive cells, format: #light,#dark")
    parser.add_argument("-canvas", action="store", default=["420,1200"],
                        nargs=1, help="canvas size in pixel, format: height,width")
    parser.add_argument("-grid", action="store", default=["84,240"],
                        nargs=1, help="grid size in cells, format: vertical,horizontal")

    param = parser.parse_args()
    print(param)
    try:
        path = os.path.abspath(getattr(param, "path")[0])
    except:
        print("Invalid PATH! Please choose an existing folder.")
        sys.exit(1)
    if not os.path.exists(path):
        print("Invalid PATH! Please choose an existing folder.")
        sys.exit(1)

    cdead = cdying = calive = canvas = grid = ""
    try:
        cdead = getattr(param, "cdead")[0].split(',')
        cdying = getattr(param, "cdying")[0].split(',')
        calive = getattr(param, "calive")[0].split(',')
        cdead = [*[getcolor(c, "RGBA") for c in cdead]]
        cdying = [*[getcolor(c, "RGBA") for c in cdying]]
        calive = [*[getcolor(c, "RGBA") for c in calive]]
    except:
        print("The color parameters must be of the format: #light,#dark")
        print("e.g.: '#FFFEFEFF,#141321FF'")
        sys.exit(1)
    try:
        canvas = tuple([int(pix) for pix in getattr(param, "canvas")[0].split(',')])
    except:
        print("The canvas parameter must be of the format: height,width")
        print("e.g.: '420,1200'")
        sys.exit(1)
    try:
        grid = tuple([int(pix) for pix in getattr(param, "grid")[0].split(',')])
    except:
        print("The grid parameter must be of the format: vertical,horizontal")
        print("e.g.: '84,240'")
        sys.exit(1)

    return (path, cdead, cdying, calive, canvas, grid)