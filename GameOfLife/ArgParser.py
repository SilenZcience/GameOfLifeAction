import sys
import os
import argparse
from PIL.ImageColor import getcolor

def parseArgs() -> tuple:
    parser = argparse.ArgumentParser(
        description='Generate a Game-of-Life Image')

    parser.add_argument("-p", "-path", action="store", default=os.path.abspath(os.path.join(__file__,  '..')),
                        help="output folder", dest="path")
    parser.add_argument("-cdead", action="store", default="#FFFEFEFF,#141321FF",
                        help="the colors for dead cells, format: #light,#dark")
    parser.add_argument("-cdying", action="store", default="#28394AFF,#F7D747FF",
                        help="the colors for dying cells, format: #light,#dark")
    parser.add_argument("-calive", action="store", default="#41B782FF,#D83A7DFF",
                        help="the colors for alive cells, format: #light,#dark")
    parser.add_argument("-canvas", action="store", default="420,1200",
                        help="canvas size in pixel, format: height,width")
    parser.add_argument("-grid", action="store", default="84,240",
                        help="grid size in cells, format: vertical,horizontal")
    parser.add_argument("-gif", action="store", default="",
                        help="create a gif of 'gifLength' for a given image with the #light color-palette.")
    parser.add_argument("-gifLength", action="store", default=10, type=int,
                        help="set the amount of cycles for the gif-generator.")
    parser.add_argument("-gifSpeed", action="store", default=100, type=int,
                        help="set the gif speed(ms) for the gif-generator.")
    
    param = parser.parse_args()
    print(param)
    try:
        path = os.path.abspath(getattr(param, "path"))
    except:
        print("Invalid PATH! Please choose an existing folder.")
        sys.exit(1)
    if not os.path.exists(path):
        print("Invalid PATH! Please choose an existing folder.")
        sys.exit(1)
    try:
        cdead = getattr(param, "cdead").split(',')
        cdying = getattr(param, "cdying").split(',')
        calive = getattr(param, "calive").split(',')
        cdead = [*[getcolor(c, "RGBA") for c in cdead]]
        cdead += (cdead if len(cdead) == 1 else [])
        cdying = [*[getcolor(c, "RGBA") for c in cdying]]
        cdying += (cdying if len(cdying) == 1 else [])
        calive = [*[getcolor(c, "RGBA") for c in calive]]
        calive += (calive if len(calive) == 1 else [])
    except:
        print("The color parameters must be of the format: #light,#dark")
        print("e.g.: '#FFFEFEFF,#141321FF'")
        sys.exit(1)
    try:
        canvas = tuple([int(pix) for pix in getattr(param, "canvas").split(',')])
    except:
        print("The canvas parameter must be of the format: height,width")
        print("e.g.: '420,1200'")
        sys.exit(1)
    try:
        grid = tuple([int(pix) for pix in getattr(param, "grid").split(',')])
    except:
        print("The grid parameter must be of the format: vertical,horizontal")
        print("e.g.: '84,240'")
        sys.exit(1)
    try:
        gif = getattr(param, "gif")
        gif = os.path.abspath(gif) if gif else ''
        gifLength = getattr(param, "gifLength")
        gifSpeed = getattr(param, "gifSpeed")
    except:
        print("The gif parameter expects a PATH to an image")
        sys.exit(1)
    allowedExt = ['.BMP', '.JPEG', '.PNG', '.SPIDER', '.TIFF', '.GIF']
    if gif:
        if (cdead[0][3] != 255 or cdying[0][3] != 255 or calive[0][3] != 255):
            print("The gif cannot be created with alpha-values.")
            sys.exit(1)
        if not os.path.splitext(gif)[1].upper() in allowedExt:
            print("The given filetype is not supported!")
            print("Allowed filetypes are:")
            print(allowedExt)
            sys.exit(1)
    
    return (path, cdead, cdying, calive, canvas, grid, gif, gifLength, gifSpeed)