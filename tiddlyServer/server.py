"""
An Starlette based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

import argparse
import os
from pathlib import Path
import signal

import uvicorn
from uvicorn.logging import DefaultFormatter

from starlette.middleware.cors import CORSMiddleware

from tiddlyServer.baseApp import createBaseApp
from tiddlyServer.configuration import loadConfig
from tiddlyServer.exceptions import ExitNow, shutDownExceptions

##################################################
# Logging BLACK MAGIC!!!
import logging
logger = logging.getLogger('tiddlyWiki')
logger.setLevel(logging.INFO)
consoleLogger = logging.StreamHandler()
consoleLogger.setLevel(logging.INFO)
consoleLogger.setFormatter(DefaultFormatter(
  fmt="%(levelprefix)s %(message)s",
  use_colors=True
))
logger.addHandler(consoleLogger)
#
###################################################

# from tiddlyserver.wsgiLogger import WSGILogger

# from logging.config import dictConfig

def sigtermHandler(signum, frame) :
  # we raise our own more specific ExitNow exception.
  raise ExitNow()

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
  logger.info(f"BaseDir: {baseDir}")

  baseApp = createBaseApp(baseDir, config)

  # app = WSGILogger(
  #   dispApp, mesg="Base logger",
  #   keys=['PATH_INFO']
  # )

  logger.info("Your Uvicorn will serve you on:")
  logger.info(f"  http://{config['host']}:{config['port']}/")

  try :
    uvicorn.run(
      CORSMiddleware(
        app=baseApp,
        allow_origins=['*'],
        allow_methods=['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS']
      ),
      host=config['host'],
      port=int(config['port'])
    )
  except shutDownExceptions :
    pass

  logger.info("Your Uvicorn has left")

if __name__ == "__main__":
  main()
