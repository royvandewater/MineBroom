#!/usr/bin/env python
import os
import sys
import getopt
import random
import time

import pygtk
pygtk.require('2.0')
import gtk
import pango

class Sweeper:
    def __init__(self, row_count, column_count, mine_count):
        """
        Setup the gtk window
        """
        # Instantiate the minefield
        self.minefield = Minefield(row_count, column_count, mine_count)

        # Create a window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        # Connect the delete event (attempted window close)
        self.window.connect("delete_event", self.delete_event)

        # Connect the destroy event (Window termination)
        self.window.connect("destroy", self.destroy)

        # Set border width of window
        self.window.set_border_width(10)
        self.window.show()

        # Set a widget container for the window 
        # (windows can only have one widget in them)
        self.layout_box = gtk.VBox(False, 0)

        # Put the layout box into the window
        self.window.add(self.layout_box)

        # Create a box to hold the reset button
        self.reset_box = gtk.HBox(False, 0)
        self.reset_box.show()

        # Create a reset button and put it in the reset box
        self.reset_button = gtk.Button("Reset")
        self.reset_button.show()
        self.reset_box.pack_start(self.reset_button, True, False, 0)

        # Put the reset box in the layout box 
        # Commented out as the reset functionality has not yet been
        # implemented
        # self.layout_box.pack_start(self.reset_box, False, False, 0)

        # Create the minebox container and a minearray for keeping track of the buttons
        self.minebox = gtk.Table(rows=row_count, columns=column_count, homogeneous=True)
        self.minebox.show()
        self.minelist = list()
        self.flaglist = list()

        # Put the minebox in the layout box
        self.layout_box.pack_start(self.minebox, True, True, 0)
        self.layout_box.show()

        for row in range(row_count):
            # Add a row to the minearray
            self.minelist.insert(row, list())
            self.flaglist.insert(row, list())

            for col in range(column_count):
                # Create a new button for every square
                button = gtk.Button()

                # Add a callback onclick function for the button
                button.connect("button_press_event", self.square_clicked_event, (row,col))

                # Attach the button to the appropriate place in the minebox
                self.minebox.attach(button, col, 1+col, row, 1+row)

                # Add the button to the row list
                self.minelist[row].insert(col, button)

                # Add a flag image
                flag_image = self.get_svg_from_file("flag")

                # Add the flag image to the flaglist
                self.flaglist[row].insert(col, flag_image)

                # Lastly, display the widget (button)
                button.show()


    def delete_event(self, widget, event, data=None):
        """Called when user attempts to exit the application

        If this returns true, destroy call will be prevented.
        This allows for confirmation prompts and termination cancellation
        """
        return False


    def destroy(self, widget, data=None):
        """Close the window

        The application will not terminate, it will resume execution
        of code written after gtk.main() is called.
        """
        gtk.main_quit()


    def display_mines(self):
        """Displays all of the mines in the minefield

        The only mine not displayed is the one clicked on to cause this
        function to be called. It is assumed that that mine's image has
        already been set.
        """

        mines = self.minefield.get_diff()

        for mine in mines:
            coords,value = mine

            if value == 1:
                button = self.minelist[coords[0]][coords[1]]
                image = self.get_svg_from_file("mine")
                button.add(image)


    def flag_square(self, widget, row, col):
        """Toggles marking the square as a mine

        The solver uses this data to find new mines. If a safe spot
        is marked in error, the solver may incorrectly deduce that a
        mined spot is safe.
        """
        flagged = self.minefield.flag(row, col)

        button = self.minelist[row][col]
        flag_image = self.flaglist[row][col]

        if(flagged == 1):
            button.add(flag_image)
        elif(flagged == 0):
            button.remove(flag_image)


    def get_svg_from_file(self, filename):
        image = gtk.Image()
        image.set_from_file("icons/{0}.svg".format(filename))
        image.show()
        return image


    def main(self):
        gtk.main()

    def solve(self):
        """
        Attempts to solve as much of the board as possible using the solver application
        """
        # Write the current board out to a file
        cwd = os.getcwd()
        f = open('input', 'w')
        f.write(self.minefield.serialize())
        f.close()
        r = self.minefield.rows
        c = self.minefield.cols
        n = max(r, c)
        command = "gringo -c r={0} -c c={1} -c n={2} helpers mines input | clasp -n 0".format(r,c,n)
        print(os.system(command))

    def square_clicked_event(self, widget, event, data=None):
        """
        Gets called on gtk button click
        """
        if event.button == 1:
            self.uncover(widget, data[0], data[1])
        elif event.button == 3:
            self.flag_square(widget, data[0], data[1])

        # This is where the solver will interact with the game
        self.solve()

        # Check to see if the game was won, output to console if so
        if self.minefield.won():
            print("A winner is you")


    def square_value_image(self, value):
        """Loads the svg file corresponding to the value number

        The svg loader expects a an integer value x where 1 <= x <= 9
        """
        image_files = ("one","two","three","four","five","six","seven","eight","nine")
        return self.get_svg_from_file(image_files[value-1])


    def uncover(self, widget, row, col):
        """Checks to see if the clicked square was a mine

        The method will automatically update the appropriate squares
        to display their new status. If the square is safe but adjacent
        to one or more mines, a number is displayed indicating the number
        of mines adjacent to it. If there are no adjacent mines, the
        square will lose its relief but display no number. Lastly, if the
        square is a mine, the square will show an explosion icon and all
        mines on the board will be revealed.
        """
        uncovered_squares = self.minefield.open(row, col)

        if not uncovered_squares:
            uncovered_squares = self.minefield.open_adjacent(row, col)

        for square in uncovered_squares:
            # unpack square ((2, 1), 1) to coordinates and values
            coords,value = square
            # If value is negative, user clicked on a mine
            if value < 0:
                print("Mine, you are dead")

                button = self.minelist[coords[0]][coords[1]]
                image = self.get_svg_from_file("bang")
                button.add(image)

                self.display_mines()
            else:
                button = self.minelist[coords[0]][coords[1]]
                # Disable the button
                # button.set_sensitive(False)
                button.set_relief(gtk.RELIEF_NONE)
                # If mine is greater than 0, display the number of adjacent mines
                if value > 0:
                    # add button image
                    image = self.square_value_image(value)
                    button.add(image)

