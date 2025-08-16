
from tiddlyServer.types import Tiddler

"""
WHAT IS A TIDDLER?

see Jeremy Ruson's answer in:
  https://groups.google.com/g/tiddlywiki/c/fUq8JWSnU_M

----
Jeremy Ruston
unread,
Jun 16, 2021, 3:32:37 PM
to tiddl...@googlegroups.com

Just to add that the .tid file format really is as simple as it looks,
with the constraints implied by that simplicity:

* Field names cannot contain colons
* Field values (apart from the "text" field) cannot contain newlines

The core works around these limitations by saving tiddlers in JSON format
if they don't meet the criteria for .tid files.

Best wishes

Jeremy

--
Jeremy Ruston
jer...@jermolene.com
https://jermolene.com
----

WE ARE BEING TOO STRICT; Further more, since we are explicitly assuming a
TiddlyWiki V5.2 or greater, all tiddlers are stored in JSON in the browser.
This means that all we care about is that WE can store and reload tiddlers.

"""

def isTiddlerSafe(tiddler: Tiddler) -> bool:
  """
  Check whether a tiddler has any fields which cannot be represented within a
  *.tid format file.
  """
  for field, value in tiddler.items():
    if field != "text":
      for string in [field, value]:
        # Cannot cope with trailing whitespace
        if string.strip() != string:
          # print(f"FOUND leading/trainlin whitespace in [{string}]")
          return False

      # Check for unsupported characters (e.g. newlines)
      if ':' in field :
        # print(f"FOUND [:] in [{field}]")
        return False

      # Check for newlines in the values of (non-text) fields
      if 1 < len(value.splitlines()) :
        # print(f"FOUND newline in [{field}] [{value}] [{value.splitlines()}]")
        return False

  return True

