#!/usr/bin/env python
"""sdl_ui.py -- An SDL interface for Pysweeper
Copyright 2002 Brett Smith <bcsmit1@engr.uky.edu>

This provides a graphical interface for Pysweeper, an implementation of
Minesweeper, using SDL with Pygame.
"""
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA, 02111-1307.
#
# Last revised: $Date: 2002/06/29 04:00:02 $

import pygame
from pygame.locals import *
if not pygame.font:
    raise 'UIError', "The SDL UI requires pygame.font"
if not pygame.image:
    raise 'UIError', "The SDL UI requires pygame.image"

import math
import os.path
import time

colors = {1: (0, 0, 255), 2: (0, 160, 0),
          3: (255, 0, 0), 4: (0, 0, 127),
          5: (160, 0, 0), 6: (0, 255, 255),
          7: (160, 0, 160), 8: (0, 0, 0)}

class SDL_UI:
    """An SDL interface for Pysweeper.

    This class is meant to serve as an interface class for Pysweeper.  It
    provides all necessary functions, and provides a number of pretty extras
    itself.
    """
    def __init__(self, rows, cols, mines, tilesize = 20, paths = ('.',)):
        """Initialize all variables and visual elements needed for the game.

        This function creates everything needed to begin playing the game:
        variables, fonts, surfaces, and other such core pieces.
        """
        self._init_vars(rows, cols, mines, tilesize, paths)
        pygame.init()
        pygame.mixer.quit()
        self._init_fonts()
        self._init_images()
        self._init_window()
        self._init_header()
        self._init_statusbar()
        self._init_screen()
        self._init_bg()
        self._init_surfaces()
        self.flag_img.convert()
        self.mine_img.convert()


    def _init_vars(self, rows, cols, mines, tilesize, paths):
        """Initialize class variables.

        This function initializes variables used by the class throughout
        game play.  This function does not initialize all variables used;
        variables which are used with a specific surface (such as the
        header or statusbar) are set in that surface's initialization
        function.  The variables here are used very frequently throughout
        the creation of all window elements, or reflect internal game
        state.
        """
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.tilesize = tilesize
        self.imagepaths = paths
        self.active = 1
        self.opened = []
        self.pressed = []
        self.pressed_last = []
        self.openmine = None
        self.last_button = None
        self.last_object = None
        self.last_flags = None
        self.last_time = None
        self.newdraws = []


    def _init_fonts(self):
        """Initialize game fonts.

        This function creates pygame Font objects for all fonts which will be
        used by the game.
        """
        self.font = pygame.font.Font(None, 14)


    def _init_images(self):
        """Create surfaces loaded from images.

        This fuction finds all the game image files, and puts them into
        surfaces, raising an exception if it fails along the way.  This
        function demands that all images be in the same directory, and
        raises UIError if it is unable to load any image for any reason.
        """
        # We'll use flag.xpm to figure out which directory to use.
        failure = 1
        for directory in self.imagepaths:
            try:
                self.flag_img = self._init_image(directory, 'flag.xpm')
            except 'UIError':
                pass
            else:
                failure = 0
                break
        if failure:
            raise 'UIError', ("Failed to load flag.xpm -- " +
                              "unable to find a valid image directory")

        self.mine_img = self._init_image(directory, 'mine.xpm')
                                         

    def _init_image(self, directory, filename):
        """Create a surface from an image.

        This function loads an image from the given filename and returns
        a surface containing it.  It raises UIError if the load failes for
        any reason.

        directory is the directory containing the file to load.  filename is
        the name of the file in that directory which is the image.
        """
        fullname = os.path.join(directory, filename)
        try:
            image = pygame.image.load(fullname)
        except pygame.error:
            raise 'UIError', "Unable to load image %s" % fullname
        image.set_colorkey(image.get_at((0, 0)), RLEACCEL)
        return image


    def _init_window(self):
        """Set measurements of the various window parts and final window.

        This function determines the sizes of the different window parts
        (header, playing field, and statusbar), often by rendering the
        requisite pieces and calculating the minimum size from them.  Since
        all pieces must be the same width, the final width for all pieces --
        the maximum among all the parts' widths -- is stored at the
        function's end.
        """
        for num in range(1, 9):
            text = self.font.render(`num`, 1, (0, 0, 0))
            textsize = max(text.get_size()) + 3
            self.tilesize = max(self.tilesize, textsize)
        for image in (self.mine_img, self.flag_img):
            imagesize = max(image.get_size()) + 3
            self.tilesize = max(self.tilesize, imagesize)

        self.xsize = (self.cols * self.tilesize) + (self.cols - 1)
        self.ysize = (self.rows * self.tilesize) + (self.rows - 1)

        self.restart_button, self.restart_pressed = \
                             self._make_header_button('New Game')
        self.quit_button, self.quit_pressed = self._make_header_button('Quit')
        self.restart_place = pygame.Rect((5, 5) +
                                         self.restart_button.get_size())
        self.quit_place = pygame.Rect((10 + self.restart_button.get_width(), 5)
                                      + self.quit_button.get_size())
        self.header_width = (self.restart_button.get_width() +
                             self.quit_button.get_width() + 15)
        self.header_height = (self.quit_button.get_height() + 10)

        max_text = 'Mines: %i/%i' % (self.rows * self.cols, self.mines)
        self.flag_text = self.font.render(max_text, 1, (0, 0, 0))
        self.time_text = self.font.render('Time: 9999:00+', 1, (0, 0, 0))
        self.time_xpos = self.flag_text.get_width() + 14
        self.statusbar_width = (self.flag_text.get_width() +
                                self.time_text.get_width() + 25)

        self.max_width = max((self.xsize, self.header_width,
                              self.statusbar_width))


    def _init_header(self):
        """Draw the header.

        This function draws the entire header, with all buttons unpressed,
        into a single surface.
        """
        self.header = pygame.Surface((self.max_width, self.header_height))
        self.header.fill((175, 175, 175))
        self.header.blit(self.restart_button, self.restart_place)
        self.header.blit(self.quit_button, self.quit_place)
        max_x = self.header.get_width() - 1
        max_y = self.header_height - 1
        pygame.draw.line(self.header, (0, 0, 0), (0, max_y), (max_x, max_y))
        

    def _init_statusbar(self):
        """Draw the initial statusbar.

        This function renders all text necessary for the initial statusbar --
        with 0 flags set and no time -- and creates a final, single surface
        providing the entire display.
        """
        self.statusbar = pygame.Surface((self.max_width,
                                         self.font.size('I')[1] + 7))
        self.statusbar.fill((175, 175, 175))
        pygame.draw.line(self.statusbar, (0, 0, 0), (0, 0),
                         (self.max_width - 1, 0))
        self.flag_text = self.font.render('Mines: 0/%i' % self.mines, 1,
                                          (0, 0, 0))
        self.statusbar.blit(self.flag_text, (4, 4))
        self.time_text = self.font.render('Time: 00:00', 1, (0, 0, 0))
        self.statusbar.blit(self.time_text, (self.time_xpos, 4))


    def _init_screen(self):
        """Initialize the window.

        This function determines the size of the whole window, containing all
        interface elements, and creates it.  It also convert()s all surfaces 
        created before the window is initialized, since that cannot be done
        before a display mode has been set.
        """
        screen_ysize = (self.ysize + self.header_height +
                        self.font.size('I')[1] + 7)
        self.screen = pygame.display.set_mode((self.max_width,
                                               screen_ysize))
        pygame.display.set_caption('Pysweeper')
        self.flag_text.convert()
        self.time_text.convert()
        self.statusbar.convert()
        self.quit_button.convert()
        self.quit_pressed.convert()
        self.restart_button.convert()
        self.restart_pressed.convert()


    def _init_bg(self):
        """Draw the playing field surface.

        This function sets up the grid which is the playing field, bg, and
        a bgwborder surface, which is simply bg centered over a dark gray
        background, used when the header or statusbar are wider than the
        playing field itself.  It also sets xmargin, which indicates the
        number of pixels between the left window border and the playing
        field.
        """
        # This looks inefficient.  It probably is.  However, lines have to be
        # drawn in the order they currently are so that they overlap each
        # other properly -- i.e., the black vertical lines overlap the
        # horizontal "stick out" shade lines.
        self.bg = pygame.Surface((self.xsize, self.ysize))
        self.bg.fill((175, 175, 175))
        pygame.draw.line(self.bg, (225, 225, 225), (0, 0), (self.xsize, 0))
        pygame.draw.line(self.bg, (225, 225, 225), (0, 0), (0, self.ysize))
        for xpos in range(self.tilesize, self.xsize, self.tilesize + 1):
            pygame.draw.line(self.bg, (125, 125, 125), (xpos - 1, 0),
                             (xpos - 1, self.ysize))
            pygame.draw.line(self.bg, (225, 225, 225), (xpos + 1, 0),
                             (xpos + 1, self.ysize))
        for ypos in range(self.tilesize, self.ysize, self.tilesize + 1):
            pygame.draw.line(self.bg, (125, 125, 125), (0, ypos - 1),
                             (self.xsize, ypos - 1))
            pygame.draw.line(self.bg, (225, 225, 225), (0, ypos + 1),
                             (self.xsize, ypos + 1))
        for xpos in range(self.tilesize, self.xsize, self.tilesize + 1):
            pygame.draw.line(self.bg, (0, 0, 0), (xpos, 0),
                             (xpos, self.ysize))
        for ypos in range(self.tilesize, self.ysize, self.tilesize + 1):
            pygame.draw.line(self.bg, (0, 0, 0), (0, ypos),
                             (self.xsize, ypos))
        pygame.draw.line(self.bg, (125, 125, 125), (0, self.ysize),
                         (self.xsize, self.ysize))
        pygame.draw.line(self.bg, (125, 125, 125), (self.xsize, 0),
                         (self.xsize, self.ysize))
        self.bg.convert()
        if self.xsize >= self.max_width:
            self.bgwborder = self.bg
            self.xmargin = 0
        else:
            self.bgwborder = pygame.Surface((self.max_width, self.ysize))
            x_difference = self.max_width - self.xsize
            self.xmargin = int(math.floor(x_difference / 2.0))
            self.bgwborder.fill((150, 150, 150))
            self.bgwborder.blit(self.bg, (self.xmargin, 0))
            self.bgwborder.convert()


    def _init_surfaces(self):
        """Initialize game surfaces.

        This function simply creates all of the surfaces which the interface
        uses.

        unflag is a 'blank' surface, used to clear flags from tiles.
        redtile is a tile with a red background, used beneath an opened mine.
        badflag is a black 'X' over a transparent background, used when the
         game is over to indicate that a flag has been placed where there is
         no mine.
        overlay is a gray square on transparency, used to give tiles a
         pressed-in look.
        clear returns tiles to their original look after overlay has been
         blit on them; it is a square over transparency, with two light edges
         and two dark edges.
        """
        tilesize = self.tilesize
        tileend = self.tilesize - 1

        self.unflag = pygame.Surface((tilesize - 2, tilesize - 2))
        self.unflag.fill((175, 175, 175))
        self.unflag.convert()

        self.redtile = pygame.Surface((tilesize, tilesize))
        self.redtile.fill((255, 0, 0))
        self.redtile.convert()

        self.badflag = pygame.Surface((tilesize, tilesize))
        self.badflag.fill((0, 255, 0))
        pygame.draw.line(self.badflag, (0, 0, 0), (0, 0),
                         (tilesize, tilesize))
        pygame.draw.line(self.badflag, (0, 0, 0), (0, tileend - 2),
                         (tileend - 2, 0))
        self.badflag.set_colorkey((0, 255, 0))
        self.badflag.convert()

        self.overlay = pygame.Surface((tilesize, tilesize))
        self.overlay.fill((175, 175, 175))
        pygame.draw.rect(self.overlay, (0, 255, 0),
                         (1, 1, tileend - 2, tileend - 2), 0)
        self.overlay.set_colorkey((0, 255, 0))
        self.overlay.convert()

        self.clear = pygame.Surface((tilesize, tilesize))
        self.clear.fill((0, 255, 0))
        self.clear.set_colorkey((0, 255, 0))
        pygame.draw.line(self.clear, (225, 225, 225), (0, 0), (tileend, 0))
        pygame.draw.line(self.clear, (225, 225, 225), (0, 0), (0, tileend))
        pygame.draw.line(self.clear, (125, 125, 125), (0, tileend),
                         (tileend, tileend))
        pygame.draw.line(self.clear, (125, 125, 125), (tileend, 0),
                         (tileend, tileend))
        self.clear.convert()


    def _make_header_button(self, text):
        """Make a pair of buttons from a string of text.

        This function renders the given string of text and returns two
        surfaces: the first is an unpressed button with the text, and the
        second is the same button with a pressed-down effect.

        text is the string to be rendered on the buttons.
        """
        button_text = self.font.render(text, 1, (0, 0, 0))
        button = pygame.Surface((button_text.get_width() + 10,
                                 button_text.get_height() + 4))
        button.fill((175, 175, 175))
        max_x = button.get_width() - 1
        max_y = button.get_height() - 1
        pygame.draw.line(button, (125, 125, 125), (0, max_y), (max_x, max_y))
        pygame.draw.line(button, (125, 125, 125), (max_x, 0), (max_x, max_y))
        pygame.draw.line(button, (225, 225, 225), (0, 0), (0, max_y))
        pygame.draw.line(button, (225, 225, 225), (0, 0), (max_x, 0))
        button.blit(button_text, (6, 3))
        pressed = pygame.Surface((button_text.get_width() + 10,
                                  button_text.get_height() + 4))
        pressed.fill((175, 175, 175))
        pygame.draw.line(pressed, (225, 225, 225), (0, max_y), (max_x, max_y))
        pygame.draw.line(pressed, (225, 225, 225), (max_x, 0), (max_x, max_y))
        pygame.draw.line(pressed, (125, 125, 125), (0, 0), (0, max_y))
        pygame.draw.line(pressed, (125, 125, 125), (0, 0), (max_x, 0))
        pressed.blit(button_text, (6, 3))
        return button, pressed


    def _need_new_screen(self, rows, cols, tilesize):
        """Determine whether a new screen is required.

        This function will return a value which is true when a new screen is
        required (because the number of rows, number of columns, or size of
        tiles has changed), and false if not.

        rows, cols, and tilesize are the new values for the number of rows,
        number of columns, and size of tiles, respectively.
        """
        return ((rows != self.rows) or (cols != self.cols) or
                (tilesize != self.tilesize))


    def _get_coords(self, pos):
        """Provide a tile's coordinates, given a screen position.

        This function will return a 2-tuple containing the coordinates of
        the tile which contains the given screen position.  If the position
        is not part of a tile, a -1 will be in the coordinate pair.

        pos is the position to be converted.
        """
        coords = [-1, -1]
        for axissize, margin, index in [(self.xsize, self.xmargin, 0),
                                        (self.ysize, self.header_height, 1)]:
            value = -1
            if pos[index] >= margin:
                for pixel in range(margin + self.tilesize,
                                   margin + axissize + 1, self.tilesize + 1):
                    value = value + 1
                    if pos[index] < pixel:
                        coords[index] = value
                        break
        return tuple(coords)


    def _get_pos(self, coords):
        """Provide the starting position of a tile, given its coordinates.

        This function will return a 2-tuple containing the screen position
        of the upper-left pixel of a field tile, given its raw coordinates.

        coords is the tile's coordinates, in a 2-sequence.
        """
        return ((coords[0] * self.tilesize) + coords[0] + self.xmargin,
                (coords[1] * self.tilesize) + coords[1] + self.header_height)


    def _get_rect_pos(self, surface, pos):
        """Provide a position which will center a surface in a tile.

        This function generates a Rect for the given surface, and will then
        modify it such that it is centered within the tile which begins at
        the given position.

        surface is the surface to be centered.  pos is the position of the
        upper-left pixel of the tile for the surface to be centered in.
        """
        rectpos = surface.get_rect()
        tilerect = Rect(pos[0] + 2, pos[1] + 2, self.tilesize - 2,
                       self.tilesize - 2)
        rectpos.centerx = tilerect.centerx
        rectpos.centery = tilerect.centery
        return rectpos


    def _press(self, coords, clobber = 1):
        """Mark a tile to be pressed.

        This function will add a coordinate pair to be drawn as 'pressed
        down.'  It will also clear the list before adding the pair if
        clobber is true.

        coords is the coordinates to be pressed, in a 2-sequence.  If
        clobber is a true value, the list of coordinates to be pressed
        will be emptied first.
        """
        if clobber:
            self.pressed = []
        if ((-1 not in coords) and (coords[0] < self.cols) and 
            (coords[1] < self.rows)):
            if coords not in self.pressed:
                self.pressed.append(coords)


    def _press_adjacent(self, coords):
        """Mark a tile and all adjacent tiles to be pressed.

        This function is called when the the player holds down the second
        mouse button over the playing field.  It marks the tile under the
        mouse, and all tiles adjacent to it, to be drawn as 'pressed down.'

        coords is the coordinates of the base tile, in a 2-sequence.
        """
        self.pressed = []
        if -1 not in coords:
            x, y = coords
            adjlist = [(x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
                       (x - 1, y), (x, y), (x + 1, y),
                       (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)]
            for pair in adjlist:
                self._press(pair, 0)


    def _draw(self, surface, position):
        """Draw a change to the screen and record its position.

        This function will blit surface on to the main screen at the given
        position.  It will then append a 4-tuple representing the place of
        the change to self.newdraws, which is used in SDL_UI.update() to
        update the screen where necessary.

        surface is the surface to blit; position is where it should be blit.
        """
        self.screen.blit(surface, position)
        self.newdraws.append(tuple(position) + surface.get_size())
        

    def _draw_on_status(self, old_size, text, color, xplace = 4):
        """Draw a statusbar change.

        This function erases old text on the statusbar and replaces it with
        the new text provided.  old_size is the height and width of the old
        text.  text is the new text to be rendered.  color is the color in
        which to render it.  xplace indicates the x position of the text on
        the statusbar.
        """
        text_place = (xplace, self.ysize + self.header_height + 4)
        text_clear = pygame.Surface(old_size)
        text_clear.fill((175, 175, 175))
        self._draw(text_clear, text_place)
        rendered_text = self.font.render(text, 1, color)
        self._draw(rendered_text, text_place)
        return rendered_text


    def _update_status(self, flags, time, color = (0, 0, 0)):
        """Update the statusbar, if necessary.

        This function will check to see if any information provided on the
        statusbar has changed, and if so, call for the appropriate changes to
        be drawn, and save the new information for future comparisons.

        flags and time are the new values for the number of flags set (an
        integer) and the current play time (a string), respectively.  color is
        the color in which the statusbar text will be drawn.
        """
        if ((flags != self.last_flags) or (color != (0, 0, 0))):
            self.flag_text = self._draw_on_status(self.flag_text.get_size(),
                                                  'Mines: %i/%i' %
                                                  (flags, self.mines), color)
            self.last_flags = flags
        if ((time != self.last_time) or (color != (0, 0, 0))):
            self.time_text = self._draw_on_status(self.time_text.get_size(),
                                                  'Time: %s' % time, color,
                                                  self.time_xpos)
            self.last_time = time
            

    def _set_for_field(self, pos, button):
        """Determine if the mouse is over the field, and take action if so.

        This function is called when a mouse button is pressed anywhere other
        than over a special object, such as a header button.  It determines
        whether or not the mouse is over the field, saving this result to
        self.last_object.  If the mouse is also over the field, it sets
        certain tiles to be pressed, if appropriate for the given button.

        pos is the mouse position; button is the mouse button pressed.
        """
        coords = self._get_coords(pos)
        if ((not self.active) or (-1 in coords)):
            self.last_object = None
        else:
            self.last_object = 'field'
            if button is 1:
                self._press(coords)
            elif button is 2:
                self._press_adjacent(coords)
            elif button is 3:
                self.pressed = []


    def _act_on_field(self, pos, button, actions):
        """Determine and write an action to execute on the field, if any.

        This function is called when a mouse button is released anywhere other
        than over a special object, such as a header button.  It determines
        whether or not the mouse is over the field, and if so, writes to the
        list of actions the command corresponding to the given mouse button.

        pos is the mouse position; button is the mouse button released.
        """
        self.pressed = []
        coords = self._get_coords(pos)
        if -1 not in coords:
            if button is 1:
                actions.append(('open', coords))
            elif button is 2:
                actions.append(('sweep', coords))
            elif button is 3:
                actions.append(('flag', coords))


    def get_input(self):
        """Get user input and return a list of game commands from it.

        This function loops over the event queue provided by
        pygame.event.get(), creating a list of game commands (i.e., open,
        flag, etc.) from it, which are then returned to be processed.  If any
        input should result in immediate changes to the interface (for
        example, moving the mouse with a button held down causes field tiles
        to be pressed down), the necessary internal changes are made
        immediately.

        The return value is a list of 2-tuples.  The first value is a string
        which indicates the action to be taken.  The second value is an
        n-sequence of parameters, the specifics of which vary from action to
        action.
        """
        actions = []
        for event in pygame.event.get():
            if event.type is QUIT:
                actions.extend([('quit', (-1, -1))])
            elif event.type is KEYDOWN:
                if event.key == K_q:
                    actions.extend([('quit', (-1, -1))])
                elif (event.key == K_r) or (event.key == K_n):
                    actions.extend([('reset', (-1, -1))])
                elif event.key == K_d:
                    coords = self._get_coords(pygame.mouse.get_pos())
                    actions.append(('debug', coords))
            elif event.type is MOUSEBUTTONDOWN:
                if ((event.button is 1) and (self.last_button is None)):
                    self.last_button = 1
                    if self.restart_place.collidepoint(event.pos):
                        self._draw(self.restart_pressed,
                                   self.restart_place[:2])
                        self.last_object = 'restart'
                    elif self.quit_place.collidepoint(event.pos):
                        self._draw(self.quit_pressed, self.quit_place[:2])
                        self.last_object = 'quit'
                    else:
                        self._set_for_field(event.pos, 1)
                elif self.last_button is None:
                    self.last_button = event.button
                    self._set_for_field(event.pos, event.button)
            elif event.type is MOUSEMOTION:
                if ((self.last_object is 'field') and
                    (self.last_button in (1, 2)) and
                    (event.buttons[self.last_button - 1])):
                    coords = self._get_coords(event.pos)
                    if self.last_button is 1:
                        self._press(coords)
                    else:
                        self._press_adjacent(coords)
            elif ((event.type is MOUSEBUTTONUP) and
                  (event.button == self.last_button)):
                if event.button is 1:
                    if self.last_object is 'restart':
                        self._draw(self.restart_button, self.restart_place[:2])
                        if self.restart_place.collidepoint(event.pos):
                            actions.append(('reset', (-1, -1)))
                    elif self.last_object is 'quit':
                        self._draw(self.quit_button, self.quit_place[:2])
                        if self.quit_place.collidepoint(event.pos):
                            actions.append(('quit', (-1, -1)))
                    elif self.last_object is 'field':
                        self._act_on_field(event.pos, 1, actions)
                elif self.last_object is 'field':
                    self._act_on_field(event.pos, event.button, actions)
                self.last_button = None
                self.last_object = None
        return actions


    def update(self, actions, flags, time, won):
        """Make changes from game output, and update the screen.

        This function parses the output provided by the game logic, and
        draws all changes necessary -- opening of tiles, updating the
        statusbar, and the like -- from it.  This function also draws the
        pressed-in effect of mines, since these draws rely heavily upon the
        opened state of the tiles.  After all changes has been made, it
        redraws all parts of the screen which have been updated.

        actions is the list of output provided by the game logic.  flags is
        an integer indicating the number of flags which the player has
        placed on the field.  time is a string representing the amount of
        time which the game has been played.  won is true when the player
        has won the game; false otherwise.
        """
        for act, params in actions:
            for coords, result in params:
                pos = self._get_pos(coords)
                if act == 'open':
                    self.opened.append(coords)
                    self._draw(self.overlay, pos)
                    if result != 0:
                        if result == -1:
                            self.openmine = coords
                        else:
                            text = self.font.render(`result`, 1,
                                                    colors[result])
                            textpos = self._get_rect_pos(text, pos)[:2]
                            self._draw(text, textpos)
                elif act == 'flag':
                    if result == 1:
                        rect = self.flag_img
                        rectpos = self._get_rect_pos(rect, pos)[:2]
                        self._draw(rect, rectpos)
                    else:
                        unflagpos = (pos[0] + 1, pos[1] + 1)
                        self._draw(self.unflag, unflagpos)
                elif act == 'show':
                    if result == -1:
                        self._draw(self.badflag,
                                   self._get_rect_pos(self.badflag, pos)[:2])
                    else:
                        self._draw(self.mine_img,
                                   self._get_rect_pos(self.mine_img, pos)[:2])
        if self.active and won:
            self._update_status(flags, time, (0, 0, 255))
            self.active = 0
        elif self.active:
            self._update_status(flags, time)
        for coords in self.pressed:
            if ((coords not in self.pressed_last) and
                (coords not in self.opened) and (coords != self.openmine)):
                self._draw(self.overlay, self._get_pos(coords))
        for coords in self.pressed_last:
            if ((coords not in self.pressed) and
                (coords not in self.opened) and (coords != self.openmine)):
                self._draw(self.clear, self._get_pos(coords))
        if (self.openmine != None) and self.active:
            pos = self._get_pos(self.openmine)
            self._draw(self.redtile, pos)
            self._draw(self.mine_img, self._get_rect_pos(self.mine_img, pos)[:2])
            self.active = 0
        if self.newdraws:
            pygame.display.update(self.newdraws)
            self.newdraws = []
        self.pressed_last = self.pressed
        

    def reset(self, rows, cols, mines, tilesize = None):
        """Set up the interface for a new game.

        This function sets up the interface to play a new game.  It
        primarily does this by calling the separate _init functions as
        necessary, given the new game parameters.  It then redraws the
        window in its pristine state.

        rows, cols, and mines are the numbers of rows, columns, and mines
        in the new game, respectively.  tilesize the new size of tiles
        desired.
        """
        if tilesize is None:
            tilesize = self.tilesize
        new_screen = self._need_new_screen(rows, cols, tilesize)
        new_surfaces = (tilesize != self.tilesize)
        self._init_vars(rows, cols, mines, tilesize, self.imagepaths)
        if new_screen:
            self._init_window()
            self._init_header()
            self._init_bg()
            self._init_screen()
        self._init_statusbar()
        if new_surfaces:
            self._init_surfaces()
        self.screen.blit(self.header, (0, 0))
        self.screen.blit(self.bgwborder, (0, self.header_height))
        self.screen.blit(self.statusbar,
                         (0, self.header_height + self.ysize))
        pygame.display.flip()


    def wait(self):
        """Sleep a bit to give the CPU time to breathe."""
        time.sleep(.05)
