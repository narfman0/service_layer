import os
from celery import Celery
from redis import Redis
from service_layer.destinations import write
from service_layer.fetch import fetch_and_cache, cached_fetch
from service_layer import settings


redis = Redis(settings.REDIS_SERVER)
app = Celery('service_layer') # without this explicit name Celery will list the app as "__main__"
app.config_from_object(settings)


@app.task
def update_all():
  for feed in settings.FEEDS:
    print("destination: {destination}\nparser: {parser}\nurl: {url}\n\n".format(**feed))
    fetch_and_schedule.delay(feed)


@app.task
def parse_from_cache(feed):
  data = cached_fetch(feed['url'], redis)
  parsed = feed['parser'](data)
  write(feed['destination'], parsed)


@app.task
def fetch_and_schedule(feed):
  fetch_and_cache(feed['url'], redis)
  parse_from_cache.delay(feed)
