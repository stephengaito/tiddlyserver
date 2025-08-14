# Pre-load caching of large tiddlywikis

## Problem

For very large TiddlyWikis with large numbers of tiddlers to load, it
would be more efficient to pre-load these tiddlers and store the assembled
tiddlyWiki in a local cache. We could then watch the TiddlyWiki's
directory for file changes and then invalidate/reload the TiddlyWiki.

## Solution

We will implement a GET REST API which takes a tiddlyWiki.config key to a
tiddlyWiki and invalidates/re-loads that tiddlyWiki's html file.

We will add a Systemd Service unit to GET from a given URL/path.

We will then add a Systemd Path unit to watch the tiddlyWiki's directory
and fire the above Systemd service unit when any changes take place.

## Justification

- I want to keep the tiddlySever code simple

- If we have an external tool monitoring a given directory, we will need a
  Systemd unit anyway. So why reimplement the systemd wheel?

## Question

**Q** Can Systemd Path units detect *new* and/or *changed* files in a
directory?

**A** ?


**Q** How do we deal with race conditions when more than one client
requests an invalidation/re-load/get on the same tiddlyWiki html file?

**A** ?

## Possible Solutions

1. We could implement a number of additional APIs to pre-load and
   invalidate a given tiddlyWiki

2. We could use a python watchdog *internal* to the TiddlyServer

3. We could use a systemd watchdog *external* to the TiddlyServer.
   (Unfortunately, this won't easily work with websites which require
   client certificates UNLESS we use the localhost:port directly).

## Resources

- [Systemd Services: Monitoring Files and Directories -
  Linux.com](https://www.linux.com/topic/desktop/systemd-services-monitoring-files-and-directories/)

- [Monitor File or Directory Changes in Linux with Systemd - Power
  Sysadmin Blog](https://poweradm.com/watch-file-directory-changes-linux/)

- [systemd.path](https://www.freedesktop.org/software/systemd/man/latest/systemd.path.html#)

- [systemd-path](https://www.freedesktop.org/software/systemd/man/latest/systemd-path.html#)

- [How To Detect File Changes Using Python -
  GeeksforGeeks](https://www.geeksforgeeks.org/python/how-to-detect-file-changes-using-python/)

- [gorakhargosh/watchdog: Python library and shell utilities to monitor
  filesystem events.](https://github.com/gorakhargosh/watchdog)

