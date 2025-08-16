
from typing import cast, Any

from pathlib import Path

from markdown import markdown
from jinja2 import Template

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from tiddlyServer.types import WikiDefs
from tiddlyServer.tiddlyWikiApp import createTiddlyWikiApp

def createBaseApp(
  baseDir : Path, config : dict[str, Any]
) -> Starlette :

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
    Route('/', listWikis),
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
    Route('/{path:path}', listWikis),
  )

  app = Starlette(routes=routes)
  return app

