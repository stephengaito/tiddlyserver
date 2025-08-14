"""
An :py:mod:`flask` based webserver implementing (a bare-bones subset of) the
TiddlyWeb API.
"""

import inspect

from pathlib import Path

# import yaml

from flask import Flask, Blueprint, Response, \
  current_app, jsonify, abort, request  # , has_request_context

import tiddlyserver

from tiddlyserver.tiddler_serdes import (
  read_all_tiddlers,
  read_tiddler,
  write_tiddler,
  delete_tiddler,
)

from tiddlyserver.tiddler_embedding import embed_tiddlers_into_empty_html


from tiddlyserver.tiddler_hash import tiddler_hash

from tiddlyserver.git import (
  init_repo_if_needed,
  commit_files_if_changed,
)

# from tiddlyserver.wsgiLogger import WSGILogger

bp = Blueprint("tiddlyserver", __name__)

def tiddler_git_filter(tiddler: dict[str, str]) -> bool:
  """
  Return True only for Tiddlers which should be included in Git.
  """
  shouldFilter = True

  # Ignore drafts
  shouldFilter = shouldFilter and tiddler.get("draft.of", None) is None

  # Skip the storylist
  shouldFilter = shouldFilter and tiddler.get("title") != "$:/StoryList"

  # Allow manual override
  shouldFilter = shouldFilter and tiddler.get("tiddlyserver.git") != "no"

  return (shouldFilter)

# @bp.before_request
# def log_requests() :
#   if has_request_context() :
#     print(request.url)
#     print(request.headers)

def packTiddlyWiki(
  empty_html_filename, tiddler_dir, wiki_url=None
) :

  empty_html = empty_html_filename.read_text()

  extraTiddlers = []
  if wiki_url :
    customPathPrefix = {
      'title': '$:/config/tiddlyweb/host',
      'text':  f'$protocol$//$host${wiki_url}/'
    }
    extraTiddlers.append(customPathPrefix)

  # print(yaml.dump(customPathPrefix))

  tiddlers = sorted(
    read_all_tiddlers(
      tiddler_dir,
      extraTiddlers=extraTiddlers
    ),
    key=lambda t: t.get("title", ""),
  )

  return embed_tiddlers_into_empty_html(empty_html, tiddlers)

def unpackTiddlyWiki(
  html_filename,
  tiddler_dir,
  base_html_filename,
) :
  pass

@bp.route('/')
def get_index():
  """
  Return a copy of the empty.html with all tiddlers in the tiddler directory
  pre-loaded.
  """
  # print(current_app.config['wiki_url'])
  # print("appRoute: /")

  html = packTiddlyWiki(
    Path(current_app.config["empty_html_filename"]),
    Path(current_app.config["tiddler_dir"]),
    wiki_url=str(current_app.config['wiki_url'])
  )

  return Response(html, content_type="text/html")

@bp.route('/status')
def get_status():
  """
  Bare-minimum response which minimises UI cruft like usernames and login
  screens.
  """
  return {
    "space": {"recipe": "all"},
    "username": "GUEST",
    "read_only": False,
    "anonymous": True,
  }

@bp.route('/recipes/all/tiddlers.json')
def get_skinny_tiddlers():
  """
  Return the JSON-ified non-text fields of all local tiddler files.

  NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  the TiddlyWiki implementation will cope just fine with a plain JSON object
  describing a tiddler's fields.
  """
  tiddler_dir = current_app.config["tiddler_dir"]
  skinny_tiddlers = list(read_all_tiddlers(tiddler_dir, include_text=False))
  return jsonify(skinny_tiddlers)

@bp.route('/recipes/all/tiddlers/<path:title>')
def get_tiddler(title):
  """
  Read a tiddler.

  NB: We assume the 'all' space (reported by the /status endpoint).

  NB: We don't emulate the slightly quirky TiddlyWeb JSON format here since
  the TiddlyWiki implementation will cope just fine with a plain JSON object
  describing a tiddler's fields.
  """
  tiddler_dir = current_app.config["tiddler_dir"]

  try:
    return jsonify(read_tiddler(tiddler_dir, title))
  except FileNotFoundError:
    abort(404)

