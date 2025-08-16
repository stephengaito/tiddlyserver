
import os
import shutil
import sys
import yaml

def basePath(baseDir, aPath) :
  if not os.path.isabs(aPath) :
    aPath = os.path.join(baseDir, aPath)
  return aPath

def wikiDie(mesg, aWiki) :
  print(f"{mesg} in the wiki definition")
  print("-------------------------------------")
  print(yaml.dump(aWiki))
  print("-------------------------------------")
  sys.exit(1)

def checkAWiki(aKey, aWiki, config) :
  if 'title' not in aWiki :
    wikiDie("The title key must be supplied", aWiki)
  if 'url' not in aWiki :
    aWiki['url'] = '/' + aKey
  if 'dir' not in aWiki :
    aWiki['dir'] = aKey
  aWiki['dir'] = basePath(
    config['baseDir'], aWiki['dir']
  )
  if not os.path.isdir(aWiki['dir']) :
    os.makedirs(aWiki['dir'], exist_ok=True)
  if 'desc' not in aWiki :
    aWiki['desc'] = ""
  if 'baseHtml' not in aWiki :
    aWiki['baseHtml'] = basePath(aWiki['dir'], 'base.html')
  if not os.path.isfile(aWiki['baseHtml']) :
    shutil.copyfile(config['baseHtml'], aWiki['baseHtml'])
  if 'emptyHtml' not in aWiki :
    aWiki['emptyHtml'] = basePath(aWiki['dir'], 'empty.html')
  if not os.path.isfile(aWiki['emptyHtml']) :
    shutil.copyfile(config['emptyHtml'], aWiki['emptyHtml'])

def configDie(mesg, config) :
  print(f"{mesg} in the 'wikiConfig.yaml' configuration file")
  print("-------------------------------------")
  print(yaml.dump(config))
  print("-------------------------------------")
  sys.exit(1)

def checkTemplate(config) :
  if 'template' not in config :
    config['template'] = os.path.join(
      os.path.abspath(os.path.dirname(__file__)),
      "defaultWiki.html"
    )
  else :
    config['template'] = os.path.join(
      config['baseDir'],
      config['template']
    )

def checkDefaultHtml(config) :
  if 'baseHtml' not in config :
    config['baseHtml'] = basePath(
      config['baseDir'], 'base.html'
    )
  if not os.path.isfile(config['baseHtml']) :
    configDie("The default base.html file MUST exist")
  if 'emptyHtml' not in config :
    config['emptyHtml'] = basePath(
      config['baseDir'], 'empty.html'
    )
  if not os.path.isfile(config['emptyHtml']) :
    configDie("The default empty.html file MUST exist")

def checkStatic(config) :
  if 'static' not in config :
    configDie("The static key MUST be supplied", config)
  if 'url' not in config['static'] :
    configDie("The static::url key must be supplied", config)
  if 'dir' not in config['static'] :
    configDie("The static::dir key must be supplied", config)
  config['static']['dir'] = basePath(
    config['baseDir'], config['static']['dir']
  )
  if not os.path.isdir(config['static']['dir']) :
    configDie("The static directory MUST exist")

def checkWikis(config) :
  if 'wikis' not in config :
    configDie("The wikis key MUST be supplied", config)
  if config['wikis'] is None :
    configDie("The wikis key MUST be a dictionary of wikis", config)
  if not isinstance(config['wikis'], dict) :
    configDie("The wikis key MUST be a dictionary of wikis", config)
  if len(config['wikis']) < 1 :
    configDie(
      "You MUST supply at least one multi-wiki in the wikis key",
      config
    )
  for aKey, aWiki in config['wikis'].items() :
    checkAWiki(aKey, aWiki, config)
  if 'wikiOrder' not in config :
    config['wikiOrder'] = sorted(config['wikis'].keys())
  for aWikiKey in config['wikiOrder'] :
    if aWikiKey not in config['wikis'] :
      configDie(f"The '{aWikiKey}' wiki key is not found in wikis", config)

def checkConfig(config) :
  checkTemplate(config)
  if 'host' not in config : config['host'] = "127.0.0.1"
  if 'port' not in config : config['port'] = "8000"
  checkDefaultHtml(config)
  checkStatic(config)
  if 'verbose' not in config : config['verbose'] = False
  checkWikis(config)

def loadConfig(baseDir) :
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

  if config['verbose'] :
    print("-------------------------------------")
    print(yaml.dump(config))
    print("-------------------------------------")
  return config

