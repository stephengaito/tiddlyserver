"""
A Starlette based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

from typing import Any

import json
import os
from pathlib import Path
# import yaml

from starlette.applications import Starlette
from starlette.responses import Response, HTMLResponse, JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from tiddlyServer.types import Tiddler, TiddlerList

from tiddlyServer.tiddlerSerDes import readAllTiddlers, readTiddler, \
  writeTiddler, deleteTiddler

from tiddlyServer.tiddlerEmbedding import embedTiddlersIntoEmptyHtml
from tiddlyServer.tiddlerHash import tiddlerHash

# from tiddlyServer.wsgiLogger import WSGILogger

appRoutes : list[Route] = []

# @bp.before_request
# def log_requests() :
#   if has_request_context() :
#     print(request.url)
#     print(request.headers)

def packTiddlyWiki(
  emptyHtmlFilename : Path, tiddlerDir : Path, wikiUrl : str | None = None
) -> str :

  emptyHtml = emptyHtmlFilename.read_text()

  extraTiddlers : TiddlerList = []
  if wikiUrl :
    customPathPrefix = {
      'title': '$:/config/tiddlyweb/host',
      'text':  f'$protocol$//$host${wikiUrl}/'
    }
    extraTiddlers.append(customPathPrefix)

  # print(yaml.dump(customPathPrefix))

  tiddlers = sorted(
    readAllTiddlers(
      tiddlerDir,
      extraTiddlers=extraTiddlers
    ),
    key=lambda t: t.get("title", ""),
  )

  return embedTiddlersIntoEmptyHtml(emptyHtml, tiddlers)

def unpackTiddlyWiki(
  htmlFilename : Path, tiddlerDir : Path, baseHtmlFilename : Path
) :
  pass

def getIndex(request : Request) -> HTMLResponse :
  """
  Return a copy of the empty.html with all tiddlers in the tiddler directory
  pre-loaded.
  """
  # print(current_app.config['wiki_url'])
  # print("appRoute: /")

  html = packTiddlyWiki(
    request.app.state.config["emptyHtmlFilename"],
    request.app.state.config["tiddlerDir"],
    wikiUrl=str(request.app.state.config['wikiUrl'])
  )

  return HTMLResponse(html)

appRoutes.append(Route('/', getIndex))

def getStatus(request : Request) -> JSONResponse :
  """
  Bare-minimum response which minimises UI cruft like usernames and login
  screens.
  """
  return JSONResponse({
    "space": {"recipe": "all"},
    "username": "GUEST",
    "read_only": False,
    "anonymous": True,
  })

appRoutes.append(Route('/status', getStatus))

def getSkinnyTiddlers(request : Request) -> JSONResponse :
  """
  Return the JSON-ified non-text fields of all local tiddler files.

  NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  the TiddlyWiki implementation will cope just fine with a plain JSON object
  describing a tiddler's fields.
  """
  tiddlerDir = request.app.state.config["tiddlerDir"]
  skinnyTiddlers = list(readAllTiddlers(tiddlerDir, includeText=False))
  return JSONResponse(json.dumps(skinnyTiddlers))

appRoutes.append(Route('/recipes/all/tiddlers.json', getSkinnyTiddlers))

def getTiddler(request : Request, title : str) -> Response :
  """
  Read a tiddler.

  NB: We assume the 'all' space (reported by the /status endpoint).

  NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  the TiddlyWiki implementation will cope just fine with a plain JSON object
  describing a tiddler's fields.
  """
  tiddlerDir = request.app.state.config["tiddlerDir"]

  try:
    return JSONResponse(
      json.dumps(readTiddler(tiddlerDir, title))
    )
  except FileNotFoundError:
    return Response("", status_code=404)

async def putTiddler(request : Request, title : str) -> Response:
  # Store (or modify) a tiddler.

  tiddlerDir = request.app.state.config["tiddlerDir"]

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

  if "tags" in tiddler:
    tiddler["tags"] = " ".join(f"[[{tag}]]" for tag in tiddler.get("tags", []))

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
    return Response("", status_code=204, headers=headers)
  else :
    return Response(
      f"ERROR: could not update {title}",
      status_code=404,
      headers=headers
    )

async def getPutTiddler(request : Request) -> Response :
  title = request.path_params['title']
  if request.method == 'GET' :
    return getTiddler(request, title)
  elif request.method == 'PUT' :
    return await putTiddler(request, title)
  else :
    return Response(
      f"ERROR unknown request method : {request.method}", status_code=404
    )

appRoutes.append(Route(
  '/recipes/all/tiddlers/{title:path}', getPutTiddler, methods=['GET', 'PUT']
))

def removeTiddler(request : Request) -> Response :
  """
  Delete a tiddler.
  """
  title = request.path_params['title']
  tiddlerDir = request.app.state.config["tiddlerDir"]

  deletedFiles = deleteTiddler(tiddlerDir, title)

  if deletedFiles :
    return HTMLResponse("")
  else:
    return Response(f"ERROR: could not delete {title}", status_code=404)

appRoutes.append(Route(
  '/bags/bag/tiddlers/{title:path}', removeTiddler, methods=["DELETE"]
))

def createApp(aWiki : dict[str, str]) -> Starlette :
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
  tiddlerDir = aWiki['dir']
  tiddlerUrl = aWiki['url']
  print(f"Tiddler: {tiddlerUrl}\n  from dir: {tiddlerDir}")

  # Create tiddler directory if it doesn't exist yet
  os.makedirs(tiddlerDir, exist_ok=True)

  # Create app
  tiddlerApp = Starlette(routes=appRoutes)
  tiddlerApp.state.emptyHtmlFilename = Path(aWiki['emptyHtml']).resolve()
  tiddlerApp.state.baseHtmlFilename  = Path(aWiki['baseHtml']).resolve()
  tiddlerApp.state.tiddlerDir        = Path(tiddlerDir).resolve()
  tiddlerApp.state.wikiUrl           = tiddlerUrl

  return tiddlerApp
