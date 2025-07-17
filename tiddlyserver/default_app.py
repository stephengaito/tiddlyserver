
from markdown import markdown

from copy import deepcopy
from flask import Flask, render_template_string

def createBaseApp(config) :

  wikis = deepcopy(config['wikis'])
  for aWiki in wikis.values() :
    aWiki['desc'] = markdown(aWiki['desc'])

  app = Flask(__name__)

  @app.get('/', defaults={'path': ''})
  @app.get('/<path:path>')
  def listWikis(path) :
    resultHtml = "No wikis found"
    with open(config['template']) as tFile :
      resultHtml = render_template_string(
        tFile.read(),
        wikis=config['wikis'],
        wikiOrder=config['wikiOrder']
      )
    return resultHtml

  return app

