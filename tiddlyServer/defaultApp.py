
from typing import cast

from markdown import markdown

from copy import deepcopy

from jinja2 import Template

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

def createBaseApp(config : dict[str, dict[str, dict[str,str]]]) -> Starlette :

  wikis = deepcopy(config['wikis'])
  for aWiki in wikis.values() :
    aWiki['desc'] = markdown(aWiki['desc'])

  def listWikis(request : Request, path : str = '') :
    resultHtml = "No wikis found"
    templatePath : str = cast(str, config['template'])
    templateStr : str = ''
    with open(templatePath) as tFile :
      templateStr = tFile.read()
    template = Template(templateStr)
    resultHtml = template.render(
      wikis=config['wikis'],
      wikiOrder=config['wikiOrder']
    )
    return HTMLResponse(resultHtml)

  app = Starlette(routes=[
    Route('/', listWikis),
    Mount('/static', StaticFiles(directory='static'), name='static'),
    Route('/{path:path}', listWikis),
  ])
  return app

