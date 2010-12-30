import cgi
import os
import GeneralCounter

from google.appengine.ext import db

class BlobFile(db.Model):
  author = db.UserProperty(auto_current_user_add=True)
  modifier = db.UserProperty(auto_current_user=True)
  title = db.StringProperty()
  data = db.BlobProperty()
  date = db.DateTimeProperty(auto_now_add=True)

  def compare_files(x, y):
    if x.date>y.date:
      return -1
    elif x.date==y.date:
      return 0
    else: # x<y
      return 1

  def GetDownloadCount(self):
    return int(GeneralCounter.get_count(str(self.key())))
