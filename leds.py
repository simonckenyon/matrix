import time, sys, os, re
from neopixel  import Color, Adafruit_NeoPixel  # See https://learn.adafruit.com/neopixels-on-raspberry-pi/software
from PIL import Image  # Use apt-get install python-imaging to install this


class LED:
    LED_COUNT = 160  # Number of LED pixels.
    LED_PIN = 18  # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 5  # DMA channel to use for generating signal (try 5)
    LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)

    # Speed of movement, in seconds (recommend 0.1-0.3)
    SPEED = 0.075

    # Size of your matrix
    MATRIX_WIDTH = 20
    MATRIX_HEIGHT = 8

    # A list converting LED string number to physical grid layout
    ledMatrix = [7, 8, 23, 24, 39, 40, 55, 56, 71, 72, 87, 88, 103, 104, 119, 120, 135, 136, 151, 152,
                6, 9, 22, 25, 38, 41, 54, 57, 70, 73, 86, 89, 102, 105, 118, 121, 134, 137, 150, 153,
                5, 10, 21, 26, 37, 42, 53, 58, 69, 74, 85, 90, 101, 106, 117, 122, 133, 138, 149, 154,
                4, 11, 20, 27, 36, 43, 52, 59, 68, 75, 84, 91, 100, 107, 116, 123, 132, 139, 148, 155,
                3, 12, 19, 28, 35, 44, 51, 60, 67, 76, 83, 92, 99, 108, 115, 124, 131, 140, 147, 156,
                2, 13, 18, 29, 34, 45, 50, 61, 66, 77, 82, 93, 98, 109, 114, 125, 130, 141, 146, 157,
                1, 14, 17, 30, 33, 46, 49, 62, 65, 78, 81, 94, 97, 110, 113, 126, 129, 142, 145, 158,
                0, 15, 16, 31, 32, 47, 48, 63, 64, 79, 80, 95, 96, 111, 112, 127, 128, 143, 144, 159]


    def __init__(self):
        # Check that we have sensible width & height
        if LED.MATRIX_WIDTH * LED.MATRIX_HEIGHT != len(LED.ledMatrix):
            raise Exception("Matrix width x height does not equal length of ledMatrix")

    def allonecolour(self, strip, colour):
        # Paint the entire matrix one colour
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, colour)
        strip.show()


    def colour(self, r, g, b):
        # Fix for Neopixel RGB->GRB, also British spelling
        return Color(g, r, b)


    def colourTuple(self, rgbTuple):
        return Color(rgbTuple[1], rgbTuple[0], rgbTuple[2])


    def initLeds(self, strip):
        # Intialize the library (must be called once before other functions).
        strip.begin()
        # Wake up the LEDs by briefly setting them all to white
        self.allonecolour(strip, self.colour(255, 255, 255))
        time.sleep(0.01)


    def startDisplay(self, image):
        global keep_on_going

        keep_on_going = True


        # Open the image file
        try:
            loadIm = Image.open(image)
        except:
            raise Exception("Image file %s could not be loaded" % image)

        # If the image height doesn't match the matrix, resize it
        if loadIm.size[1] != LED.MATRIX_HEIGHT:
            origIm = loadIm.resize((loadIm.size[0] / (loadIm.size[1] // LED.MATRIX_HEIGHT), LED.MATRIX_HEIGHT), Image.BICUBIC)
        else:
            origIm = loadIm.copy()
        # If the input is a very small portrait image, then no amount of resizing will save us
        if origIm.size[0] < LED.MATRIX_WIDTH:
            raise Exception("Picture is too narrow. Must be at least %s pixels wide" % LED.MATRIX_WIDTH)

        # Check if there's an accompanying .txt file which tells us
        # how the user wants the image animated
        # Commands available are:
        # NNNN speed S.SSS
        #   Set the scroll speed (in seconds)
        #   Example: 0000 speed 0.150
        #   At position zero (first position), set the speed to 150ms
        # NNNN hold S.SSS
        #   Hold the frame still (in seconds)
        #   Example: 0011 hold 2.300
        #   At position 11, keep the image still for 2.3 seconds
        # NNNN-PPPP flip S.SSS
        #   Animate MATRIX_WIDTH frames, like a flipbook
        #   with a speed of S.SSS seconds between each frame
        #   Example: 0014-0049 flip 0.100
        #   From position 14, animate with 100ms between frames
        #   until you reach or go past position 49
        #   Note that this will jump positions MATRIX_WIDTH at a time
        #   Takes a bit of getting used to - experiment
        # NNNN jump PPPP
        #   Jump to position PPPP
        #   Example: 0001 jump 0200
        #   At position 1, jump to position 200
        #   Useful for debugging only - the image will loop anyway
        txtlines = []
        match = re.search(r'^(?P<base>.*)\.[^\.]+$', image, re.M | re.I)
        if match:
            txtfile = match.group('base') + '.txt'
            if os.path.isfile(txtfile):
                #print "Found text file %s" % (txtfile)
                f = open(txtfile, 'r')
                txtlines = f.readlines()
                f.close()

        # Add a copy of the start of the image, to the end of the image,
        # so that it loops smoothly at the end of the image
        im = Image.new('RGB', (origIm.size[0] + LED.MATRIX_WIDTH, LED.MATRIX_HEIGHT))
        im.paste(origIm, (0, 0, origIm.size[0], LED.MATRIX_HEIGHT))
        im.paste(origIm.crop((0, 0, LED.MATRIX_WIDTH, LED.MATRIX_HEIGHT)),
                 (origIm.size[0], 0, origIm.size[0] + LED.MATRIX_WIDTH, LED.MATRIX_HEIGHT))

        # Create NeoPixel object with appropriate configuration.
        strip = Adafruit_NeoPixel(LED.LED_COUNT, LED.LED_PIN, LED.LED_FREQ_HZ, LED.LED_DMA, LED.LED_INVERT, LED.LED_BRIGHTNESS)
        self.initLeds(strip)

        # And here we go.
        try:
            while (keep_on_going):

                # Loop through the image widthways
                # Can't use a for loop because Python is dumb
                # and won't jump values for FLIP command
                x = 0
                # Initialise a pointer for the current line in the text file
                tx = 0

                while (x < im.size[0] - LED.MATRIX_WIDTH) and keep_on_going:

                    # Set the sleep period for this frame
                    # This might get changed by a textfile command
                    thissleep = LED.SPEED

                    # Set the increment for this frame
                    # Typically advance 1 pixel at a time but
                    # the FLIP command can change this
                    thisincrement = 1

                    rg = im.crop((x, 0, x + LED.MATRIX_WIDTH, LED.MATRIX_HEIGHT))
                    dots = list(rg.getdata())

                    for i in range(len(dots)):
                        strip.setPixelColor(LED.ledMatrix[i], self.colourTuple(dots[i]))
                    strip.show()

                    # Check for instructions from the text file
                    if tx < len(txtlines):
                        match = re.search(
                            r'^(?P<start>\s*\d+)(-(?P<finish>\d+))?\s+((?P<command>\S+)(\s+(?P<param>\d+(\.\d+)?))?)$',
                            txtlines[tx], re.M | re.I)
                        if match:
                            #print "Found valid command line %d:\n%s" % (tx, txtlines[tx])
                            st = int(match.group('start'))
                            fi = st
                            #print "Current pixel %05d start %05d finish %05d" % (x, st, fi)
                            if match.group('finish'):
                                fi = int(match.group('finish'))
                            if x >= st and tx <= fi:
                                if match.group('command').lower() == 'speed':
                                    LED.SPEED = float(match.group('param'))
                                    thissleep = LED.SPEED
                                    #print "Position %d : Set speed to %.3f secs per frame" % (x, thissleep)
                                elif match.group('command').lower() == 'flip':
                                    thissleep = float(match.group('param'))
                                    thisincrement = LED.MATRIX_WIDTH
                                    #print "Position %d: Flip for %.3f secs" % (x, thissleep)
                                elif match.group('command').lower() == 'hold':
                                    thissleep = float(match.group('param'))
                                    #print "Position %d: Hold for %.3f secs" % (x, thissleep)
                                elif match.group('command').lower() == 'jump':
                                    #print "Position %d: Jump to position %s" % (x, match.group('param'))
                                    x = int(match.group('param'))
                                    thisincrement = 0
                            # Move to the next line of the text file
                            # only if we have completed all pixels in range
                            if x >= fi:
                                tx = tx + 1
                        else:
                            #print "Found INVALID command line %d:\n%s" % (tx, txtlines[tx])
                            tx = tx + 1

                    x = x + thisincrement
                    time.sleep(thissleep)
            self.allonecolour(strip, self.colour(0, 0, 0))

        except (KeyboardInterrupt, SystemExit):
            #print "Stopped"
            self.allonecolour(strip, self.colour(0, 0, 0))


    def stopDisplay(self):
        global keep_on_going

        keep_on_going = False
