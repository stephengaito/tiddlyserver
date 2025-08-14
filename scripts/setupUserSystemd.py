#!/usr/bin/env python

import os
import sys
import yaml

userSystemdDir = os.path.expanduser(
  "~/.config/systemd/user"
)

def usage() :
  print("""
  usage: setupTiddlyServerSystemd <tiddlyServerBasePath>

  where <TiddlyServerBasePath> is the path to the tiddlyServer's
        root directory which MUST contain the wikiConfig.yaml file.

  """)
  sys.exit(1)

def die(aMsg) :
  print(aMsg)
  sys.exit(1)

###########################################
# Load the tiddlyServer wiki configuration

if len(sys.argv) < 2 :
  usage()

tiddlyServerDir = os.path.abspath(sys.argv[1])
configPath = os.path.join(tiddlyServerDir, 'wikiConfig.yaml')
config = {}
try :
  with open(configPath) as yamlFile :
    config = yaml.safe_load(yamlFile.read())
except Exception as err :
  print(repr(err))
  die(f"Could not load the {configPath} configuration file")

if 'host' not in config : config['host'] = '127.0.0.1'
if 'port' not in config : config['port'] = '8980'

print("-------------------------------------------_")
print(yaml.dump(config))
print("-------------------------------------------_")

if 'wikis' not in config :
  die("No wikis found in the configuraiton file")

###########################################
# make sure required directories exist
os.system(f"mkdir -p {userSystemdDir}")
# os.system("mkdir -p ~/.local/bin")

###########################################
# now setup systemd for each listed wiki

for aWiki, aWikiDef in config['wikis'].items() :
  baseUnitPath = os.path.join(
    userSystemdDir, 'preload_' + aWiki + '_TiddlyWiki'
  )
  aWikiDir = aWiki
  if 'dir' in aWikiDef :
    aWikiDir = aWikiDef['dir']
  tiddlyWikiDir = os.path.join(
    tiddlyServerDir, aWikiDir
  )
  with open(baseUnitPath + '.path', 'w') as pathFile :
    pathFile.write(f"""[Unit]
Description=Watch the {aWiki} tiddlyWiki directory

[Path]
PathChanged={aWikiDir}/
Unit=preload_{aWiki}_TiddlyWiki.service

[Install]
WantedBy=default.target
""")

  with open(baseUnitPath + '.service', 'w') as serviceFile :
    serviceFile.write(f"""[Unit]
Description=Force the preloading of the {aWiki} tiddlyWiki

[Service]
ExecStart=curl --silent --output /dev/null \
  http://{config['host']}:{config['port']}/{aWiki}/preload

[Install]
WantedBy=default.target
""")

  # preloadTiddlyWikiScript = os.path.join(
  #   os.path.expanduser("~/.local/bin"),
  #   'preload_' + aWiki + '_TiddlyWiki'
  # )
  # with open(preloadTiddlyWikiScript, 'w') as scriptFile :
  #   scriptFile.write("""#!/bin/bash
  #
  # date >> /tmp/testPreloadTiddlyWiki
  # """)
  # os.system(f"chmod a+x {preloadTiddlyWikiScript}")

  os.system(f"echo systemctl --user enable {baseUnitPath}.path")
  os.system(f"echo systemctl --user enable {baseUnitPath}.service")
  os.system( "echo systemctl --user daemon-reload")

