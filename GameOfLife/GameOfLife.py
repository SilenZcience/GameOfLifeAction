import os
import sys
import numpy as np
from PIL import Image
from PIL.ImageColor import getcolor

color_light_dead = "#FFFEFEFF"
color_light_alive = "#41B782FF"
color_light_dying = "#28394AFF"

color_dark_dead = "#141321FF"
color_dark_alive = "#D83A7DFF"
color_dark_dying = "#F7D747FF"

color_dead = [getcolor(color_light_dead, "RGBA"), getcolor(color_dark_dead, "RGBA")]
color_alive = [getcolor(color_light_alive, "RGBA"), getcolor(color_dark_alive, "RGBA")]
color_dying = [getcolor(color_light_dying, "RGBA"), getcolor(color_dark_dying, "RGBA")]

canvas_size = (420, 1200)  # height, width
cell_grid = (84, 240)

cell_size = [canvas_size[0]/cell_grid[0],
             canvas_size[1]/cell_grid[1]]
for i, size in enumerate(cell_size):
    if not size.is_integer():
        cell_size[i] += 1
    cell_size[i] = int(cell_size[i])

workingDir = os.path.abspath(os.path.join(__file__,  '..'))
if len(sys.argv) > 1:
    try:
        workingDir = os.path.abspath(sys.argv[1])
    except:
        pass

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
    currentArray = np.zeros(
        [currentColorArray.shape[0], currentColorArray.shape[1]], dtype=np.int8)

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
            cells, currentImage = initRunningGame(target_image, i)
            cells = updateGame(cells)
            image = generateImage(cells, i)
            if np.array_equal(currentImage, image):
                startNewGame(target_image, i)
                updateIteration(target_iteration_images[i], i, False)
            else:
                image.save(target_image)
                updateIteration(target_iteration_images[i], i, True)
        else:
            startNewGame(target_image, i)
            updateIteration(target_iteration_images[i], i, False)


if __name__ == '__main__':
    main()
