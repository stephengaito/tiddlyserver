
from typing import cast, Any

import contextlib
from pathlib import Path

from markdown import markdown
from jinja2 import Template

from anyio import create_task_group

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from tiddlyServer.types import WikiDefs
from tiddlyServer.tiddlyWikiApp import createTiddlyWikiApp

async def preloadTiddlyWiki(wikiApp) :
  pass
  # using the wikiApp and its associated state...
  # wait for the wikiLoadEvent
  # clear the wikiLoadEvent
  # load the wiki
  # assert the wikiLoadedEvent
  # do it all again

@contextlib.asynccontextmanager
async def appLifespan(app):
  async with create_task_group() as tg :
    print("Run at startup!")
    with aWikiApp in app.state.wikiApps :
      pass
      # with each app, add wikiLoaded, wikiNeedsLoading events
      # assert the wikiNeedsLoading event
      # and then start the preloadTiddlyWiki for aWikiApp
    yield
    print("Run on shutdown!")

def createBaseApp(
  baseDir : Path, config : dict[str, Any]
) -> Starlette :

  def corsOptions(request : Request) -> Response :
    return Response(
      "", headers={
        'Allow' : 'OPTIONS,GET,HEAD,PUT,DELETE'
      }
    )

  wikis : WikiDefs = cast(WikiDefs, config['wikis'])
  wikiOrder : list[str] = cast(
    list[str], config['wikiOrder']
  )

  def listWikis(request : Request) -> HTMLResponse :
    resultHtml = "No wikis found"
    templatePath : str = cast(str, config['template'])
    templateStr : str = ''
    with open(templatePath) as tFile :
      templateStr = tFile.read()
    template = Template(templateStr)
    resultHtml = template.render(
      wikis=wikis,
      wikiOrder=wikiOrder
    )
    return HTMLResponse(resultHtml)

  routes : list[Route | Mount] = [
    Route('/', endpoint=listWikis, methods=['GET']),
    Route('/', endpoint=corsOptions, methods=['OPTIONS']),
  ]

  staticDef : dict[str,str] = cast(dict[str,str], config['static'])

  staticDir = Path(staticDef['dir'])
  if not staticDir.is_absolute() :
    staticDir = baseDir / staticDef['dir']
  print(f"StaticDir: {staticDir}")

  if not staticDir.is_dir() :
    staticDir.mkdir(parents=True)

  routes.append(
    Mount(
      staticDef['url'],
      app=StaticFiles(directory=staticDir),
      name='static'
    )
  )

  for aWikiName, aWiki in wikis.items() :
    aWiki['desc'] = markdown(aWiki['desc'])
    routes.append(
      Mount(
        aWiki['url'],
        app=createTiddlyWikiApp(aWiki),
        name=aWikiName
      )
    )

  routes.append(
    Route('/{path:path}', endpoint=listWikis, methods=['GET']),
  )

  app = Starlette(routes=routes, lifespan=appLifespan)
  return app

