from os.path import exists


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


def updateIteration(imageFile, color, increment):
    if not exists(imageFile):
        with open(imageFile, 'w', encoding="utf-8") as image:
            image.write(IterationImageContent(*color))
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