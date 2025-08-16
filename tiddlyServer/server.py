"""
An Starlette based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

import argparse
import os
from pathlib import Path
import signal
import sys
# import yaml

import uvicorn

from tiddlyServer.baseApp import createBaseApp
from tiddlyServer.configuration import loadConfig

# from tiddlyserver.wsgiLogger import WSGILogger

# from logging.config import dictConfig

class ExitNow(Exception) :
  pass

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

def main():

  signal.signal(signal.SIGTERM, sigtermHandler)

  parser = argparse.ArgumentParser(
    description="""
      A personal (i.e. unauthenticated) server for TiddlyWiki which
      implements the TiddlyWeb protocol.
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

  parser.add_argument(
    "--host",
    type=str,
    help="""
      The host/IP for the server to listen on.
      Overrides any default or host configured in wikiConfig.yaml.
    """
  )

  parser.add_argument(
    "--port",
    type=str,
    help="""
      The port to listen on.
      Overrides any default or port configured in wikiConfig.yaml.
    """
  )

  args = parser.parse_args()

  baseDir = os.path.abspath(args.baseDir)
  config = loadConfig(baseDir)

  if args.host : config['host'] = args.host
  if args.port : config['port'] = int(args.port)

  baseDir = Path(baseDir)
  print(f"BaseDir: {baseDir}")

  baseApp = createBaseApp(baseDir, config)

  # app = WSGILogger(
  #   dispApp, mesg="Base logger",
  #   keys=['PATH_INFO']
  # )

  print("\nYour Uvicorn will serve you on:")
  print(f"  http://{config['host']}:{config['port']}/")

  try :
    uvicorn.run(
      baseApp,
      host=config['host'],
      port=int(config['port'])
    )
  except shutDownExceptions :
    pass

  print("\nYour Uvicorn has left")

if __name__ == "__main__":
  main()
