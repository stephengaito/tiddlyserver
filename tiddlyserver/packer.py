"""
A tool to (re)build a complete and portable tiddlyWiki from a
tiddlyerServer's collection of tiddlers.
"""

import argparse
from pathlib import Path
import os
import signal
import sys

from tiddlyserver.configuration import loadConfig
from tiddlyserver.tiddly_wiki_app import reBuildTiddlyWiki

class ExitNow(Exception) :
  def __init__(self) :
    super.__init()

def sigtermHandler(signum, frame) :

  # simply call sys.exit as this will raise a SystemExit exception which
  # is then "handled" by Waitress and if we care, can be handled by our
  # app.

  # consider sending and waiting for a Blinker signal followed by an
  # ExitNow exception. This would provide a softer shutdown sequence.

  # try raising the more specific ExitNow exception defined by
  # waitress.wasyncore.... most of our application does not care... BUT
  # our database update/insert operations should be protected.

  raise ExitNow()

  sys.exit(0)

shutDownExceptions = (ExitNow, KeyboardInterrupt, SystemExit)

def getArgsLoadConfig() :
  signal.signal(signal.SIGTERM, sigtermHandler)

  parser = argparse.ArgumentParser(
    description="""
      A tool to (re)build a complete and portable tiddlyWiki from a
      tiddlyServer's collection of tiddlers.
    """
  )

  parser.add_argument(
    "baseDir",
    nargs="?",
    type=Path,
    default=Path(),
    help="""
      The base directory for all Multi-TiddlyWikis to store all tiddlers.
      Defaults to the current working directory.

      This directory MUST contain the wikiConfig.yaml configuration. It
      may, in addition, also contain a file called `empty.html` containing
      the base *empty* TiddlyWiki with the nothing more than the TiddlyWeb
      plugin installed.
    """
  )

  args = parser.parse_args()

  baseDir = os.path.abspath(args.baseDir)
  return loadConfig(baseDir)

def pack() :
  print("Packing")
  
  config = getArgsLoadConfig()

  html = reBuildTiddlyWiki(config)

  with open('aFile', 'w') as htmlFile :
    htmlFile.write(html)

def unpack() : 
  print("Unpacking")
  print("   not yet implemented")
