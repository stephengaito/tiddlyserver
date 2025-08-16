"""
Routines for inserting tiddlers into an ``empty.html`` TiddlyWiki file.
"""

from typing import Optional, cast

from html import escape
from html.parser import HTMLParser
import json
import logging

from tiddlyServer.types import Tiddler, Tiddlers

class HTMLTagOffsetFinder(HTMLParser):
  """
  A :py:class:`html.parser.HTMLParser` derrivative which finds the start and
  end character offsets of the contents of tags with defined names and
  attributes.
  """

  _to_find: list[tuple[str, set[tuple[str, str]]]]

  _chars_fed: int
  """The number of chars already fed to the feed function."""

  _lineno_to_offset: list[int]
  """
  The character offsets of the start of each line fed to this class.
  """

  _tag_stack: list[tuple[str, set[tuple[str, str | None ]], int]]
  """
  Stack of tags the parser is currently inside. Each entry in the stack is a
  (tag, attrs, start_offset).
  """

  matches: list[list[tuple[str, dict[str, str | None], int, int]]]
  """
  All offsets for matching tags, one list for each pattern supplied. Each
  entry in the stack is a (tag, attrs, start_offset, end_offset).
  """

  # to_find IS NOT a Tiddler....
  def __init__(self, to_find: list[tuple[str, dict[str, str]]]) -> None:
    """
    Find the start and end offsets of all tags listed in the 'to_find'
    list (given as lower-case-tag-name, attribute-dict pairs.
    """
    super().__init__()
    self._to_find = [(tag, set(attrs.items())) for tag, attrs in to_find]

    self._chars_fed = 0
    self._lineno_to_offset = [0]

    self._tag_stack = []
    self.matches = [[] for _ in self._to_find]

  def feed(self, string: str) -> None:
    # Find the line start offsets for this batch of data
    for i, c in enumerate(string):
      if c == "\n":
        self._lineno_to_offset.append(self._chars_fed + i + 1)
    self._chars_fed += len(string)

    super().feed(string)

  def get_offset(self) -> int:
    line, col = self.getpos()
    return self._lineno_to_offset[line - 1] + col

  def handle_starttag(
    self, tag: str, attrs: list[tuple[str, str | None]]
  ) -> None:
    startTagText = self.get_starttag_text()
    if not startTagText : startTagText = ""
    start_offset = self.get_offset() + len(startTagText)
    self._tag_stack.append((tag, set(attrs), start_offset))

  def handle_endtag(self, end_tag: str) -> None:
    # Crudely pop any tags which don't have matching closing tags, ignoring
    # them entirely since we don't actually need to be able to find them
    # for this application.
    while self._tag_stack[-1][0] != end_tag:
      self._tag_stack.pop(-1)

    tag, attrs, start_offset = self._tag_stack.pop(-1)
    end_offset = self.get_offset()

    for (target_tag, target_attrs), matches in zip(self._to_find, self.matches):  # noqa
      if tag == target_tag and target_attrs.issubset(attrs):
        matches.append((tag, dict(attrs), start_offset, end_offset))

def modify_string(
  string: str,
  insertions: list[tuple[int, str]] = [],
  deletions: list[tuple[int, int]] = [],
) -> str:
  """
  Modify a string by inserting new substrings at a provided set of offsets
  and by deleting defined regions of the string.

  Deletion ranges must not overlap eachother or insertion points. Multiple
  values may be inserted at a given point and will be inserted one after
  another in the order given in that case.
  """
  ranges = sorted([(i, i) for i, s in insertions] + deletions)
  for (s1, e1), (s2, e2) in zip(ranges[:-1], ranges[1:]):
    if s2 < e1:
      raise ValueError("Overlapping insertions or deletions")

  parts = []
  changes : list[tuple[int, int | str]] = []
  changes = cast(list[tuple[int, int | str]], deletions) + \
    cast(list[tuple[int, int | str]], insertions[::-1])
  for change in sorted(changes, key=lambda x: x[0], reverse=True):  # noqa
    if isinstance(change[1], str):  # Insertion
      offset, substring = change
      parts.append(string[offset:])
      parts.append(cast(str, substring))
      string = string[:offset]
    else:  # Deletion
      start, end = change
      parts.append(string[cast(int, end):])
      string = string[:start]
  parts.append(string)
  return "".join(reversed(parts))

