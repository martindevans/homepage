import cgi
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from XmlTreeView import XmlRender

class Resume(webapp.RequestHandler):
  def get(self):
    template_values = {
        "xmlRender":XmlRender.Render(XmlRender.ReadDocument("Resume.xml")),
    }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/Resume.html')
    self.response.out.write(template.render(path, template_values).decode("utf-8"))

application = webapp.WSGIApplication([('/.*', Resume)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
