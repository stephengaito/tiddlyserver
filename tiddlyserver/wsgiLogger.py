
import yaml

class WSGILogger :

  def __init__(self, app, mesg = "unknown", keys = []) :
    self.app  = app
    self.mesg = mesg
    self.keys = keys

  def __call__(self, environ, start_response) :
    try :
      print("---------------------------------")
      print(self.mesg)
      if self.keys :
        for aKey in self.keys :
          print(f"{aKey} = {environ[aKey]}")
      else :
        print("No environ keys to print....")
        print("Here is the list of environ keys:")
        print(yaml.dump(sorted(environ.keys())))
    except Exception as err :
      print(repr(err))

    return self.app(environ, start_response)