def getTitleAndSubtitle(
  tiddlers: Tiddlers
) -> tuple[Optional[str], Optional[str]]:
  """
  Get the wiki title and subtitles defined in the given set of tiddlers (if a
  custom title/subtitle is defined).
  """
  title: Optional[str] = None
  subtitle: Optional[str] = None
  for tiddler in tiddlers:
    if tiddler.get("title") == "$:/SiteTitle":
      title = tiddler.get("text")
    elif tiddler.get("title") == "$:/SiteSubtitle":
      subtitle = tiddler.get("text")

  return (title, subtitle)

def serialiseAsJsonTiddler(tiddler: Tiddler) -> str:
  """
  Given a Tiddler, return the JSON for the 'tiddlywiki-tiddler-store'
  serialisation format used by TiddlyWiki.
  """
  return json.dumps(tiddler)

def serialiseAsTextTiddler(tiddler: Tiddler) -> str:
  """
  Given a Tiddler, return the HTML for the 'text' serialisation format used
  by TiddlyWiki.
  """
  attrs = "".join(
    f' {field}="{escape(value, quote=True)}"'
    for field, value in tiddler.items()
    if field != "text"
  )
  text = tiddler.get("text", "")
  return f"<div{attrs}><pre>{escape(text, quote=False)}</pre></div>"

class UnexpectedHTMLStructureError(ValueError):
  """
  Exception thrown when the TiddlyWiki HTML does not contain the expected
  structures. Perhaps the file is malformed or the format has changed in the
  version supplied?
  """

def embedTiddlersIntoEmptyHtml(
  html: str, tiddlers: Tiddlers
) -> str:
  """
  Given the HTML of an empty TiddlyWiki, embed the provided tiddlers.
  """
  # Find the <title> tag, Javascript disabled message (which contains a stale
  # list of tiddlers) and tiddler store area.
  finder = HTMLTagOffsetFinder(
    [
      ("title", {}),
      ("noscript", {}),
      ("script", {"class": "tiddlywiki-tiddler-store"}),
      # ("div", {"id": "storeArea"}),
    ]
  )
  finder.feed(html)
  if len(finder.matches[0]) != 1:
    raise UnexpectedHTMLStructureError("Expected exactly one <title>")
  if len(finder.matches[1]) != 1:
    raise UnexpectedHTMLStructureError("Expected exactly one <noscript>")
  if len(finder.matches[2]) != 1:
    raise UnexpectedHTMLStructureError("Expected exactly one store area")
  _tag, _attrs, title_start, title_end = finder.matches[0][0]
  _tag, _attrs, noscript_start, noscript_end = finder.matches[1][0]
  _tag, _attrs, _store_area_start, store_area_end = finder.matches[2][0]

  insertions = []
  deletions = []

  # Change <title> as necessary
  title, subtitle = getTitleAndSubtitle(tiddlers)
  if title is not None:
    if subtitle is not None:
      title += f" \N{EM DASH} {subtitle}"
    deletions.append((title_start, title_end))
    insertions.append((title_start, title))

  # Remove noscript content (arguably we should add the tiddler title list
  # but, honestly, I can't be bothered right now...
  deletions.append((noscript_start, noscript_end))
  insertions.append((noscript_start,  "Please enable Javascript"))

  # Check for (unsupported) RawMarkup tiddlers (which we can't embed by just
  # stuffing them in to the store area).
  for tiddler in tiddlers:
    if "$:/tags/RawMarkup" in tiddler.get("tags", ""):
      logging.error(
        f"Could not correctly render RawMarkup tiddler {tiddler.get('title', '')}"  # noqa
      )

  # Add tiddlers
  #
  # In the v5.2.x style tiddler store, each tiddler MUST be separated by a
  # comma and be on a line of its own.
  #
  def sortByTitle(aTiddler : Tiddler ) -> str :
    return aTiddler.get("title", "")
  serialised_tiddlers = []
  for aTiddler in  sorted(tiddlers, key=sortByTitle) :
    serialised_tiddlers.append(serialiseAsJsonTiddler(aTiddler))
  serialised_tiddlers_str = ",\n".join(serialised_tiddlers)
  #

  # In the v5.2.x style tiddler store, the end of the "tiddler store" (an
  # array of JSON encoded strings separated by commas and on their own
  # lines) IS NOT the start of the `</srcipt>` tag but is actually two
  # characters (a space/newline and a `]`) BEFORE the `</script> end tag.

  insertions.append((store_area_end - 2, ',\n' + serialised_tiddlers_str))

  return modify_string(html, insertions, deletions)

def extractTiddlersFromHtml(html : str) -> Tiddlers :
  tiddlers : Tiddlers = []
  return tiddlers