@bp.route('/recipes/all/tiddlers/<path:title>', methods=["PUT"])
def put_tiddler(title):
  """
  Store (or modify) a tiddler.
  """
  tiddler_dir = current_app.config["tiddler_dir"]
  use_git = current_app.config["use_git"]

  tiddler = request.get_json()

  # Undo silly TiddlyWeb formatting
  tiddler.update(tiddler.pop("fields", {}))
  if "tags" in tiddler:
    tiddler["tags"] = " ".join(f"[[{tag}]]" for tag in tiddler.get("tags", []))

  # Mandatory for TiddlyWeb but (but unused by this implementation)
  tiddler["bag"] = "bag"

  # Set revision to hash of Tiddler contents
  tiddler.pop("revision", None)
  hash = tiddler_hash(tiddler)
  tiddler["revision"] = revision = hash

  # Sanity check
  assert title == tiddler.get("title")

  changed_files = write_tiddler(tiddler_dir, tiddler)
  if use_git and tiddler_git_filter(tiddler):
    commit_files_if_changed(tiddler_dir, changed_files, f"Updated {title}")

  etag = f'"bag/{title}/{revision}:{hash}"'
  headers = {"Etag": etag}

  return "", 204, headers

@bp.route('/bags/bag/tiddlers/<path:title>', methods=["DELETE"])
def remove_tiddler(title):
  """
  Delete a tiddler.
  """
  tiddler_dir = current_app.config["tiddler_dir"]
  use_git = current_app.config["use_git"]

  deleted_files = delete_tiddler(tiddler_dir, title)

  if use_git:
    commit_files_if_changed(tiddler_dir, deleted_files, f"Deleted {title}")

  if deleted_files:
    return ""
  else:
    abort(404)

def create_app(aWiki) -> Flask:
  """
  Create an :py:class:`flask.Flask` application for the TiddlyServer.

  Parameters
  ==========
  baseDir : Path
    The base directory of all tiddler wikis served by this TiddlyServer
  tiddler_dir : Path
    The directory in which tiddlers will be stored.
  tiddler_url : str
    The base url for this tiddler wiki
  use_git : bool
    If True, will ensure the tiddler directory is a git repository and
    auto-commit changes to that repository.
  """

  # make the tiddler_dir relative to the baseDir
  tiddler_dir = Path(aWiki['dir'])
  tiddler_url = aWiki['url']
  print(f"Tiddler: {tiddler_url}\n  from dir: {tiddler_dir}")

  # Create tiddler directory if it doesn't exist yet
  if not tiddler_dir.is_dir():
    tiddler_dir.mkdir(parents=True)

  # create the empty HTML if it doesn't exist yet
  empty_html_filename = Path(aWiki['emptyHtml'])
  base_html_filename  = Path(aWiki['baseHtml'])

  if aWiki['useGit'] :
    init_repo_if_needed(tiddler_dir)
    commit_files_if_changed(
      tiddler_dir,
      [empty_html_filename, base_html_filename],
      "Updated empty.html and base.html"
    )

  # Create app
  tiddlerApp = Flask(__name__)
  tiddlerApp.register_blueprint(bp)
  tiddlerApp.config["empty_html_filename"] = empty_html_filename
  tiddlerApp.config["base_html_filename"]  = base_html_filename
  tiddlerApp.config["tiddler_dir"] = tiddler_dir.resolve()
  tiddlerApp.config["use_git"] = aWiki['useGit']
  tiddlerApp.config['wiki_url'] = tiddler_url

  # loggerApp = WSGILogger(
  #   tiddlerApp, mesg=f"tiddlerApp: {tiddler_url}",
  #   keys=['PATH_INFO']
  # )
  # return loggerApp

  return tiddlerApp
