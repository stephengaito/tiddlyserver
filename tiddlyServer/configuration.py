
from typing import NoReturn, Any, cast

import os
import shutil
import sys
import yaml

from tiddlyServer.types import WikiDef, WikiDefs

def basePath(baseDir : str, aPath : str) -> str :
  if not os.path.isabs(aPath) :
    aPath = os.path.join(baseDir, aPath)
  return aPath

def wikiDie(mesg : str, aWiki : WikiDef) -> NoReturn :
  print(f"{mesg} in the wiki definition")
  print("-------------------------------------")
  print(yaml.dump(aWiki))
  print("-------------------------------------")
  sys.exit(1)

def checkAWiki(
  aKey : str, aWiki : WikiDef, config : dict[str, Any]
) -> None :

  baseDir   : str = cast(str, config['baseDir'])
  baseHtml  : str = cast(str, config['baseHtml'])
  emptyHtml : str = cast(str, config['emptyHtml'])

  if 'title' not in aWiki :
    wikiDie("The title key must be supplied", aWiki)
  if 'url' not in aWiki :
    aWiki['url'] = '/' + aKey
  if 'dir' not in aWiki :
    aWiki['dir'] = aKey
  aWiki['dir'] = basePath(baseDir, aWiki['dir'])
  if not os.path.isdir(aWiki['dir']) :
    os.makedirs(aWiki['dir'], exist_ok=True)
  if 'desc' not in aWiki :
    aWiki['desc'] = ""
  if 'baseHtml' not in aWiki :
    aWiki['baseHtml'] = basePath(aWiki['dir'], 'base.html')
  if not os.path.isfile(aWiki['baseHtml']) :
    shutil.copyfile(baseHtml, aWiki['baseHtml'])
  if 'emptyHtml' not in aWiki :
    aWiki['emptyHtml'] = basePath(aWiki['dir'], 'empty.html')
  if not os.path.isfile(aWiki['emptyHtml']) :
    shutil.copyfile(emptyHtml, aWiki['emptyHtml'])

def configDie(mesg : str, config : dict[str, Any]) -> NoReturn :
  print(f"{mesg} in the 'wikiConfig.yaml' configuration file")
  print("-------------------------------------")
  print(yaml.dump(config))
  print("-------------------------------------")
  sys.exit(1)

def checkTemplate(config : dict[str, Any]) -> None :
  if 'template' not in config :
    config['template'] = os.path.join(
      os.path.abspath(os.path.dirname(__file__)),
      "defaultWiki.html"
    )
  else :
    config['template'] = os.path.join(
      cast(str, config['baseDir']),
      cast(str, config['template'])
    )

def checkDefaultHtml(config : dict[str, Any]) -> None :
  if 'baseHtml' not in config :
    config['baseHtml'] = basePath(
      cast(str, config['baseDir']), 'base.html'
    )
  if not os.path.isfile(config['baseHtml']) :
    configDie("The default base.html file MUST exist", config)
  if 'emptyHtml' not in config :
    config['emptyHtml'] = basePath(
      cast(str, config['baseDir']), 'empty.html'
    )
  if not os.path.isfile(config['emptyHtml']) :
    configDie("The default empty.html file MUST exist", config)

def checkStatic(config : dict[str, Any]) -> None :
  if 'static' not in config :
    configDie("The static key MUST be supplied", config)

  configStatic : dict[str,str] = cast(dict[str,str], config['static'])

  if 'url' not in configStatic :
    configDie("The static::url key must be supplied", config)
  if 'dir' not in configStatic :
    configDie("The static::dir key must be supplied", config)
  configStatic['dir'] = basePath(
    cast(str, config['baseDir']), configStatic['dir']
  )
  if not os.path.isdir(configStatic['dir']) :
    configDie("The static directory MUST exist", config)

def checkWikis(config : dict[str, Any]) -> None :
  if 'wikis' not in config :
    configDie("The wikis key MUST be supplied", config)
  if config['wikis'] is None :
    configDie("The wikis key MUST be a dictionary of wikis", config)
  if not isinstance(config['wikis'], dict) :
    configDie("The wikis key MUST be a dictionary of wikis", config)

  configWikis : WikiDefs = cast(WikiDefs, config['wikis'])

  if len(configWikis) < 1 :
    configDie(
      "You MUST supply at least one multi-wiki in the wikis key",
      config
    )
  for aKey, aWiki in configWikis.items() :
    checkAWiki(aKey, aWiki, config)

  if 'wikiOrder' not in config :
    config['wikiOrder'] = sorted(config['wikis'].keys())

  for aWikiKey in config['wikiOrder'] :
    if aWikiKey not in config['wikis'] :
      configDie(f"The '{aWikiKey}' wiki key is not found in wikis", config)

def checkConfig(config : dict[str, Any]) -> None :
  checkTemplate(config)
  if 'host' not in config : config['host'] = "127.0.0.1"
  if 'port' not in config : config['port'] = "8000"
  checkDefaultHtml(config)
  checkStatic(config)
  if 'verbose' not in config : config['verbose'] = False
  checkWikis(config)

def loadConfig(baseDir : str) -> dict[str,Any] :
  config = {}

  try :
    with open(os.path.join(baseDir, "wikiConfig.yaml")) as cFile :
      config = yaml.safe_load(cFile.read())
      if not config : config = {}
  except Exception as err :
    print(f"Could not open the wikiConfig.yaml file in the base dir: {baseDir}")  # noqa
    print(repr(err))
    sys.exit(1)

  config['baseDir'] = baseDir
  checkConfig(config)

  if cast(bool, config['verbose']) :
    print("-------------------------------------")
    print(yaml.dump(config))
    print("-------------------------------------")
  return config

