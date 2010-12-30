import cgi
import os
import blobclasses

from google.appengine.ext import db

class FileRepositoryCollection(db.Model):
  author = db.UserProperty(auto_current_user_add=True)
  title = db.StringProperty()
  language = db.StringProperty()
  description = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  containedFiles = db.ListProperty(db.Key)
