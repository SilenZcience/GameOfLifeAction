import os
import numpy as np
from PIL import Image
from ArgParser import parseArgs
from IterationUpdater import updateIteration

def tracelog(*args):
    print("TraceLog:", *args)


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
                    updateIteration(target_iteration_images[i], color_alive[i], False)
                else:
                    tracelog("saving image...")
                    image.save(target_image)
                    tracelog("updating index counter...")
                    updateIteration(target_iteration_images[i], color_alive[i], True)
            except Exception as e:
                tracelog("an error occured:", e)
                tracelog("restarting...")
                startNewGame(target_image, i)
                tracelog("resetting index counter...")
                updateIteration(target_iteration_images[i], color_alive[i], False)
        else:
            tracelog("starting new game...")
            startNewGame(target_image, i)
            tracelog("generating index counter...")
            updateIteration(target_iteration_images[i], color_alive[i], False)


if __name__ == '__main__':
    main()
