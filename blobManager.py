import cgi
import os
import blobclasses
import GeneralCounter

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

class MainPage(webapp.RequestHandler):
  def get(self):
    #display a list of all uploaded files
    query = blobclasses.BlobFile.all()
    query.order("date")
    files = query.fetch(1000)

    head_template_values = {
      'title': "All files",
      'styles': ["../stylesheets/main.css", "../stylesheets/redirect.css"]
    }
    body_template_values = {
      'count': len(files),
      'files': files,
    }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body><div class="redirectservice"><div class="redirecttitle"><a href="/">Homepage</a></div><div class="redirectdescription">Back to the homepage</div></div>')
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/filelist.html')
    self.response.out.write(template.render(path, body_template_values))
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class UploadPage(webapp.RequestHandler):
  def post(self):
    if users.get_current_user():
      entry = blobclasses.BlobFile()
      entry.title = self.request.get("filename")
      data = self.request.get("data")
      entry.data = db.Blob(data)
      entry.put()
    
      self.redirect('/file')
    else:
      self.redirect(create_login_url('/'))

class DownloadPage(webapp.RequestHandler):
  def get(self):
    file = blobclasses.BlobFile.get(db.Key(self.request.query_string))
    if (file):
      GeneralCounter.increment(self.request.query_string)
      if (file.data):
        self.response.headers['Content-Type'] = "application/octet-stream"
        self.response.out.write(file.data)
      else:
        self.error(404)
    else:
      self.error(404)

application = webapp.WSGIApplication(
                                     [('/file/upload', UploadPage),
                                      ('/file/perma', DownloadPage),
                                      ('/file', MainPage),
                                      ('/file.*', DownloadPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
