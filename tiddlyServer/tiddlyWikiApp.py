"""
A Starlette based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

from typing import Any

import logging
import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import Response, HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from tiddlyServer.types import Tiddler, WikiDef
from tiddlyServer.tiddlerSerDes import readTiddler, readAllTiddlersBlocking, \
  writeTiddler, deleteTiddler
from tiddlyServer.preLoader import reloadTiddlyWiki

from tiddlyServer.tiddlerHash import tiddlerHash

# from tiddlyServer.wsgiLogger import WSGILogger

logger = logging.getLogger('tiddlyWiki')

appRoutes : list[Route] = []

async def corsOptions(request : Request) -> Response :
  return Response(
    "", headers={
      'Allow' : 'OPTIONS,GET,HEAD,PUT,DELETE'
    }
  )

appRoutes.append(Route(
  '/', endpoint=corsOptions, methods=['OPTIONS']
))

async def getIndex(request : Request) -> HTMLResponse :
  # Return a copy of the empty.html with all tiddlers in the tiddler directory
  # pre-loaded.

  # print(current_app.config['wiki_url'])
  # print("appRoute: /")

  # html = packTiddlyWiki(
  #   request.app.state.emptyHtmlFilename,
  #   request.app.state.tiddlerDir,
  #   str(request.app.state.wikiUrl)
  # )

  logger.info(f"Looking for {request.app.state.name} HTML")
  html = None
  while True :
    async with request.app.state.htmlLock :
      if not request.app.state.wikiNeedsLoading.is_set() :
        html = request.app.state.html
        if html : break

  logger.info(f"Found {request.app.state.name} HTML")
  return HTMLResponse(html)

appRoutes.append(Route(
  '/', endpoint=getIndex, methods=['GET']
))

async def getStatus(request : Request) -> JSONResponse :
  # Bare-minimum response which minimises UI cruft like usernames and login
  # screens.

  return JSONResponse({
    "space": {"recipe": "all"},
    "username": "GUEST",
    "read_only": False,
    "anonymous": True,
  })

appRoutes.append(Route(
  '/status', endpoint=getStatus, methods=['GET']
))

async def getReloadTiddlyWiki(request : Request ) -> Response :
  reloadTiddlyWiki(request.app)
  return Response("done")

appRoutes.append(Route(
  '/reload', endpoint=getReloadTiddlyWiki, methods=['GET']
))

async def getSkinnyTiddlers(request : Request) -> JSONResponse :
  # Return the JSON-ified non-text fields of all local tiddler files.
  #
  # NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  # the TiddlyWiki implementation will cope just fine with a plain JSON object
  # describing a tiddler's fields.

  tiddlerDir = request.app.state.tiddlerDir
  skinnyTiddlers = list(readAllTiddlersBlocking(tiddlerDir, includeText=False))
  return JSONResponse(skinnyTiddlers)

appRoutes.append(Route(
  '/recipes/all/tiddlers.json', endpoint=getSkinnyTiddlers, methods=['GET']
))

async def getTiddler(request : Request) -> Response :
  # Read a tiddler.
  #
  # NB: We assume the 'all' space (reported by the /status endpoint).
  #
  # NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  # the TiddlyWiki implementation will cope just fine with a plain JSON object
  # describing a tiddler's fields.

  title = request.path_params['title']

  tiddlerDir = request.app.state.tiddlerDir

  try:
    return JSONResponse(readTiddler(tiddlerDir, title))
  except FileNotFoundError:
    return Response("", status_code=404)

appRoutes.append(Route(
  '/recipes/all/tiddlers/{title:path}', endpoint=getTiddler, methods=['GET']
))

async def putTiddler(request : Request) -> Response:
  # Store (or modify) a tiddler.

  title = request.path_params['title']

  tiddlerDir = request.app.state.tiddlerDir

  tiddlerDict : dict[str, Any] = await request.json()

  # Undo silly TiddlyWeb formatting
  tiddlerFields : dict[str, Any] = tiddlerDict.pop('fields', {})
  tiddler : Tiddler = {}
  for aKey, aValue in tiddlerDict.items() :
    if isinstance(aValue, str) :
      tiddler[aKey] = aValue
  for aKey, aValue in tiddlerFields.items() :
    if isinstance(aValue, str) :
      tiddler[aKey] = aValue

  if "tags" in tiddlerDict:
    tiddler["tags"] = " ".join(
      f"[[{tag}]]" for tag in tiddlerDict.get("tags", [])
    )

  # Mandatory for TiddlyWeb but (but unused by this implementation)
  tiddler["bag"] = "bag"

  # Set revision to hash of Tiddler contents
  tiddler.pop("revision", None)
  hash = tiddlerHash(tiddler)
  tiddler["revision"] = revision = hash

  # Sanity check
  assert title == tiddler.get("title")

  filesWritten = writeTiddler(tiddlerDir, tiddler)

  etag = f'"bag/{title}/{revision}:{hash}"'
  headers = {"Etag": etag}

  if filesWritten :
    reloadTiddlyWiki(request.app)
    return Response("", status_code=204, headers=headers)
  else :
    return Response(
      f"ERROR: could not update {title}",
      status_code=404,
      headers=headers
    )

appRoutes.append(Route(
  '/recipes/all/tiddlers/{title:path}', endpoint=putTiddler, methods=['PUT']
))

async def removeTiddler(request : Request) -> Response :
  # Delete a tiddler.

  title = request.path_params['title']
  tiddlerDir = request.app.state.tiddlerDir

  deletedFiles = deleteTiddler(tiddlerDir, title)

  if deletedFiles :
    reloadTiddlyWiki(request.app)
    return HTMLResponse("")
  else:
    return Response(f"ERROR: could not delete {title}", status_code=404)

appRoutes.append(Route(
  '/bags/bag/tiddlers/{title:path}', endpoint=removeTiddler, methods=["DELETE"]
))

def createTiddlyWikiApp(aWiki : WikiDef) -> Starlette :
  """
  Create an Starlette application for the TiddlyServer.

  Parameters
  ==========
  emptyHtml  : Path
    The location of the empty.html for this tiddlyWiki
  baseHtml   : Path
    The location of the base.html for this tiddlyWiki
  tiddlerDir : Path
    The directory in which tiddlers will be stored.
  tiddlerUrl : str
    The base url for this tiddler wiki
  """

  # make the tiddler_dir relative to the baseDir
  tiddlerDir  = aWiki['dir']
  tiddlerUrl  = aWiki['url']
  tiddlerName = aWiki['name']

  logger.info(f"Tiddler: {tiddlerUrl}")
  logger.info(f"  from dir: {tiddlerDir}")

  # Create tiddler directory if it doesn't exist yet
  os.makedirs(tiddlerDir, exist_ok=True)

  # Create app
  tiddlerApp = Starlette(routes=appRoutes)
  tiddlerApp.state.emptyHtmlFilename = Path(aWiki['emptyHtml']).resolve()
  tiddlerApp.state.baseHtmlFilename  = Path(aWiki['baseHtml']).resolve()
  tiddlerApp.state.tiddlerDir        = Path(tiddlerDir).resolve()
  tiddlerApp.state.wikiUrl           = tiddlerUrl
  tiddlerApp.state.name              = tiddlerName

  return tiddlerApp

