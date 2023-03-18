import sys
import os
import argparse
from PIL.ImageColor import getcolor


class Settings():
    def __init__(self) -> None:
        self.path: str = ''
        self.cdead: list = []
        self.cdying: list = []
        self.calive: list = []
        self.canvas: tuple = None
        self.grid: tuple = None
        self.gif: str = ''
        self.gifLength: int = 0
        self.gifSpeed: int = 0
        self.fromTransition: str = ''
        self.toTransition: str = ''


settings = Settings()


def parseArgs() -> None:
    parser = argparse.ArgumentParser(
        description='Generate a Game-of-Life Image')

    parser.add_argument("-p", "-path", action="store", default=os.path.abspath(os.path.join(__file__,  '..')),
                        help="specify output folder", dest="path")
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
                        help="create a gif of 'gifLength' for a given image with the #light color-palette")
    parser.add_argument("-gifLength", action="store", default=10, type=int,
                        help="set the amount of frames for the gif")
    parser.add_argument("-gifSpeed", action="store", default=100, type=int,
                        help="set the gif speed in ms")
    parser.add_argument("-from", action="store", default="", 
                        help="make a transition from this file")
    parser.add_argument("-to", action="store", default="", 
                        help="make a transition to this file")
    
    param = parser.parse_args()
    print(param)
    allowedExt = ['.BMP', '.JPEG', '.PNG', '.SPIDER', '.TIFF', '.GIF']
    
    try:
        settings.path = os.path.abspath(getattr(param, "path"))
        if not os.path.exists(settings.path):
            raise ValueError
    except:
        print("Invalid PATH! Please choose an existing folder")
        sys.exit(1)
    try:
        cdead = getattr(param, "cdead").split(',')
        cdying = getattr(param, "cdying").split(',')
        calive = getattr(param, "calive").split(',')
        settings.cdead = [*[getcolor(c, "RGBA") for c in cdead]]
        settings.cdead += (cdead if len(cdead) == 1 else [])
        settings.cdying = [*[getcolor(c, "RGBA") for c in cdying]]
        settings.cdying += (cdying if len(cdying) == 1 else [])
        settings.calive = [*[getcolor(c, "RGBA") for c in calive]]
        settings.calive += (calive if len(calive) == 1 else [])
    except:
        print("The color parameters must be of the format: #light,#dark")
        print("e.g.: '#FFFEFEFF,#141321FF'")
        sys.exit(1)
    try:
        settings.canvas = tuple([int(pix) for pix in getattr(param, "canvas").split(',')])
    except:
        print("The canvas parameter must be of the format: height,width")
        print("e.g.: '420,1200'")
        sys.exit(1)
    try:
        settings.grid = tuple([int(pix) for pix in getattr(param, "grid").split(',')])
    except:
        print("The grid parameter must be of the format: vertical,horizontal")
        print("e.g.: '84,240'")
        sys.exit(1)
    try:
        gif = getattr(param, "gif")
        settings.gif = os.path.abspath(gif) if gif else ''
        settings.gifLength = getattr(param, "gifLength")
        settings.gifSpeed = getattr(param, "gifSpeed")
        if gif and not os.path.exists(settings.gif):
            raise ValueError
    except:
        print("The gif parameter expects a PATH to an image")
        sys.exit(1)
    if gif:
        if not os.path.splitext(settings.gif)[1].upper() in allowedExt:
            print("The given filetype is not supported!")
            print("Allowed filetypes are:")
            print(allowedExt)
            sys.exit(1)
    try:
        fromTransition = getattr(param, 'from')
        toTransition = getattr(param, 'to')
        if bool(fromTransition) != bool(toTransition):
            raise ValueError
    except:
        print("When creating a transition, you need to specify from AND to")
        sys.exit(1)
    try:
        settings.fromTransition = os.path.abspath(fromTransition) if fromTransition else ''
        settings.toTransition = os.path.abspath(toTransition) if toTransition else ''
        if fromTransition and toTransition:
            if not os.path.exists(settings.fromTransition) or not os.path.exists(settings.toTransition):
                raise ValueError
    except:
        print("The from and to parameters expect PATHs to an image")
        sys.exit(1)
    if fromTransition and toTransition:
        if not os.path.splitext(settings.fromTransition)[1].upper() in allowedExt or not os.path.splitext(settings.toTransition)[1].upper() in allowedExt:
            print("The given filetype is not supported!")
            print("Allowed filetypes are:")
            print(allowedExt)
            sys.exit(1)
    if gif or (fromTransition and toTransition):
        if (settings.cdead[0][3] != 255 or settings.cdying[0][3] != 255 or settings.calive[0][3] != 255):
            print("The gif cannot be created with alpha-values.")
            sys.exit(1)
