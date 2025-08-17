
from typing import cast, Any

import logging
from pathlib import Path

from markdown import markdown
from jinja2 import Template

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from tiddlyServer.types import WikiDefs
from tiddlyServer.tiddlyWikiApp import createTiddlyWikiApp
from tiddlyServer.preLoader import appLifespan

logger = logging.getLogger('tiddlyWiki')

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
  logger.info(f"StaticDir: {staticDir}")

  if not staticDir.is_dir() :
    staticDir.mkdir(parents=True)

  routes.append(
    Mount(
      staticDef['url'],
      app=StaticFiles(directory=staticDir),
      name='static'
    )
  )

  wikiApps : list[Starlette] = []
  for aWikiName, aWiki in wikis.items() :
    aWiki['desc'] = markdown(aWiki['desc'])
    theWikiApp = createTiddlyWikiApp(aWiki)
    wikiApps.append(theWikiApp)
    routes.append(
      Mount(
        aWiki['url'],
        app=theWikiApp,
        name=aWikiName
      )
    )

  routes.append(
    Route('/{path:path}', endpoint=listWikis, methods=['GET']),
  )

  app = Starlette(routes=routes, lifespan=appLifespan)
  app.state.wikiApps = wikiApps
  return app

