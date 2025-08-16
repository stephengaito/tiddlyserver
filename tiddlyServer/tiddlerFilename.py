
from hashlib import md5
import os
import re

underscoreRunsRegExp = re.compile(r'_+')

def titleToFilenameStub(title : str) -> str :
  """
  Convert a title into a safe filename.

  To make a filename safe, the following steps are taken:

  * The prefix "$:" is replaced with "system"
  * The title is split at all forward or backward slashes into directories.
  * Loading and trailing whitespace are removed from all path parts
  * Empty path components are removed.
  * Any path components which contain a Windows reserved filename (e.g. COM)
    are suffixed with an underscore.
  * All ASCII non alphanumeric, space, dash and underscore characters are
    replaced with ``_``.  **Specificaly ALLOW non-ascii utf-8 characters.**
  * The first seven (lower-case) characters of the MD5 hash of the original
    title encoded as UTF-8 are appended (after an underscore) to the end of
    the filename.

  No extension is added but one *must* be added to all filenames to prevent
  the possibility of clashes between directory and filenames.

  The initial steps of this renaming process ensure that the filename is safe
  on popular operating systems. The final step ensures that filenames are
  distinct even when some letters have been replaced (and that case changes
  result in a distinct filename.
  """

  # Split on any slash
  parts = re.split(r"[/\\]+", title)

  # Special case: replace $: with system
  if parts[0] == "$" + ":" :
    parts[0] = "system"

  # Replace all (runs of) nontrivial characters with _
  # WAS:  re.sub(r"[^a-zA-Z0-9_-]+", "_", part)
  newParts = []
  for aPart in parts :
    newPart = []
    for aChar in aPart :
      if ord(aChar) == 45   : newPart.append(aChar)  # allow '-'
      elif ord(aChar) == 46 : newPart.append(aChar)  # allow '.'
      elif ord(aChar) < 30  : newPart.append("_")
      elif ord(aChar) < 58  : newPart.append(aChar)  # allow 0-9
      elif ord(aChar) < 65  : newPart.append("_")
      elif ord(aChar) < 91  : newPart.append(aChar)  # allow uppercase A-Z
      elif ord(aChar) < 97  : newPart.append("_")
      elif ord(aChar) < 123 : newPart.append(aChar)  # allow lowercase a-z
      elif ord(aChar) < 128 : newPart.append("_")
      else                  : newPart.append(aChar)  # allow utf-8 characters
    newPartStr = "".join(newPart)
    newPartStr = underscoreRunsRegExp.sub('_', newPartStr)
    newParts.append(newPartStr)
  parts = newParts

  # Suffix all reserved Windows filenames with _
  parts = [
    re.sub(
      r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$",
      r"\1_", part, flags=re.IGNORECASE
    )
    for part in parts
  ]

  # Remove trailing whitespace (and remove any empty path components)
  parts = [part.strip() for part in parts if part.strip()]
  if not parts:
    parts.append("")

  # Append hash
  title_hash = md5(title.encode("utf-8")).hexdigest()[:7].lower()
  parts[-1] = f"{parts[-1]}_{title_hash}".lstrip("_")

  return os.path.join(*parts)