class Minefield:
    """Provide a playing field for a Minesweeper game.

    This class internally represents a Minesweeper playing field, and provides
    all functions necessary for the basic manipulations used in the game.
    """
    def __init__(self, rows = 16, cols = 16, mines = 40):
        """Initialize the playing field.

        This function creates a playing field of the given size, and randomly
        places mines within it.

        rows and cols are the numbers of rows and columns of the playing
        field, respectively.  mines is the number of mines to be placed within
        the field.
        """
        for var in (rows, cols, mines):
            if var < 0:
                raise ValueError, "all arguments must be > 0"
        if mines >= (rows * cols):
            raise ValueError, "mines must be < (rows * cols)"

        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.cleared = 0
        self.flags = 0
        self.start_time = None

        minelist = []
        self.freecoords = {}
        for col in range(cols):
            self.freecoords[col] = range(rows)
        while mines > 0:
            y = random.choice(self.freecoords.keys())
            x = random.randrange(len(self.freecoords[y]))
            minelist.append((self.freecoords[y][x], y))
            del self.freecoords[y][x]
            if not self.freecoords[y]:
                del self.freecoords[y]
            mines = mines - 1

        self.board = []
        for col in range(cols):
            self.board.append([(-2, 0)] * rows)
            for row in range(rows):
                if (row, col) in minelist:
                    self.board[col][row] = (-1, 0)


    def _get_adjacent(self, x, y):
        """Provide a list of all tiles adjacent to the given tile.

        This function takes the x and y coordinates of a tile, and returns a
        list of a 2-tuples containing the coordinates of all adjacent tiles.

        x and y are the x and y coordinates of the base tile, respectively.
        """
        adjlist = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                   (x - 1, y), (x + 1, y),
                   (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)]
        rmlist = []
        for adjpair in adjlist:
            for value, index in [(-1, 0), (-1, 1), (self.cols, 0),
                                 (self.rows, 1)]:
                if adjpair[index] == value:
                    rmlist.append(adjpair)
                    break
        for item in rmlist:
            adjlist.remove(item)
        return adjlist


    def flag(self, x, y):
        """Flag or unflag an unopened tile.

        This function attempts to toggle the flagged status of the tile at
        the given coordinates, and returns a value indicating the action
        which occurred.  A return value of -1 indicates that the tile is
        opened and cannot be flagged; 0 indicates that the tile is unflagged;
        and 1 indicates that the tile was flagged.

        x and y are the x and y coordinates of the tile to be flagged,
        respectively.
        """
        if self.board[x][y][1] == -1:
            return -1
        elif self.board[x][y][1] == 0:
            self.board[x][y] = (self.board[x][y][0], 1)
            self.flags = self.flags + 1
            return 1
        else:
            self.board[x][y] = (self.board[x][y][0], 0)
            self.flags = self.flags - 1
            return 0

    def get_diff(self):
        """
        Return a list providing mine locations.
        This function provides a list of 2-tuples.  The first value of each
        2-tuple is a 2-tuple, providing the x and y coordinates of a tile;
        the second value of the 2-tuple is either 1 or -1.  1 indicates that
        a mine is at those coordinates; -1 indicates that a mine is not at
        those coordinates, but a flag was placed there.
        """
        diff = []
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board[x][y] == (-2, 1):
                    diff.extend([((x, y), -1)])
                elif ((self.board[x][y][0] == -1) and
                      (self.board[x][y][1] == 0)):
                    diff.extend([((x, y), 1)])
        return diff

    def open(self, coordlist, y = None):
        """Open one or more tiles.

        This function opens all the tiles provided, and others as
        appropriate, and returns a list indicating which tiles were opened
        and the result of the open.  If a tile is opened which has no
        adjacent mines, all adjacent tiles will be opened automatically.

        The function returns a list of 2-tuples.  The first value is a
        2-tuple with the x and y coordinates of the opened tile; the second
        value indicates the number of mines adjacent to the tile, or -1 if
        the tile contains a mine.

        If a value for y is given, the tile at (coordlist, y) will be
        opened; otherwise, the function will open the tiles whose
        coordinates are given in 2-tuples in coordlist.
        """
        if y is not None:
            coordlist = [(coordlist, y)]
        opened = []
        while len(coordlist) != 0:
            x, y = coordlist.pop()
            not_done = 1
            if (self.board[x][y][1] == 1) or (self.board[x][y][0] >= 0):
                not_done = 0
            elif self.board[x][y][0] == -1:
                if self.cleared > 0:
                    self.board[x][y] = (-1, -1)
                    opened.append(((x, y), -1))
                    not_done = 0
                else:
                    while self.board[x][y][0] == -1:
                        # The first opened block is a mine; move it elsewhere.
                        newx = random.choice(self.freecoords.keys())
                        newy = random.randrange(len(self.freecoords[newx]))
                        self.board[x][y] = (-2, 0)
                        self.board[newx][newy] = (-1,
                                                  self.board[newx][newy][1])
            if not_done:
                adjlist = self._get_adjacent(x, y)
                adjcount = 0
                for adjx, adjy in adjlist:
                    if self.board[adjx][adjy][0] == -1:
                        adjcount = adjcount + 1
                self.board[x][y] = (adjcount, -1)
                if self.cleared is 0:
                    del self.freecoords
                    self.start_time = time.time()
                self.cleared = self.cleared + 1
                opened.append(((x, y), adjcount))
                if adjcount == 0:
                    coordlist.extend(adjlist)
        return opened


    def open_adjacent(self, x, y):
        """Open all unflagged tiles adjacent to the given one, if appropriate.

        This function counts the number of tiles adjacent to the given one
        which are flagged.  If that count matches the number of mines adjacent
        to the tile, all unflagged adjacent tiles are opened, using
        Field.open().

        x and y are the x and y coordinates of the tile to be flagged,
        respectively.
        """
        adjmines = self.board[x][y][0]
        if self.board[x][y][1] != -1:
            return []
        adjlist = self._get_adjacent(x, y)
        flagcount = 0
        for adjx, adjy in adjlist:
            if self.board[adjx][adjy][1] == 1:
                flagcount = flagcount + 1
        if adjmines == flagcount:
            return self.open(adjlist)
        else:
            return []


    def playtime(self):
        """Return a string representing the current play time.

        This function returns a string which provides a human-readable
        representation of the amount of time the current game has been
        played, starting when the first tile is opened.  If the player
        takes an inordinate amount of time (9999 minutes, 0 seconds -- or
        longer), the returned string will be '9999:00+'.
        """
        if self.start_time is None:
            return '00:00'
        rawtime = int(time.time() - self.start_time)
        mins = int(math.floor(rawtime / 60.0))
        secs = rawtime % 60
        if mins > 9998:
            return '9999:00+'
        elif (mins < 10) and (secs < 10):
            return '0%i:0%i' % (mins, secs)
        elif mins < 10:
            return '0%i:%i' % (mins, secs)
        elif secs < 10:
            return '%i:0%i' % (mins, secs)
        else:
            return '%i:%i' % (mins, secs)

    def serialize(self):
        """Returns a normalized, serialized form of the game board.

        The serializer is only intended to be used for input into a particular
        GRINGO application
        """
        squares = list()
        for row in enumerate(self.board):
            for col in enumerate(self.board[row[0]]):
                square = col[1]
                if square[1] == -1:
                    # This is a safe square
                    squares.append("safe({0},{1},{2}).".format(row[0],col[0],square[0]))
                elif square[1] == 1:
                    # This is a known mine
                    squares.append("mine({0},{1}).".format(row[0],col[0]))

        return_string = ""
        for square in squares:
            return_string += square + "\n"

        # return everything except the last linebreak
        return return_string[:-1]

    def won(self):
        """Indicate whether or not the game has been won.

        This function will return a true value if the game has been won, and
        a false value otherwise.
        """
        return ((self.flags == self.mines) and
                (self.cleared == (self.rows * self.cols) - self.mines))

