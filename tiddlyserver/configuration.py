
import os
import sys
import yaml

def wikiDie(mesg, aWiki) :
  print(f"{mesg} in the wiki definition")
  print("-------------------------------------")
  print(yaml.dump(aWiki))
  print("-------------------------------------")
  sys.exit(1)

def checkAWiki(aWiki) :
  if 'title' not in aWiki :
    wikiDie("The title key must be supplied", aWiki)
  if 'url' not in aWiki :
    wikiDie("The url key must be supplied", aWiki)
  if 'dir' not in aWiki :
    wikiDie("The dir key must be supplied", aWiki)
  if 'desc' not in aWiki :
    aWiki['desc'] = ""
  if 'useGit' not in aWiki :
    aWiki['useGit'] = False

def configDie(mesg, config) :
  print(f"{mesg} in the 'wikiConfig.yaml' configuration file")
  print("-------------------------------------")
  print(yaml.dump(config))
  print("-------------------------------------")
  sys.exit(1)

def checkConfig(config) :
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
  if 'host' not in config : config['host'] = "127.0.0.1"
  if 'port' not in config : config['port'] = "8000"
  if 'verbose' not in config : config['verbose'] = False
  if 'static' not in config :
    configDie("The static key MUST be supplied", config)
  if 'url' not in config['static'] :
    configDie("The static::url key must be supplied", config)
  if 'dir' not in config['static'] :
    configDie("The static::dir key must be supplied", config)
  if 'wikis' not in config :
    configDie("The wikis key MUST be supplied", config)
  if config['wikis'] is None :
    configDie("The wikis key MUST be a list of wikis", config)
  if not isinstance(config['wikis'], list) :
    configDie("The wikis key MUST be a list of wikis", config)
  if len(config['wikis']) < 1 :
    configDie(
      "You MUST supply at least one multi-wiki in the wikis key",
      config
    )
  for aWiki in config['wikis'] : checkAWiki(aWiki)

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

