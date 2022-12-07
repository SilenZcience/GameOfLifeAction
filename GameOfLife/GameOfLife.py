import os
import sys
import argparse
import numpy as np
from PIL import Image
from PIL.ImageColor import getcolor


def tracelog(*args):
    print("TraceLog:", *args)


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
    tracelog(param)
    try:
        path = os.path.abspath(getattr(param, "path")[0])
    except:
        tracelog("Invalid PATH! Please choose an existing folder.")
        sys.exit(1)
    if not os.path.exists(path):
        tracelog("Invalid PATH! Please choose an existing folder.")
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
        tracelog("The color parameters must be of the format: #light,#dark")
        tracelog("e.g.: '#FFFEFEFF,#141321FF'")
        sys.exit(1)
    try:
        canvas = tuple([int(pix) for pix in getattr(param, "canvas")[0].split(',')])
    except:
        tracelog("The canvas parameter must be of the format: height,width")
        tracelog("e.g.: '420,1200'")
        sys.exit(1)
    try:
        grid = tuple([int(pix) for pix in getattr(param, "grid")[0].split(',')])
    except:
        tracelog("The grid parameter must be of the format: vertical,horizontal")
        tracelog("e.g.: '84,240'")
        sys.exit(1)

    return (path, cdead, cdying, calive, canvas, grid)


workingDir, color_dead, color_dying, color_alive, canvas_size, cell_grid = parseArgs()


cell_size = [canvas_size[0]/cell_grid[0],
             canvas_size[1]/cell_grid[1]]
for i, size in enumerate(cell_size):
    if not size.is_integer():
        cell_size[i] += 1
    cell_size[i] = int(cell_size[i])


target_images = [os.path.join(workingDir, 'GameOfLifeBright.png'),
                 os.path.join(workingDir, 'GameOfLifeDark.png')]
target_iteration_images = [os.path.join(workingDir, 'IterationBright.svg'),
                           os.path.join(workingDir, 'IterationDark.svg')]


def IterationImageContent(r, g, b, *args):
    hexColor = '#{:02x}{:02x}{:02x}'.format(r, g, b)
    IterationImageContent = '''
    <svg fill="none" viewBox="0 0 345 20" width="345px" height="20px"
    xmlns="http://www.w3.org/2000/svg">
    <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml">
        <style>

            .wrapper {
                text-align: center;
                width: 345px;
                height: 20px
            }

            h1 {
                background: ''' + hexColor + ''';
                color: #fff;
                font-size: 10px;
                position: center;
                font-weight: 500;
                font-family: "Josefin Sans", sans-serif;
                background-size: 200% auto;
                background-clip: text;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
            }

        </style>

            <div class="wrapper">
            <h1>Current Iteration: 0</h1>
            </div>

        </div>
    </foreignObject>
    </svg>
    '''
    return IterationImageContent


def updateGame(cells):
    """Calculate the next cycle of cells, aswell
    as the cycle after that, to flag the cells,
    which are about to die."""
    nextArray = np.zeros(cell_grid, dtype=np.int8)

    for row, col in np.ndindex(cells.shape):
        num_alive = np.sum(cells[row-1:row+2, col-1:col+2]) - cells[row, col]

        if (cells[row, col] == 1 and 2 <= num_alive <= 3) or (cells[row, col] == 0 and num_alive == 3):
            nextArray[row, col] = 1

    cells = nextArray.copy()
    for row, col in np.ndindex(nextArray.shape):
        num_alive = np.sum(
            nextArray[row-1:row+2, col-1:col+2]) - nextArray[row, col]

        if nextArray[row, col] == 1 and (num_alive < 2 or num_alive > 3):
            cells[row, col] = 2

    return cells


def generateImage(cells, dark):
    newArray = np.zeros([canvas_size[0], canvas_size[1], 4], dtype=np.int8)

    for row, col in np.ndindex(cells.shape):
        if cells[row, col] == 0:
            newArray[row * cell_size[0]:(row+1) * cell_size[0], col *
                     cell_size[1]:(col+1) * cell_size[1]] = color_dead[dark]
        elif cells[row, col] == 1:
            newArray[row * cell_size[0]:(row+1) * cell_size[0], col *
                     cell_size[1]:(col+1) * cell_size[1]] = color_alive[dark]
        elif cells[row, col] == 2:
            newArray[row * cell_size[0]:(row+1) * cell_size[0], col *
                     cell_size[1]:(col+1) * cell_size[1]] = color_dying[dark]

    return Image.fromarray(newArray.astype('uint8'))


