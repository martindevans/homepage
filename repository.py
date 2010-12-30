import cgi
import os
import blobclasses
import repositoryclasses
import GeneralCounter

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users

class MainPage(webapp.RequestHandler):
  def get(self):
    query = repositoryclasses.FileRepositoryCollection.all()
    query.order("title")
    collections = query.fetch(1000)

    head_template_values = {
        'title': "Project List",
        'styles': ["../stylesheets/main.css", "../stylesheets/redirect.css"]
      }
    homebox_templates_values = {
        'title': '<a href="/">Homepage</a>',
        'descriptions': [ "Return to the homepage" ]
      }
    body_template_values = {
      'collections': collections,
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/redirectservicebox.html')
    self.response.out.write(template.render(path, homebox_templates_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/projectlist.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class ListProjectFiles(webapp.RequestHandler):  
  def get(self):
    if self.request.query_string == '':
      self.redirect('/repository')
    else:
      project = repositoryclasses.FileRepositoryCollection.get(db.Key(self.request.query_string))

      files = []
      for key in project.containedFiles:
        f = db.get(key)
        files.append(f)
      files.sort(blobclasses.BlobFile.compare_files)

      head_template_values = {
        'title': "Project files in \"" + project.title + "\"",
        'styles': ["../stylesheets/main.css", "../stylesheets/redirect.css"]
      }
      homebox_templates_values = {
        'title': '<a href="/">Homepage</a>',
        'descriptions': [ "Return to the homepage" ]
      }
      infobox_templates_values = {
        'title': project.title,
        'descriptions': [ "author: " + project.author.nickname(), "language: " + project.language, project.description]
      }
      body_template_values = {
        'count': len(files),
        'files': files,
      }
      attach_templates_values = {
        'projectkey': self.request.query_string
      }

      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
      self.response.out.write(template.render(path, head_template_values))

      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/redirectservicebox.html')
      self.response.out.write(template.render(path, homebox_templates_values))

      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/redirectservicebox.html')
      self.response.out.write(template.render(path, infobox_templates_values))
      
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/filelist.html')
      self.response.out.write(template.render(path, body_template_values))

      if users.is_current_user_admin():
        path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/attachfileform.html')
        self.response.out.write(template.render(path, attach_templates_values))
      
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
      self.response.out.write(template.render(path, body_template_values))

      self.response.out.write("</body></html>")

class AttachFile(webapp.RequestHandler):
  def post(self):
    entry = blobclasses.BlobFile()
    entry.title = self.request.get("filename")
    data = self.request.get("data")
    entry.data = db.Blob(data)
    key = entry.put()

    project = repositoryclasses.FileRepositoryCollection.get(db.Key(self.request.query_string))
    project.containedFiles.append(key)
    project.put()

    #self.response.out.write(str(key))
    self.redirect('/repository/listallfiles?' + self.request.query_string)

application = webapp.WSGIApplication(
                                     [('/repository', MainPage),
                                      ('/repository/listallfiles', ListProjectFiles),
                                      ('/repository/attach', AttachFile)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
