"""
An :py:mod:`flask` based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

import argparse
import os
from pathlib import Path
import signal
import sys
# import yaml

from waitress import serve, wasyncore

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.shared_data import SharedDataMiddleware

from tiddlyserver.tiddly_wiki_app import create_app
from tiddlyserver.default_app import createBaseApp
from tiddlyserver.configuration import loadConfig

# from tiddlyserver.wsgiLogger import WSGILogger

# from logging.config import dictConfig


def sigtermHandler(signum, frame) :

  # simply call sys.exit as this will raise a SystemExit exception which
  # is then "handled" by Waitress and if we care, can be handled by our
  # app.

  # consider sending and waiting for a Blinker signal followed by an
  # ExitNow exception. This would provide a softer shutdown sequence.

  # try raising the more specific ExitNow exception defined by
  # waitress.wasyncore.... most of our application does not care... BUT
  # our database update/insert operations should be protected.

  raise wasyncore.ExitNow()

  sys.exit(0)

shutDownExceptions = (wasyncore.ExitNow, KeyboardInterrupt, SystemExit)

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

  tiddlyWikis = {}
  for aWiki in config['wikis'].values() :
    tiddlyWikis[aWiki['url']] = create_app(aWiki)

  baseApp = createBaseApp(config)

  staticDir = baseDir / config['static']['dir']
  print(f"StaticDir: {staticDir}")

  if not staticDir.is_dir() :
    staticDir.mkdir(parents=True)

  staticApp = SharedDataMiddleware(baseApp, {
    config['static']['url'] :
      os.path.join(baseDir, config['static']['dir'])
  })

  dispApp = DispatcherMiddleware(staticApp, tiddlyWikis)

  # app = WSGILogger(
  #   dispApp, mesg="Base logger",
  #   keys=['PATH_INFO']
  # )

  print("\nYour Waitress will serve you on:")
  print(f"  http://{config['host']}:{config['port']}/")

  try :
    serve(
      dispApp,
      host=config['host'],
      port=int(config['port'])
    )
  except shutDownExceptions :
    pass

  print("\nYour Waitress has left")

if __name__ == "__main__":
  main()
