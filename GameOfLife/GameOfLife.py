import os
import numpy as np
from PIL import Image
from ArgParser import parseArgs
from IterationUpdater import updateIteration

def tracelog(*args):
    print("TraceLog:", *args)


workingDir, color_dead, color_dying, color_alive, canvas_size, cell_grid, gif, gifLength, gifSpeed = parseArgs()

def defineCellSize():
    global cell_size
    cell_size = [canvas_size[0]/cell_grid[0],
                canvas_size[1]/cell_grid[1]]
    for i, size in enumerate(cell_size):
        if not size.is_integer():
            cell_size[i] += 1
        cell_size[i] = int(cell_size[i])

defineCellSize()
target_images = [os.path.join(workingDir, 'GameOfLifeBright.png'),
                os.path.join(workingDir, 'GameOfLifeDark.png')]
target_iteration_images = [os.path.join(workingDir, 'IterationBright.svg'),
                           os.path.join(workingDir, 'IterationDark.svg')]


def updateGame(cells):
    """Calculate the next cycle of cells, aswell
    as the cycle after that, to flag the cells,
    which are about to die."""
    while True:
        nextArray = np.zeros(cell_grid, dtype=np.uint8)

        for row, col in np.ndindex(cells.shape):
            num_alive = np.sum(cells[max(row-1,0):row+2, max(col-1,0):col+2]) - cells[row, col]

            nextArray[row, col] = int((cells[row, col] and num_alive == 2) or (num_alive == 3))

        cells = nextArray.copy()
        for row, col in np.ndindex(nextArray.shape):
            num_alive = np.sum(nextArray[max(row-1,0):row+2, max(col-1,0):col+2]) - nextArray[row, col]

            if nextArray[row, col] == 1 and (num_alive < 2 or num_alive > 3):
                cells[row, col] = 2

        yield cells
        cells[cells > 1] = 1


def generateImage(cells, dark):
    newArray = np.zeros([*cells.shape, 4], dtype=np.uint8)
    newArray[cells == 0] = color_dead[dark]
    newArray[cells == 1] = color_alive[dark]
    newArray[cells == 2] = color_dying[dark]
    newArray = newArray.repeat(cell_size[0], axis=0).repeat(cell_size[1], axis=1)
    
    return Image.fromarray(newArray)


def initConvertGame(image, dark):
    global canvas_size
    currentColorArray = np.asarray(image)
    if currentColorArray.shape != (*canvas_size, 4):
        canvas_size = (currentColorArray.shape[0], currentColorArray.shape[1])
        defineCellSize()
        print("Modified canvas_size:", canvas_size)
    currentColorArray = currentColorArray[::cell_size[0], ::cell_size[1]]
    currentArray = (~(currentColorArray == color_dead[dark]).all(-1)).astype(np.uint8)

    return (currentArray, image)


def initRunningGame(imageFile, dark):
    image = Image.open(imageFile).convert("RGBA")
    return initConvertGame(image, dark)


def initNewGame():
    return np.random.randint(0, 2, cell_grid, dtype=np.uint8)


def startNewGame(target_image, dark):
    cells = initNewGame()
    image = generateImage(cells, dark)
    image.save(target_image)


def readGif(filename, asNumpy=True, split=True):
    if not os.path.isfile(filename):
        raise IOError('File not found: ' + str(filename))
    
    gifImage = Image.open(filename)
    
    gifImage.seek(0)
    
    images = []
    nFrames = (gifImage.n_frames//2)+1 if split else gifImage.n_frames
    for n in range(nFrames):
        image = gifImage.convert("RGBA")
        if asNumpy:
            image = np.asarray(image)
            if len(image.shape) == 0:
                raise MemoryError("Too little memory to convert PIL image to array!")
        images.append(image)
        gifImage.seek(n+1)

    return images


def createGif():
    gifSplit = os.path.splitext(gif)

    if (gifSplit[1].upper() == '.GIF'):
        images = readGif(gif, False)
        cells, currentImage = initConvertGame(images[-1], 0)
        global gifLength
        if gifLength < 0:
            gifLength = len(images)+1
    else:
        images = []
        cells, currentImage = initRunningGame(gif, 0)
        print("Generating image ", 1, '/', gifLength, sep='')
        images.append(currentImage)
    
    startFrame = len(images)
    cell_gen = updateGame(cells)
    try:
        for i in range(startFrame, gifLength):
            print("Generating image ", i+1, '/', gifLength, sep='')
            cells = next(cell_gen)
            images.append(generateImage(cells, 0))
    except KeyboardInterrupt:
        pass
    print("Saving gif...")
    images[0].save(gifSplit[0] + '.gif',
               save_all=True, append_images=images[1:] + images[-2::-1], optimize=False, duration=gifSpeed, loop=0)


def main():
    if gif:
        createGif()
        return
    
    for i, target_image in enumerate(target_images):
        if os.path.exists(target_image):
            try:
                tracelog("reading game state...")
                cells, currentImage = initRunningGame(target_image, i)
                tracelog("updating game cycle...")
                cells = next(updateGame(cells))
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
            except Exception as exception:
                tracelog("an error occured:", exception)
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
    try:
        main()
    except Exception as exception:
        tracelog("an error occured:", exception)
    except KeyboardInterrupt:
        pass
