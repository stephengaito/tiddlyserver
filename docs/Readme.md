# TiddlyServer (New style)

## Documentation

- [CreateUpgrade](CreateUpgrade.md) documents a process that can be used
  to create the base `empty.html` file required by any `tiddlyserver`
  instance.

- [MultiTiddlyServer](MultiTiddlyServer.md) documents how to configure
  `tiddlyserver` to serve multiple TiddlyWiki instances using the single
  `tiddlyserver` server.

## (New style) Goals

To provide updated documentation on how to obtain/upgrade a suitable
empty.html base TiddlyWiki.

To provide a Python based *simple* TiddlyWiki server which stores the
user's tiddlers in separate TIDs.

  - The forked TiddlyServer already does this, using the older v5.1.23
    <div> format, rather than the newer v5.2.x <script> format.

To provide a *simple* multi TiddlyWiki server which allows the user to
have distinct TiddlyWiki''s which allows rudimentary "copy and paste".

  - Since the forked TiddlyServer uses Flask, we can use the underlying
    [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/)
    [Application
    Dispatcher](https://werkzeug.palletsprojects.com/en/stable/middleware/dispatcher/)
    middleware.

  - At the moment we will use a simple configuration file to list the
    known Multi-TiddlerWiki instances. This will require a restart to
    add/remove an Multi-TiddlerWiki instance.
  
(**Future?**): To provide an version with the core TiddlyWiki as an
external JavaScript package

  - Since the forked TiddlyServer uses Flask, we can use the underlying
    [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/) [Serve
    Shared Static
    Files](https://werkzeug.palletsprojects.com/en/stable/middleware/dispatcher/)
    middleware.

  - However we need to discover how to *easily* obtain the "split" "empty"
    HTML used to drive the externalized JavaScript single page application.
  
## Resources

**TiddlyWiki HTML structure**

See: [TiddlyWiki/Dev — documentation for
developers](https://tiddlywiki.com/dev/#Data%20Storage%20in%20Single%20File%20TiddlyWiki)

