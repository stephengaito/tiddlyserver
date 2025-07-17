"""
A tool to (re)build a complete and portable tiddlyWiki from a
tiddlyerServer's collection of tiddlers.
"""

import argparse
from pathlib import Path
import os
import signal
import sys
import yaml

from tiddlyserver.configuration import loadConfig
from tiddlyserver.tiddly_wiki_app import packTiddlyWiki

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

def getArgsLoadConfig(desc) :
  signal.signal(signal.SIGTERM, sigtermHandler)

  parser = argparse.ArgumentParser(description=desc)

  parser.add_argument(
    "baseDir",
    type=Path,
    help="""
      The base directory for all of the Multi-TiddlyWikis.

      Defaults to the current working directory.

      This directory MUST contain the 'wikiConfig.yaml' file.

    """
  )

  parser.add_argument(
    "wikiKey",
    type=str,
    help="""
      The key of the wiki to pack. This key must be contained in the
      dictionary of wikis in the `wikiConfig.yaml` file.
      """
  )

  parser.add_argument(
    'htmlPath',
    type=Path,
    help="""
      The path to the tiddlyWiki html file to be (un)packed.
    """
  )
  args = parser.parse_args()

  baseDir = os.path.abspath(args.baseDir)
  return (args, loadConfig(baseDir))

def pack() :
  print("Packing")

  args, config = getArgsLoadConfig("""
      A tool to (re)build a complete and portable tiddlyWiki from a
      tiddlyServer's collection of tiddlers.
    """)

  if args.wikiKey not in config['wikis'] :
    print(f"The wikiKey {args.wikiKey} could not be found in the configuration")  # noqa
    print("-----------------------------------")
    print(yaml.dump(config))
    print("-----------------------------------")
    sys.exit(1)

  theWiki = config['wikis'][args.wikiKey]
  html = packTiddlyWiki(
    Path(theWiki['baseHtml']), Path(theWiki['dir'])
  )

  with open(args.htmlPath, 'w') as htmlFile :
    htmlFile.write(html)

def unpack() :
  print("Unpacking")

  config = getArgsLoadConfig("""
      A tool to unpack an existing tiddlyWiki into a tiddlyServer's
      collection of tiddlers.
  """)

  html = None
  with open('aFile') as htmlFile :
    html = htmlFile.read()

  unpackTiddlyWiki(config, html)

