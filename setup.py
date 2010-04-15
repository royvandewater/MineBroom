#!/usr/bin/env python
#
# Last reviseed: $Date: 2002/06/29 17:22:46 $

from distutils.core import setup

setup(name="Pysweeper",
      version = "1.0",
      description = "A Minesweeper implementation",
      author = "Brett Smith",
      author_email = "bcsmit1@engr.uky.edu",
      url = "http://www.canonical.org/pysweeper",
      scripts = ['pysweeper'],
      data_files = [('lib/games/pysweeper', ['sdl_ui.py']),
                    ('share/games/pysweeper', ['flag.xpm', 'mine.xpm']),
                    ('share/man/man6', ['pysweeper.6']),
                    ('share/doc/pysweeper', ['LICENSE', 'README'])]
     )