def initRunningGame(imageFile, dark):
    image = Image.open(imageFile)
    currentColorArray = np.array(image)
    currentColorArray = currentColorArray[::cell_size[0], ::cell_size[1]]
    currentArray = np.zeros([currentColorArray.shape[0], currentColorArray.shape[1]], dtype=np.int8)

    for row, col in np.ndindex(currentArray.shape):
        if np.array_equal(currentColorArray[row, col], color_dead[dark]):
            currentArray[row:(row+1), col:(col+1)] = 0
        elif np.array_equal(currentColorArray[row, col], color_alive[dark]):
            currentArray[row:(row+1), col:(col+1)] = 1
        elif np.array_equal(currentColorArray[row, col], color_dying[dark]):
            currentArray[row:(row+1), col:(col+1)] = 1

    return (currentArray, image)


def initNewGame():
    # testGame = np.zeros(cell_grid, dtype=np.int8) # Cell Grid should be >= 19x19

    # Still-lifes
    # a[2:4,2:4] = 1 # Block

    # a[1:2,2:4] = 1
    # a[2:3,1:2] = 1
    # a[2:3,4:5] = 1
    # a[3:4,2:4] = 1 # Bee-Hive

    # Oscillators
    # a[2:4,2:4] = 1
    # a[3:4,1:2] = 1
    # a[2:3,4:5] = 1 # Toad

    # a[2:5,2:3] = 1 # Blinker

    # a[1:3,1:3] = 1
    # a[3:5,3:5] = 1 # Beacon

    # a[2:3,4:7] = 1
    # a[2:3,10:13] = 1
    # a[4:7,2:3] = 1
    # a[4:7,7:8] = 1
    # a[4:7,9:10] = 1
    # a[4:7,14:15] = 1
    # a[7:8,4:7] = 1
    # a[7:8,10:13] = 1
    # a[9:10,4:7] = 1
    # a[9:10,10:13] = 1
    # a[10:13,2:3] = 1
    # a[10:13,7:8] = 1
    # a[10:13,9:10] = 1
    # a[10:13,14:15] = 1
    # a[14:15,4:7] = 1
    # a[14:15, 10:13] = 1 # Pulsar

    # Spaceships
    # a[2:3, 1:2] = 1
    # a[3:4, 2:3] = 1
    # a[1:4, 3:4] = 1 # Glider

    # return testGame
    return np.random.randint(0, 2, cell_grid, dtype=np.int8)


def startNewGame(target_image, dark):
    cells = initNewGame()
    image = generateImage(cells, dark)
    image.save(target_image)


def updateIteration(imageFile, dark, increment):
    if not os.path.exists(imageFile):
        with open(imageFile, 'w', encoding="utf-8") as image:
            image.write(IterationImageContent(*color_alive[dark]))
        return
    fileContent = headerContent = ""
    currentIteration = 0
    try:
        with open(imageFile, 'r', encoding="utf-8") as image:
            fileContent = image.read()
            headerContent = fileContent[fileContent.find("<h1>") + 4:fileContent.find("</h1>")]
    except:
        return

    newHeaderContent = ""
    if increment:
        headerIteration = ""
        for char in headerContent[::-1]:
            if not char.isnumeric():
                break
            headerIteration += char
        currentIteration = int(headerIteration[::-1]) + 1

    newHeaderContent = "Current Iteration: {}".format(currentIteration)

    try:
        with open(imageFile, 'w', encoding="utf-8") as image:
            image.write(fileContent.replace(headerContent, newHeaderContent))
    except:
        return


def main():
    for i, target_image in enumerate(target_images):
        if os.path.exists(target_image):
            try:
                tracelog("reading game state...")
                cells, currentImage = initRunningGame(target_image, i)
                tracelog("updating game cycle...")
                cells = updateGame(cells)
                tracelog("generating new image...")
                image = generateImage(cells, i)
                if np.array_equal(currentImage, image):
                    tracelog("game finished, only still-lifes or no lifes")
                    tracelog("starting over...")
                    startNewGame(target_image, i)
                    tracelog("resetting index counter...")
                    updateIteration(target_iteration_images[i], i, False)
                else:
                    tracelog("saving image...")
                    image.save(target_image)
                    tracelog("updating index counter...")
                    updateIteration(target_iteration_images[i], i, True)
            except Exception as e:
                tracelog("an error occured:", e)
                tracelog("restarting...")
                startNewGame(target_image, i)
                tracelog("resetting index counter...")
                updateIteration(target_iteration_images[i], i, False)
        else:
            tracelog("starting new game...")
            startNewGame(target_image, i)
            tracelog("resetting index counter...")
            updateIteration(target_iteration_images[i], i, False)


if __name__ == '__main__':
    main()
