import os
import numpy as np
from PIL import Image
from ArgParser import parseArgs
from IterationUpdater import updateIteration

def tracelog(*args):
    print("TraceLog:", *args)


workingDir, color_dead, color_dying, color_alive, canvas_size, cell_grid, gif, gifLength, gifSpeed = parseArgs()

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
    newArray = np.zeros([canvas_size[0], canvas_size[1], 4], dtype=np.uint8)

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

    return Image.fromarray(newArray)


def initRunningGame(imageFile, dark):
    global canvas_size
    image = Image.open(imageFile).convert("RGBA")
    currentColorArray = np.asarray(image)
    if currentColorArray.shape != (canvas_size[0], canvas_size[1], 4):
        canvas_size = (currentColorArray.shape[0], currentColorArray.shape[1])
        print("Modified canvas_size:", canvas_size)
    currentColorArray = currentColorArray[::cell_size[0], ::cell_size[1]]
    currentArray = (~(currentColorArray == color_dead[dark]).all(-1)).astype(np.uint8)

    return (currentArray, image)


def initNewGame():
    return np.random.randint(0, 2, cell_grid, dtype=np.uint8)


def startNewGame(target_image, dark):
    cells = initNewGame()
    image = generateImage(cells, dark)
    image.save(target_image)


def createGif():
    images = []
    cells, currentImage = initRunningGame(gif, 0)
    images.append(currentImage)
    cell_gen = updateGame(cells)
    try:
        for i in range(gifLength):
            print("Generating image ", i+1, '/', gifLength, sep='')
            cells = next(cell_gen)
            images.append(generateImage(cells, 0))
    except KeyboardInterrupt:
        pass
    print("Saving gif...")
    images[0].save(os.path.splitext(gif)[0] + '.gif',
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
    try:
        main()
    except:
        pass
