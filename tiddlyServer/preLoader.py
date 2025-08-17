
import contextlib
from datetime import datetime

from anyio import create_task_group, Event, \
  TASK_STATUS_IGNORED, to_thread, CancelScope
from anyio.abc import TaskStatus

from starlette.applications import Starlette

from tiddlyServer.tiddlerSerDes import packTiddlyWikiBlocking
from tiddlyServer.exceptions import shutDownExceptions

import logging

logger = logging.getLogger('tiddlyWiki')

def reloadTiddlyWiki(wikiApp) :
  logger.info(f"forcing reload of {wikiApp.state.name}")
  if wikiApp.state.cancelLoading :
    wikiApp.state.cancelLoading.cancel()
  wikiApp.state.wikiNeedsLoading.set()

async def preloadTiddlyWiki(
  wikiApp : Starlette, task_status: TaskStatus[None] = TASK_STATUS_IGNORED
) :
  # using the wikiApp and its associated state...
  # wait for the wikiLoadEvent
  # clear the wikiLoadEvent
  # load the wiki
  # assert the wikiLoadedEvent
  # do it all again
  task_status.started()
  while True :
    try :
      logger.info(f"Waiting to load {wikiApp.state.name}")
      await wikiApp.state.wikiNeedsLoading.wait()
      wikiApp.state.wikiNeedsLoading = Event()  # essentially clear the event
      wikiApp.state.cancelLoading    = None
      timeStart = datetime.now()
      logger.info(f"loading {wikiApp.state.name}")
      with CancelScope() as cancelScope :
        wikiApp.state.html          = None
        wikiApp.state.cancelLoading = cancelScope
        wikiApp.state.html = await to_thread.run_sync(
          packTiddlyWikiBlocking,
          wikiApp.state.emptyHtmlFilename,
          wikiApp.state.tiddlerDir,
          str(wikiApp.state.wikiUrl)
        )
        timeTaken = datetime.now() - timeStart
        if cancelScope.cancel_called :
          logger.info(
            f"cancelled loading {wikiApp.state.name} took {timeTaken}"
          )
          wikiApp.state.wikiNeedsLoading.set()
        else :
          logger.info(f"loaded {wikiApp.state.name} took {timeTaken}")
          wikiApp.state.wikiLoaded.set()
    except shutDownExceptions :
      break

@contextlib.asynccontextmanager
async def appLifespan(app):
  async with create_task_group() as tg :
    logger.info("App LifeSpan: Run at startup!")
    for aWikiApp in app.state.wikiApps :
      # with each app, add wikiLoaded, wikiNeedsLoading events
      # assert the wikiNeedsLoading event
      # and then start the preloadTiddlyWiki for aWikiApp
      aWikiApp.state.html = None
      aWikiApp.state.wikiNeedsLoading = Event()
      aWikiApp.state.wikiLoaded       = Event()
      aWikiApp.state.wikiNeedsLoading.set()
      await tg.start(preloadTiddlyWiki, aWikiApp)
    yield
    logger.info("App LifeSpan: Run on shutdown!")
    tg.cancel_scope.cancel()
  logger.info("App LifeSpane: All shutdown")

# see: https://anyio.readthedocs.io/en/stable/tasks.html
# see: https://anyio.readthedocs.io/en/stable/api.html#anyio.abc.TaskGroup.start_soon  # noqa
# see: https://anyio.readthedocs.io/en/stable/api.html#anyio.create_task_group