def get_options():
    """Parse command-line options.

    This function reads the command-line options from sys.argv[1:] and
    returns a dict containing all configuration options with their given
    values.  It will abort the program if appropriate; for example, if
    an option has a bad argument, or a bad option is given.
    """
    game_opts = {'rows': 16, 'cols': 16, 'mines': 40, 'debug': 0}
    if os.name is 'posix':
        game_opts['paths'] = ['/usr/share/games/pysweeper',
                              '/usr/local/share/games/pysweeper', sys.path[0],
                              '.']
    else:
        game_opts['paths'] = [sys.path[0], '.']

    try:
        options = getopt.getopt(sys.argv[1:], 'hvdr:c:m:',
                                ['help', 'rows=', 'columns=', 'cols=', 'dir=',
                                 'mines=', 'version', 'debug'])[0]
    except getopt.error:
        show_usage(sys.exc_info()[1])

    set_size = 0
    set_mines = 0
    for option, argument in options:
        if option in ('-h', '--help'):
            show_usage()
        elif option in ('-v', '--version'):
            show_version()
        elif option in ('-d', '--debug'):
            game_opts['debug'] = 1
        elif option in ('-r', '--rows'):
            set_option(game_opts, 'rows', argument)
            set_size = 1
        elif option in ('-c', '--cols', '--columns'):
            set_option(game_opts, 'cols', argument)
            set_size = 1
        elif option in ('-m', '--mines'):
            set_option(game_opts, 'mines', argument)
            set_mines = 1
        elif option == '--dir':
            argument = os.path.normcase(argument)
            argument = os.path.normpath(argument)
            game_opts['paths'].insert(0, argument)
    if set_size and (not set_mines):
        game_opts['mines'] = int(round(game_opts['rows'] * game_opts['cols']
                                       * .15625))
    if game_opts['mines'] > (game_opts['rows'] * game_opts['cols']):
        show_usage("Too many mines (%i) for a %ix%i playing field" %
                   (game_opts['mines'], game_opts['rows'], game_opts['cols']))
    return game_opts

