import os
import numpy as np
from scipy.ndimage import convolve
from PIL import Image
from ArgParser import parseArgs, settings
from IterationUpdater import updateIteration

def tracelog(*args):
    print("TraceLog:", *args)

kernel = np.ones((3,3), dtype=np.uint8)
kernel[1,1] = 0

parseArgs()
workingDir  = settings.path
color_dead  = settings.cdead
color_dying = settings.cdying
color_alive = settings.calive
canvas_size = settings.canvas
cell_grid   = settings.grid
gif         = settings.gif
gifLength   = settings.gifLength
gifSpeed    = settings.gifSpeed
fromTransition = settings.fromTransition
toTransition   = settings.toTransition

def defineCellSize() -> None:
    """
    Calculate the cell_size by the given
    canvas- and grid size.
    """
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


def updateGame(cells: np.ndarray) -> np.ndarray:
    """Calculate/Yields the next cycle of cells, aswell
    as the cycle after that, to flag the cells,
    which are about to die."""
    while True:
        num_alive = convolve(cells, kernel, mode='constant')
        cells = (((cells) & (num_alive == 2)) | (num_alive == 3)).astype(np.uint8)

        num_alive = convolve(cells, kernel, mode='constant')
        cells[(cells == 1) & ((num_alive < 2) | (num_alive > 3))] = 2

        yield cells
        cells[cells > 1] = 1


def generateImage(cells: np.ndarray, dark: int) -> Image:
    """
    Generate and return a PIL Image from a given cell array.
    'dark' is either 0 or 1, used as the index for the color-arrays.
    """
    newArray = np.zeros([*cells.shape, 4], dtype=np.uint8)
    newArray[cells == 0] = color_dead[dark]
    newArray[cells == 1] = color_alive[dark]
    newArray[cells == 2] = color_dying[dark]
    newArray = newArray.repeat(cell_size[0], axis=0).repeat(cell_size[1], axis=1)
    
    return Image.fromarray(newArray)


def initConvertGame(image: Image, dark: int) -> tuple:
    """
    Takes a PIL Image and the color-index 'dark'.
    Returns a tuple containing the cell array and the image
    itself.
    """
    global canvas_size
    currentColorArray = np.asarray(image)
    if currentColorArray.shape != (*canvas_size, 4):
        canvas_size = (currentColorArray.shape[0], currentColorArray.shape[1])
        defineCellSize()
        print("Modified canvas_size:", canvas_size)
    currentColorArray = currentColorArray[::cell_size[0], ::cell_size[1]]
    currentArray = (currentColorArray != color_dead[dark]).any(-1).astype(np.uint8)

    return (currentArray, image)


def initRunningGame(imageFile: str, dark: int) -> tuple:
    """
    Takes an imagePath as String and the 'dark' color-index
    value.
    Returns the cell array and the PIL Image as a tuple.
    """
    image = Image.open(imageFile).convert("RGBA")
    return initConvertGame(image, dark)


def initNewGame() -> np.ndarray:
    return np.random.randint(0, 2, cell_grid, dtype=np.uint8)


def startNewGame(target_image: str, dark: int) -> None:
    """
    Starts a new Game Of Life Game by saving a random
    image to the 'target_image' path.
    """
    cells = initNewGame()
    image = generateImage(cells, dark)
    image.save(target_image)


