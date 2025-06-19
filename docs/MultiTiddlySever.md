# Mult-TiddlyWiki based TiddlyServer

The configuration YAML file will look like:

```
host: <the host IP address on which to listen>
port: <the IP port on which to listen>
template: <a Path to a Jinja2 template for the base app>
static:
  url: <the url for static objects - defaults to `/static`>
  dir: <the path, relative to the base path, containing all static objects>
wikis:
  - url: /aMultiTiddlerWikiUrlPath
    dir: /aFileSystemPath
    useGit: <true or false to use git to version control this wiki>
    title: <a Title for the wiki>
    desc: <a text/markdown description which will be displayed with the list of wikis>
  - url: /anotherMultiTiddlerWikiUrlPath
    dir: /anotherFileSystemPath
    useGit: <true or false to use git to version control this wiki>
    title: <a Title for the wiki>
    desc: <a text/markdown description which will be displayed with the list of wikis>
```

This configuration file (named `wikiConfig.yaml`) will be placed in the
base directory as provided by the first command line argument to the
`tiddlyserver`.

All file system paths will be relative to the base directory.

The `static`/`url` and `static`/`dir` keys MUST be supplied.

The `wikis` key MUST have at least one element. All of the listed `wikis`
elements MUST have the `url` and `dir` keys. The `useGit` key is optional
and defaults to `True`. The optional `desc` key can contain a markdown
based description of the given wiki. This description will be displayed
whenever the user gets the list of wikis.

Any unknown urls will be mapped to a list of the known TiddlyWikis.

The `host` and `port` keys are optional, but, if supplied, will be used to
start the Waitress server.

If the base directory contains an `empty.html` file, this file will be
used to initialize any new Mult-TidllyWiki instances using a Linux
symbolic link. Alternatively you can place your own (per multi-wiki)
`empty.html` in the base directory of any given multi-wiki.

## Resources

- [Flask](https://flask.palletsprojects.com/en/stable/)

- [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/)

- [Application
  Dispatcher](https://werkzeug.palletsprojects.com/en/stable/middleware/dispatcher/)
  middleware.

- [Serve Shared Static
  Files](https://werkzeug.palletsprojects.com/en/stable/middleware/shared_data/)
  middleware.

- [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/index.html)