def init_ui(game_opts):
    """Initialize a game interface and return it.

    This function attempts to import and initialize a user interface for the
    game.  If successful, it returns the initialized interface.  Otherwise,
    it aborts the program, with a traceback if debug is true.

    game_opts is a dictionary of game options, as provided by get_options().
    """

    row_count    = game_opts['rows'] if game_opts.has_key('rows') else 16
    column_count = game_opts['cols'] if game_opts.has_key('cols') else 16
    mine_count   = game_opts['mines'] if game_opts.has_key('mines') else 40

    sweeper = Sweeper(row_count, column_count, mine_count)

    sweeper.main()
    return sweeper

def main(argv):
    """ Main method of application """
    sweeper = Sweeper()
    sweeper.main()

def set_option(options, name, value, minvalue = 0):
    """Set a value of a dictionary, with type and bounds checking.

    This function will set a given dictionary key to the given value, if it
    can be converted to an integer and is above a given value.  If any of
    the checks fail, the program will abort with an appropriate error
    message.

    options is the dictionary which contains the key to be set.  name is the
    name of the dictionary key to be set.  value is the value which will be
    checked and stored.  minvalue is the minimum value; the variable value
    must be larger than minvalue to be set.
    """
    try:
        value = int(value)
    except ValueError:
        show_usage("Bad argument (%s) for option %s" % (value, name))
    else:
        if value > minvalue:
            options[name] = value
        else:
            fail("bad value for option %s (too small)" % name)

