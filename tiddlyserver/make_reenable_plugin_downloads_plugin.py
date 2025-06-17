"""
Generate a TiddlyWiki plugin which reenables the plugin download UI in the
control panel (when TiddlyWeb has disabled it).

This plugin works by overwriting TiddlyWeb's
``$:/config/OfficialPluginLibrary`` shaddow tiddler with the shaddow tiddler of
that name defined by the core plugin. This tiddler hard-codes the URL of the
plugin repository for that TiddlyWiki version and so is specific to a
particular TiddlyWiki version, hence generating it dynamically here.
"""

from pathlib import Path

import argparse

import json

import sys

from tiddlyserver.tiddler_embedding import HTMLTagOffsetFinder

from tiddlyserver.server import EMPTY_WITH_TIDDLYWEB


def extract_core_official_plugin_library_tiddler_and_version(
  empty_html_path: Path,
) -> tuple[dict[str, str], str]:
  officialPluginLib = None
  version           = None

  finder = HTMLTagOffsetFinder([
    ("script", {"class": "tiddlywiki-tiddler-store"}),
  ])
  empty_html = empty_html_path.read_text()
  finder.feed(empty_html)

  _tag, attrs, start, end = finder.matches[0][0]
  tiddlerStore = empty_html[start:end]
  jsonStore = json.loads(tiddlerStore)
  for aLibrary in jsonStore :
    if 'title' in aLibrary :
      if 'core' in aLibrary['title'] :
        if 'version' in aLibrary :
          version = aLibrary['version']
        if 'text' in aLibrary :
          if 'tiddlers' in aLibrary['text'] :
            libText = aLibrary['text'].strip("'\"")
            libJson = json.loads(libText)
            if "$:/config/OfficialPluginLibrary" in libJson['tiddlers'] :
              officialPluginLib = libJson['tiddlers']["$:/config/OfficialPluginLibrary"]  # noqa
    if version and officialPluginLib :
      break
  if not version or not officialPluginLib :
    print("ERROR: Could not find the officialPluginLib")
    sys.exit(1)

  return (
    officialPluginLib,
    version,
  )

def make_plugin(empty_html_path: Path) -> dict[str, str]:
  (
    official_plugin_library,
    core_version,
  ) = extract_core_official_plugin_library_tiddler_and_version(empty_html_path)

  official_plugin_library["tiddlyserver.git"] = "no"

  return {
    "title": "$:/plugins/mossblaser/reenable-plugin-downloads",
    "author": "mossblaser",
    "version": core_version,
    "core-version": f"=={core_version}",
    "description": "Renable the plugin download UI when TiddlyWeb is enabled",
    "plugin-type": "plugin",
    "plugin-priority": 20,
    "type": "application/json",
    "text": json.dumps(official_plugin_library)
  }

def main() -> None:
  parser = argparse.ArgumentParser(
    description="""
      Generate a plugin which reenables plugin downloads in TiddlyWiki
      when TiddlyWeb is enabled.
    """
  )

  parser.add_argument(
    "output",
    type=Path,
    help="""
      The name of the JSON file to write the plugin to.
    """
  )

  parser.add_argument(
    "--empty-html", "-e",
    type=Path,
    default=EMPTY_WITH_TIDDLYWEB,
    help="""
      Filename of the empty.html file with the version of TiddlyWiki to
      generate the plugin for. Defaults to the version of TiddlyWiki
      shipped with TiddlyServer.
    """
  )

  args = parser.parse_args()

  json.dump([make_plugin(args.empty_html)], args.output.open("w"))

if __name__ == "__main__":
    main()

