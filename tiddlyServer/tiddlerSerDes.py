"""
Routines for serialising and deserialising tiddlers on disk.
"""

from typing import NoReturn

import json
from pathlib import Path

from tiddlyServer.types import Tiddler, Tiddlers
from tiddlyServer.tiddlerFilename import titleToFilenameStub
from tiddlyServer.tiddlerSafety import isTiddlerSafe

def serialiseTid(tiddler: Tiddler, filename : Path) -> None :
  """
  Serialise a tiddler into a .tid file.
  """
  with filename.open("w", encoding="utf-8") as f:
    for field, value in sorted(tiddler.items()):
      if field != "text":
        f.write(f"{field}: {value}\n")
    f.write("\n")
    f.write(tiddler.get("text", ""))

def deserialiseTid(filename : Path, includeText : bool = True) -> Tiddler :
  """
  Deserialise a tiddler from a .tid file.
  """
  tiddler : Tiddler = {}
  with filename.open("r", encoding="utf-8") as f:
    for line in f:
      field, colon, value = line.partition(":")
      if colon:
        tiddler[field.strip()] = value.strip()
      else:
        break

    if includeText :
      tiddler["text"] = f.read()

  if 'title' not in tiddler :
    print(f"No title found in [{filename}]")
  elif not tiddler['title'] :
    print(f"Empty title in [{filename}]")

  return tiddler

def serialiseJsonPlusText(tiddler : Tiddler, filename : Path) -> None :
  """
  Serialise a tiddler into a .json and .text file. The `.json` filename must
  be given as the argument.
  """
  tiddler = tiddler.copy()
  with filename.with_suffix(".text").open("w", encoding="utf-8") as f:
    f.write(tiddler.pop("text", ""))
  with filename.open("w", encoding="utf-8") as f:
    json.dump(tiddler, f)

def deserialiseJsonPlusText(filename : Path, includeText : bool = True) :
  """
  Deserialise a tiddler from a .json and .text file. The `.json` filename must
  be given as the argument.
  """
  tiddler : Tiddler = {}
  if includeText :
    with filename.with_suffix(".text").open("r", encoding="utf-8") as f:
      tiddler["text"] = f.read()
  with filename.open("r", encoding="utf-8") as f:
    tiddler.update(json.load(f))
  return tiddler

def deleteTiddler(directory : Path, title : str) -> list[Path] :
  """
  Delete the tiddler file(s) associated with the named tiddler, if it exists.

  Returns the full filenames of any deleted files.
  """
  out : list[Path] = []

  filenameStub = directory / titleToFilenameStub(title)
  for suffix in [".tid", ".json", ".text"]:
    filename = filenameStub.with_suffix(suffix)
    if filename.is_file():
      out.append(filename)
      filename.unlink()

  return out

def writeTiddler(directory : Path, tiddler : Tiddler) -> list[Path] :
  """
  Store the given tiddler, replacing any previously existing tiddler file.

  Returns the full filenames of any deleted or created files.
  """
  # Delete any previous tiddler (we delete rather than overwriting because
  # changing the tiddler may change whether it is stored in a single tid file
  # or in json+text files.
  title = tiddler.get("title", "")
  out = deleteTiddler(directory, title)

  filenameStub = directory  / titleToFilenameStub(title)

  filenameStub.parent.mkdir(parents=True, exist_ok=True)

  if isTiddlerSafe(tiddler):
    filename = filenameStub.with_suffix(".tid")
    serialiseTid(tiddler, filename)
    if filename not in out:
      out.append(filename)
  else:
    jsonFilename = filenameStub.with_suffix(".json")
    textFilename = filenameStub.with_suffix(".text")

    serialiseJsonPlusText(tiddler, jsonFilename)

    if jsonFilename not in out:
      out.append(jsonFilename)

    if textFilename not in out:
      out.append(textFilename)

  return out

def readTiddler(directory : Path, title : str) -> Tiddler | NoReturn :
  """
  Read the tiddler with the title given.

  Raises a :py:exc:`FileNotFoundError` if the tiddler does not exist.
  """
  filenameStub = directory / titleToFilenameStub(title)

  tidFilename = filenameStub.with_suffix(".tid")
  if tidFilename.is_file():
    return deserialiseTid(tidFilename)

  jsonFilename = filenameStub.with_suffix(".json")
  if jsonFilename.is_file():
    return deserialiseJsonPlusText(jsonFilename)

  raise FileNotFoundError(
    f"No .tid or .json file could be found for tiddler '{title}'"
  )

def readAllTiddlers(
  directory : Path, extraTiddlers : Tiddlers = [], includeText : bool = True
) -> Tiddlers :
  """
  Read all of the tiddlers in the named directory.
  """
  for aTid in extraTiddlers :
    yield aTid
  for tidFilename in directory.glob("**/*.tid"):
    yield deserialiseTid(tidFilename, includeText)
  for jsonFilename in directory.glob("**/*.json"):
    yield deserialiseJsonPlusText(jsonFilename, includeText)