def show_usage(error = None):
    """Show usage information, with an error if given, and exit appropriately.

    This function will display a standard, run-of-the-mill usage message,
    providing rudimentary help with the game's command-line switches.  If an
    error message is given, it will be printed preceding the rest of the
    message, and the program will exit with an exit code of 2; otherwise,
    the program will exit with a code of 0.
    """
    if error is not None:
        print "Error: %s." % error
    print "Usage: %s [-d] [-r,--rows ROWS]" % sys.argv[0],
    print "[-c,--cols,--columns COLUMNS] [-m,--mines MINES] [--dir DIRECTORY]"
    print "  -h,--help:           Display this usage message and exit."
    print "  -v,--version:        Display the program version and exit."
    print "  -r,--rows:           Set the number of rows in the playing field."
    print "  -c,--cols,--columns: Set the number of columns in the playing",
    print "field."
    print "  -m,--mines:          Set the number of mines in the playing",
    print "field."
    print "  --dir:               Add a directory for finding external data."
    print "  -d,--debug:          Enable debugging."
    if error is None:
        sys.exit(0)
    else:
        sys.exit(2)

def show_version():
    """
    Print version and copyright information, and exit normally.
    """
    print """
    sweeper 0.1 -- An implementation of the Minesweeper game in GTK.
    Copyright 2010 Roy van de Water <support@royvandewater.com>
    Code based on pysweeper by Brett Smith (Copyright 2002)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.
    """
    sys.exit(0)

if __name__=="__main__":
    game_opts = get_options()
    sweeper = init_ui(game_opts)