def readGif(filename: str, asNumpy: bool = True, split: bool = True) -> list:
    """
    Takes a string-path of a gif-File and returns either the numpy array
    or the PIL Image array of all frames or half the frames.
    """
    if not os.path.isfile(filename):
        raise IOError('File not found: ' + str(filename))
    
    gifImage = Image.open(filename)
    
    images = []
    nFrames = (gifImage.n_frames//2)+1 if split else gifImage.n_frames
    
    for n in range(nFrames):
        gifImage.seek(n)
        image = gifImage.convert("RGBA")
        if asNumpy:
            image = np.asarray(image)
            if len(image.shape) == 0:
                raise MemoryError("Too little memory to convert PIL image to array!")
        images.append(image)
    
    return images


def createGif() -> None:
    """
    Reads the -gif Parameter file to an image array,
    updates the last frame until -gifLength frames is
    reached, and saves the updated gif.
    """
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
    framePause = max((400//gifSpeed), 0)
    framePauseImages = []
    for _ in range(framePause):
        framePauseImages.append(images[0])
    images[0].save(gifSplit[0] + '.gif',
               save_all=True, append_images=framePauseImages + images[1:] + images[-2::-1], optimize=False, duration=gifSpeed, loop=0)


def generateTransition(cellsFrom: np.ndarray, cellsTo: np.ndarray, probability: int, previousMask: np.ndarray = None) -> np.ndarray:
    """
    return a cell-array, that resembles cellsTo with 'probability'% and
    cellsFrom with 1-'probability'%.
    """
    randomModifier = np.random.choice([False, True], size=cellsFrom.shape, p=[0.25, 0.75])
    previousMask[previousMask] = randomModifier[previousMask]
    randomMask = np.random.choice([False, True], size=cellsFrom.shape, p=[1-probability, probability])
    randomMask[previousMask] = True
    transitionCells = np.copy(cellsFrom)
    transitionCells[randomMask] = cellsTo[randomMask]
    return (transitionCells, randomMask)


def createTransition() -> None:
    """
    Reads the -from and -to parameters to images and gameoflife state arrays.
    updates the arrays and concatenates then.
    inserts transition frames between the images.
    saves the transition to a gif.
    """
    gifSplit = os.path.splitext(fromTransition)
    
    imagesFrom = []
    cellsFrom, currentImageFrom = initRunningGame(fromTransition, 0)
    imagesFrom.append(currentImageFrom)
    print(imagesFrom)
    print(fromTransition, toTransition)
    imagesTo = []
    cellsTo, currentImageTo = initRunningGame(toTransition, 0)
    imagesTo.append(currentImageTo)
    
    imagesTransition = []
    
    frameCountSplit = gifLength//2
    frameCountTransition = max(5, gifLength//10)
    
    cell_gen_from = updateGame(cellsFrom)
    cell_gen_to = updateGame(cellsTo)
    try:
        for i in range(frameCountSplit):
            print("Generating image (from) ", i+1, '/', gifLength, sep='')
            cellsFrom = next(cell_gen_from)
            imagesFrom.append(generateImage(cellsFrom, 0))
        for i in range(frameCountSplit, gifLength):
            print("Generating image  (to)  ", i+1, '/', gifLength, sep='')
            cellsTo = next(cell_gen_to)
            imagesTo.append(generateImage(cellsTo, 0))
        randomMask = (cellsFrom == cellsTo)
        for i in range(1, frameCountTransition+1):
            probability = i/(frameCountTransition+1)
            if probability < 0.1:
                continue
            elif probability > 0.9:
                break
            print("Generating transition   ", i, '/', frameCountTransition, sep='')
            cellsTransition, randomMask = generateTransition(cellsFrom, cellsTo, i/(frameCountTransition+1), randomMask)
            imagesTransition.append(generateImage(cellsTransition, 0))
            # if np.count_nonzero(cellsTransition==cellsTo) > 0.95 * np.multiply(*cellsFrom.shape):
            #     break
    except KeyboardInterrupt:
            pass
    framePause = max((600//gifSpeed), 0)
    framePauseFrom, framePauseTo = [], []
    for _ in range(framePause):
        framePauseFrom.append(imagesFrom[0])
        framePauseTo.append(imagesTo[0])
    print("Saving gif...")
    imagesFrom[0].save(gifSplit[0] + '-transition.gif',
               save_all=True,
               append_images=framePauseFrom + imagesFrom[1:] + imagesTransition + imagesTo[::-1] + framePauseTo + imagesTo[1:] + imagesTransition[::-1] + imagesFrom[:0:-1],
               optimize=False, duration=gifSpeed, loop=0)    
        


def main():
    if gif:
        createGif()
        return
    
    if fromTransition:
        createTransition()
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
