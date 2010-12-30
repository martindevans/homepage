import cgi
import os
import blog
import forumclasses
import repositoryclasses

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import mail

class MainPage(webapp.RequestHandler):
  def get(self):
    #self.redirect('xmldata/restricted/adminpanel.html')
    stats = memcache.get_stats()
    template_values = {
      'hits': stats['hits'],
      'misses': stats['misses'],
      'byte_hits': stats['byte_hits'],
      'items': stats['items'],
      'bytes': stats['bytes'],
      'oldest_item_age': stats['oldest_item_age']
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/adminpanel.html')
    self.response.out.write(template.render(path, template_values))

class RenderPostPage(webapp.RequestHandler):
  def get(self):
    self.redirect('../restricted/blogpost.html')

class RenderCreatePage(webapp.RequestHandler):
  def get(self):
    template_values = {
      'authgroups': forumclasses.AuthorisationGroup.all()
      }
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/createforum.html')
    self.response.out.write(template.render(path, template_values))

class PostPage(webapp.RequestHandler):  
  def post(self):
    blogPost = blog.classes.BlogPost()
    blogPost.content = self.request.get('content')
    blogPost.title = self.request.get('title')
    blogPost.put()
    self.redirect('/admin/flushmemcache')

class MakeForumPage(webapp.RequestHandler):  
  def post(self):
    forum = forumclasses.Forum()
    forum.description = self.request.get('description')
    forum.title = self.request.get('title')
    if self.request.get('authdropdown') == 'none':
      forum.authgroup = None
    else:
      forum.authgroup = forumclasses.AuthorisationGroup.get(db.Key(self.request.get('authdropdown')))
    forum.put()
    self.redirect('/admin/flushmemcache')

class FlushMemcache(webapp.RequestHandler):
  def get(self):
    memcache.flush_all()
    self.redirect("../admin")

class NewRepositoryCollection(webapp.RequestHandler):
  def post(self):
    collection = repositoryclasses.FileRepositoryCollection()
    collection.description = self.request.get('description')
    collection.title = self.request.get('title')
    collection.language = self.request.get('language')
    collection.containedFiles = []
    collection.put()
    self.redirect('/admin')

class RenderAuthApprove(webapp.RequestHandler):
  def get(self):
    template_values = {
      'applications': forumclasses.AuthGroupJoinRequest.all()
      }
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/authgroupapproval.html')
    self.response.out.write(template.render(path, template_values))

class ApproveAuth(webapp.RequestHandler):
  def post(self):
    req = db.get((db.Key(self.request.query_string)))
    membership = forumclasses.AuthGroupMembership()
    membership.member = req.member
    membership.group = req.group
    membership.put()
    req.delete()
    mail.send_mail(sender="martindevans@gmail.com",
              to=req.member.email(),
              subject="Your application has been approved",
              body="""
Your application to join the group """ + req.group.title + """ on the messageboards at
martindevans.appspot.com has been approved.  You can now visit
http://martindevans.appspot.com/messageboard and sign in using your Google Account to
access new features.

Please let us know if you have any questions.
""")
    self.redirect('/admin/renderauthapproval')

class DisapproveAuth(webapp.RequestHandler):
  def post(self):
    req = db.get((db.Key(self.request.query_string)))
    req.delete()
    mail.send_mail(sender="martindevans@gmail.com",
              to=req.member.email(),
              subject="Your application has not been approved",
              body="""
Your application to join the group """ + str(req.group.title) + """ on the messageboards at
martindevans.appspot.com has not been approved. 

Please let us know if you have any questions.
""")
    self.redirect('/admin/renderauthapproval')

application = webapp.WSGIApplication(
                                     [('/admin/PostPage', PostPage),
                                      ('/admin/blogpost', RenderPostPage),
                                      ('/admin/createforum', RenderCreatePage),
                                      ('/admin/makeforum', MakeForumPage),
                                      ('/admin/flushmemcache', FlushMemcache),
                                      ('/admin/new_collection', NewRepositoryCollection),
                                      ('/admin/renderauthapproval', RenderAuthApprove),
                                      ('/admin/allow_auth_application', ApproveAuth),
                                      ('/admin/disallow_auth_application', DisapproveAuth),
                                      ('/admin', MainPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
