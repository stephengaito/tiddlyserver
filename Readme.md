TiddlyServer: A Personal TiddlyWiki Sync Server
===============================================

TiddlyServer is a minimal personal [TiddlyWiki](https://tiddlywiki.com/) sync
server implementing the [TiddlyWeb](https://tiddlywiki.com/#TiddlyWeb) sync
API.

***This version*** has been *copied* (not forked) from [Jonathan
Heathcote's](https://github.com/mossblaser) original
[mossblaser/tiddlyserver](https://github.com/mossblaser/tiddlyserver)

**Features:**

* Stores tiddlers as individual files on disk in plaintext
  [`.tid`](https://tiddlywiki.com/#TiddlerFiles) or as a pair of
  `.json`/`.text` files if a tiddler contains values unsupported by the
  `.tid` format.
* As a syncer, (and not a [saver](https://github.com/philips/tiddly)), with
  TiddlyServer:
  * Just changes are sent to the server: no need to upload the whole wiki
    on every save making saving instant, even on slow connections.
  * TiddlyWiki automatically pulls changes made in other windows or devices
    from the server in the background.
  * When multiple copies of the wiki are open, changing one won't silently
    delete changes made in another.
* Plugins can be installed and used normally (unlike with the 
  [reference node.js TiddlyWiki server](https://tiddlywiki.com/#GettingStarted%20-%20Node.js))
* Pre-populates TiddlyWiki with all tiddlers on first load, preventing lazy
  loading bugs and ensuring search is available immediately
* **This version*** adds the pre-loading of tiddlers into the tiddlyWiki's html file.
* ***This version*** adds the ability to serve multiple tiddlyWikis from the same server.
* Easy to use. Just run: `tiddlyserver [tiddler-directory]`

**Non-features:**

* No authentication at all: everyone who can reach the server has full
  read/write access. You should use TiddlyServer only locally or via a suitable
  authenticating proxy server (e.g. [nginx](https://nginx.org/)).
* No support for public (read-only) or multi-user access (though single-user,
  multiple-devices is fully supported).
* Does not run TiddlyWiki on the server, keeping things simple.

Installation
------------

You can install TiddlyServer using pip from PyPI like so:

    $ pip install tiddlyserver


Standalone usage
----------------

You can then start the server using:

    $ tiddlyServer [tiddler-directory]

This will serve (to localhost only) all Tiddlers in the named directory (or current
directory, if none was given) on port 8000. Go to http://localhost:8000/ in
your browser to use the wiki.

See `--help` for details on changing the port/host the server listens on.


Web server usage
----------------

To run tiddlyserver behind a webserver, TiddlyServer exposes an ASGI API via the
`tiddlyserver.create_app` application factory. This factory requres two
arguments:

* `tiddler_dir` (A `pathlib.Path`) -- The directory in which tiddlers will be
  stored.

Limitations
-----------

* Changes made in other windows (or directly to files on disk) will only be
  picked up when TiddlyWiki polls the server for changes (by default every 60
  seconds). Sadly there is no mechanism currently available to push changes up
  to TiddlyWiki.
* If you edit the same Tiddler in two windows (or on two devices) at once,
  changes from one will silently overwrite each other without any warnings.
  Both edits will, however, be recorded in separate git commits so the
  situation is recoverable.  The assumption is that if you have multiple
  windows/devices you'll be using each for a distinct purpose and so be
  unlikely to simultaneously edit a single tiddler.
* Tiddlers must have a very specific filename format based on sanitised
  versions of their title for TiddlyServer to correctly serve and edit them.
  (See [`title_to_filename_stub` in
  `tiddler_serdes.py`](./tiddlyserver/tiddler_serdes.py) for specifics.) As
  such you should avoid creating new tiddler files or changing tiddler titles
  by editing files directly to avoid any surprises.
* Binary files (e.g. images) are stored base-64 encoded (as it is in the
  underlying Tiddler data structure) rather than image files on disk.
  Unfortunately TiddlyWiki uses its own (lookup-table-based) logic to control
  base-64 encoding/decoding which would be complex and fragile if implemented
  outside of TiddlyWiki.
* Does not support the (almost unused in practice)
  [`$:/tags/RawMarkup`](https://tiddlywiki.com/#SystemTag%3A%20%24%3A%2Ftags%2FRawMarkup)
  feature (out of laziness on my part) and the various
  [`$:/tags/RawMarkupWikified`](https://tiddlywiki.com/#SystemTag%3A%20%24%3A%2Ftags%2FRawMarkup)
  tags (because these require a copy of TiddlyWiki running on the server).

Advanced usage notes
--------------------

### `empty.html` and upgrading TiddlyWiki

TiddlyServer uses the file `empty.html` in the tiddler directory as the basis
for the wiki sent when you request `/` from the server. If this file does not
exist, TiddlyServer will create it for you.

Note that as the name suggests, `empty.html` is an *empty* TiddlyWiki -- your
tiddlers are always stored in separate `*.tid` files. Actually, `empty.html`
isn't quite empty but is an empty TiddlyWiki with the following plugins
installed:

* The official 'TiddlyWeb' plugin (which communicates with TiddlyServer)
* The 'reenable-plugin-downloads' plugin which reenables the plugin downloading
  UI in the TiddlyWiki control panel which TiddlyWeb disables.

To create a suitable `empty.html` file (e.g. to upgrade to a newer version of
TiddlyWiki) perform the following

1. Download an `empty.html` file from [the TiddlyWiki website](https://tiddlywiki.com/#GettingStarted)
2. Generate a version of the `reenable-plugin-downloads` plugin for that
   version of TiddlyWiki using the following command (installed alongside
   TiddlyServer):

       $ make-tiddlywiki-reenable-plugin-downloads-plugin \
           --empty-html /path/to/empty.html \
           reenable-plugin-downloads.json

3. Open `empty.html` in your browser
4. Drag-and-drop the generated `reenable-plugin-downloads.json` plugin onto the
   wiki and import it.
5. Go to the control panel (gear icon) -> Plugins -> Get more plugins -> Open
   plugin library -> TiddlyWeb and click install.
6. When prompted to save and reload the wiki, save the new wiki as `empty.html`
   and you're ready to go!

Remember to commit your new `empty.html` file to the git repository and upgrade
any plugins you might be using as necessary.


Similar projects
----------------

TiddlyServer is far from the only solution to the problem of persisting
TiddlyWiki state -- it just happens to be one which suits my needs well, but it
might not suit yours. You might also prefer:

* Syncers:
  * [The official node.js based TiddlyWiki server](https://tiddlywiki.com/#GettingStarted%20-%20Node.js)
    * Pros: Officially supported, can generate static sites, supports a few extra
      niche features (e.g. `RawMarkupWikified`), stores binary tiddlers as native
      (e.g. jpeg/mp4/pdf) files
    * Cons: Using plugins is fiddly, a bit complicated to use, runs a full
      TiddlyWiki instance on your server, no git support, nodejs.
  * [Tiddly](https://github.com/philips/tiddly)
    * Pros: Tiny (about 250 lines of Go), a syncer (not a saver)
    * Cons: Doesn't pre-fill tiddlers into the served wiki, doesn't handle
      filename corner cases well, no git support.
  * [TiddlyWeb](https://github.com/tiddlyweb/tiddlyweb)
    * Pros: Fully featured, multi-user, multi-wiki web platform.
    * Cons: Complex to setup and manage, no git support.

* Savers:
  * [GitHub saver](https://tiddlywiki.com/#GitHub%20Saver%20Tutorial%20by%20Mohammad)
    * Pros: Built-in to TiddlyWiki, no server needed, supports public read-only
      access, changes logged in git.
    * Cons: A saver, not a syncer (slow and error prone, stores all tiddlers
      embedded in a single HTML file), authentication involves messing around with
      generating GitHub auth tokens.
  * [TW Receiver](https://github.com/sendwheel/tw-receiver)
    * Pros: Very easy to set up on any-old PHP based shared web hosting, simple
      automatic backups.
    * Cons: A saver, not a syncer (slow and error prone, stores all tiddlers
      embedded in a single HTML file), backups are just dated copies of the wiki
      and so only suitable for disaster recovery.

Development
-----------

You can install a development version of TiddlyServer directly from a checkout
of its repository using [flit](https://flit.readthedocs.io/):

    $ flit install --pth-file

