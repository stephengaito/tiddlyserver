

class ExitNow(Exception) :
  pass

shutDownExceptions = (ExitNow, KeyboardInterrupt, SystemExit)

