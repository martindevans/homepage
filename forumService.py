import os
import forumclasses
import profileextension

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail
from datetime import datetime
from datetime import date
from datetime import timedelta

class ForumList(webapp.RequestHandler):
  def get(self):
    #list all forums
    console = []
    
    forums = memcache.get('allforums')
    if forums is None:
      console.append('ADDED forum list to memcache')
      forums_query = forumclasses.Forum.all()
      forums = forums_query.fetch(1000)
      memcache.set('allforums', forums)
    else:
      console.append('FETCHED forum list from memcache')

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js", "../javascript/Forum.js" ],
      'includenewlink': True,
      'titles': [ "Messageboard 2.0" ],
      'title': "Messageboard 2.0",
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'forums': forums,
      'console': console,
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write("<body onload=\"initialise_style(); initialise_forum();\">")

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write("<br />")
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlist.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class SpecificForum(webapp.RequestHandler):
  def get(self):
    #list all threads in forum
    console = []

    forum = memcache.get('forum' + self.request.query_string)
    if forum is None:
      forum = forumclasses.Forum.get(db.Key(self.request.query_string))
      memcache.set('forum' + self.request.query_string, forum)
      console.append('ADDED forum to memcache')
    else:
      console.append('FETCHED forum from memcache')

    threads = memcache.get('threads' + self.request.query_string)
    if threads is None:
      thread_query = forumclasses.ForumThread.gql("WHERE ParentForum = :1 ORDER BY lastUpdated DESC", forum)
      threads = thread_query.fetch(1000)      
      memcache.set('threads' + self.request.query_string, threads)
      console.append('ADDED threads to memcache')
    else:
      console.append('FETCHED threads from memcache')

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js", "../javascript/Forum.js" ],
      'titles': [ forum.title ],
      'title': forum.title,
      'options': [ '<a href="/messageboard">Forum List</a>',
                   '<a href="/messageboard/CreateThread?' + str(forum.key()) + '">New Thread</a>' ],
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'forum': forum,
      'threads': threads,
      'console': console,
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body onload="initialise_style();">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<br /><div class="forumlist">')
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    self.response.out.write(template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/threadlist.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write('</div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class SpecificThread(webapp.RequestHandler):
  def get(self):    
    #list all posts
    console = []

    thread = memcache.get('thread' + self.request.query_string)
    if thread is None:
      thread = forumclasses.ForumThread.get(db.Key(self.request.query_string))
      memcache.set('thread' + self.request.query_string, thread)
      console.append('ADDED thread to memcache')
    else:
      console.append('FETCHED thread from memcache')

    if not thread.AllowedToView():
      self.response.clear()
      self.response.set_status(401, "You are not authorised to view this")
      return

    threadhtml = memcache.get('threadhtml' + self.request.query_string)
    if threadhtml != None:
      self.response.out.write(threadhtml)
      return

    console.append('html added to memcache ' + datetime.isoformat(datetime.now()))
    
    forum = thread.ParentForum
    post_query = forumclasses.ForumPost.gql("WHERE ParentThread = :1 " +
                                            "ORDER BY date ASC", thread)

    posts = post_query.fetch(1000)

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>",
                "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/code.css\"/>" ],
      'scripts': [ "../javascript/md5.js", "../javascript/Cookies.js", "../javascript/Style.js" ],
      'titles': [ forum.title, thread.title ],
      'title': thread.title,
      'options': [ '<a href="/messageboard">Forum List</a>',
                   '<a href="/messageboard/forum?' + str(forum.key()) + '">Back to ' + forum.title + '</a>',
                   '<a href="/messageboard/CreatePost?' + str(thread.key()) + '">New Post</a>'],
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'forum': forum,
      'thread': thread,
      'posts': posts,
      'console': console,
      }

    threadhtml = ''

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    threadhtml += (template.render(path, head_template_values))

    threadhtml += ('<body onload="initialise_style();">\n')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    threadhtml += (template.render(path, head_template_values))

    threadhtml += ('<br />')
    threadhtml += ('<div class="forumlist">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    threadhtml += (template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/postlist.html')
    threadhtml += (template.render(path, body_template_values))

    threadhtml += ('<br />')
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    threadhtml += (template.render(path, head_template_values))
    threadhtml += ('</div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    threadhtml += (template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    threadhtml += (template.render(path, body_template_values))

    threadhtml += ("</body></html>")

    memcache.set('threadhtml' + self.request.query_string, threadhtml)

    self.response.out.write(threadhtml)

class CreateThread(webapp.RequestHandler):
  def get(self):
    console = []
    
    #create a new thread in this forum
    forum = memcache.get('forum' + self.request.query_string)
    if forum is None:
      forum = forumclasses.Forum.get(db.Key(self.request.query_string))
      memcache.set('forum' + self.request.query_string, forum)
      console.append('ADDED forum to memcache')
    else:
      console.append('FETCHED forum from memcache')

    authgroups = [ forum.authgroup ]
    if authgroups[0] == None:
      authgroups[0] = "none"
    auth = forumclasses.AuthorisationGroup.all()
    for a in auth:
      contained = False
      for i in authgroups:
        if i != "none":
          if i.key() == a.key():
            contained = True
            break
      if not contained:
        authgroups.append(a)

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js" ],
      'titles': [ "New thread in \"" + forum.title + "\""],
      'title': "New thread: " + forum.title,
      'options': [ '<a href="/messageboard">Forum List</a>',
                   '<a href="/messageboard/forum?' + str(forum.key()) + '">Back to ' + forum.title + '</a>' ],
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'forum': forum,
      'key': self.request.query_string,
      'console': console,
      'authgroups': authgroups
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body onload="initialise_style();">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<br />')
    self.response.out.write('<div class="forumlist">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    self.response.out.write(template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/newthread.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write('</div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class CreatePost(webapp.RequestHandler):
  def get(self):
    console = []
    
    #create a new post in this thread
    thread = memcache.get('thread' + self.request.query_string)
    if thread is None:
      thread = forumclasses.ForumThread.get(db.Key(self.request.query_string))
      memcache.set('thread' + self.request.query_string, thread)
      console.append('ADDED thread to memcache')
    else:
      console.append('FETCHED thread from memcache')

    post_query = forumclasses.ForumPost.gql("WHERE ParentThread = :1 " +
                                            "ORDER BY date DESC", thread)
    posts = post_query.fetch(1000)

    forum = thread.ParentForum

    authgroups = [ thread.authgroup ]
    if authgroups[0] == None:
      authgroups[0] = "none"
    auth = forumclasses.AuthorisationGroup.all()
    for a in auth:
      contained = False
      for i in authgroups:
        if i != "none":
          if i.key() == a.key():
            contained = True
            break
      if not contained:
        authgroups.append(a)

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/md5.js", "../javascript/Cookies.js", "../javascript/Style.js" ],
      'titles': [ "Reply in \"" + thread.title + "\"" ],
      'title': "New post: " + thread.title,
      'options': [ '<a href="/messageboard">Forum List</a>',
                   '<a href="/messageboard/forum?' + str(forum.key()) + '">Back to ' + forum.title + '</a>',
                   '<a href="/messageboard/thread?' + str(thread.key()) + '">Back to ' + thread.title + '</a>' ],
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'thread': thread,
      'key': self.request.query_string,
      'console': console,
      'posts': posts,
      'authgroups': authgroups
      }


    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body onload="initialise_style();">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write("<br />")
    self.response.out.write('<div class="forumlist">')
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    self.response.out.write(template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/newpost.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write('</div>')
    self.response.out.write('<br />')
    self.response.out.write('<div class="forumlist"><div class="forumlistoptioncontainer">Topic Overview<div class="forumlistoption"></div></div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/postlist.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write('</div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class PostNewThread(webapp.RequestHandler):
  def post(self):
    self.response.out.write(self.request.get('authdropdown'))
    thread = forumclasses.ForumThread()
    thread.ParentForum = forumclasses.Forum.get(db.Key(self.request.query_string))
    thread.title = self.request.get('title')
    thread.lastUpdated = datetime.now()
    if self.request.get('authdropdown') == 'none' or self.request.get('authdropdown') == '':
      thread.authgroup = None
    else:
      thread.authgroup = forumclasses.AuthorisationGroup.get(db.Key(self.request.get('authdropdown')))
    thread.put()
    
    post = forumclasses.ForumPost()
    post.ParentThread = thread
    post.content = self.request.get('content')
    if self.request.get('authdropdown') == 'none' or self.request.get('authdropdown') == '':
      post.authgroup = None
    else:
      post.authgroup = forumclasses.AuthorisationGroup.get(db.Key(self.request.get('authdropdown')))
    post.put()

    memcache.delete('threads' + self.request.query_string)
    self.redirect('/messageboard/thread?' + str(thread.key()))

class PostNewPost(webapp.RequestHandler):
  def post(self):
    thread = forumclasses.ForumThread.get(db.Key(self.request.query_string))
    thread.lastUpdated = datetime.now()
    thread.put()

    #delete the memcached html for the parent thread
    memcache.delete('threadhtml' + self.request.query_string)
    
    post = forumclasses.ForumPost()
    post.ParentThread = thread
    post.content = self.request.get('content')
    if self.request.get('authdropdown') == 'none' or self.request.get('authdropdown') == '':
      post.authgroup = None
    else:
      post.authgroup = forumclasses.AuthorisationGroup.get(db.Key(self.request.get('authdropdown')))
    post.put()
    self.redirect('/messageboard/thread?' + self.request.query_string + '#' + str(post.key()))

class NewContent(webapp.RequestHandler):
  def get(self):
    console = []
    
    query_string = self.request.query_string
    console.append("Request = " + query_string)
    justdate = query_string[5:len(query_string)]
    splitted = justdate.split('-')
    day = int(splitted[0])
    month = int(splitted[1])
    year = int(splitted[2])
    queryDate = date(year, month, day)
    console.append("Date = " + str(queryDate))
    thread_query = forumclasses.ForumThread.gql("WHERE lastUpdated > :d ORDER BY lastUpdated DESC", d=queryDate)
    threads = thread_query.fetch(1000)

    template_values = {
      'threads': threads,
      'console': console,
      'listtitle': "New threads since last visit"
      }

    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js", "../javascript/Forum.js" ],
      'titles': [ "New content since last visit" ],
      'title': "New content",
      'options': [ '<a href="/messageboard">Forum List</a>' ],
      'logouthtml': users.create_logout_url("/"),
      }

    body_template_values = {
      'threads': threads,
      'console': console,
      }

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body onload="initialise_style();">')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<br /><div class="forumlist">')
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumlistoptioncontainer.html')
    self.response.out.write(template.render(path, head_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/threadlist.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write('</div>')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class CreateGroup(webapp.RequestHandler):
  def post(self):
    if users.is_current_user_admin():
      g = forumclasses.AuthorisationGroup()
      g.title = self.request.get('groupname')
      g.description = self.request.get('groupdescription')
      g.put()

      m = forumclasses.AuthGroupMembership()
      m.member = users.get_current_user()
      m.group = g
      m.put()
    
    self.redirect('/messageboard')

class JoinGroupRequest(webapp.RequestHandler):
  def post(self):
    req = forumclasses.AuthGroupJoinRequest()
    req.group = forumclasses.AuthorisationGroup.get(db.Key(self.request.query_string))
    req.put()

    self.redirect(self.request.get('redirect'))

class DeletePost(webapp.RequestHandler):
  def get(self):
    post = db.get(db.Key(self.request.query_string))
    if (post.IsModeratable()):
      post.delete()
      #delete the memcached html for the parent thread
      memcache.delete('threadhtml' + str(post.ParentThread.key()))
    self.redirect('/messageboard/thread?' + str(post.ParentThread.key()))

class DisplayProfile(webapp.RequestHandler):
  def get(self):
    console = []

    userprofile = None
    if (self.request.query_string == "me"):
      userprofile = profileextension.GetOrMakeProfile(users.get_current_user())
    else:
      userprofile = profileextension.GetProfileById(self.request.query_string)

    othergroups = forumclasses.AuthorisationGroup.all().fetch(1000)
    mygroups = []
    myapplications = []

    application_query = forumclasses.AuthGroupJoinRequest.gql("WHERE member = :1", userprofile.user)
    applications = application_query.fetch(1000)
    member_query = forumclasses.AuthGroupMembership.gql("WHERE member = :1", userprofile.user)
    memberships = member_query.fetch(1000)
    for m in memberships:
      mygroups.append(m.group)
      for o in othergroups:
        if o.key() == m.group.key():
          othergroups.remove(o)
          break
    for a in applications:
      myapplications.append(a.group)
      for o in othergroups:
        if o.key() == a.group.key():
          othergroups.remove(o)
          break

    mygroup_templates_values = {
      'groups': mygroups,
      }

    notmygroup_templates_values = {
      'groups': othergroups,
      'redirecturl': self.request.url,
      }

    application_templates_values = {
      'groups': myapplications,
      }
    
    head_template_values = {
      'styles': [ "../stylesheets/main.css", "../stylesheets/forum.css" ],
      'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumDark.css\" id=\"DarkStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/ForumLight.css\" id=\"LightStyle\"/>", ],
      'scripts': [ "../javascript/md5.js", "../javascript/Cookies.js", "../javascript/Style.js", "../javascript/Forum.js" ],
      'includenewlink': False,
      'titles': [ "Messageboard 2.0" ],
      'title': "Messageboard 2.0",
      'logouthtml': users.create_logout_url("/"),
      }
    body_template_values = {
      'console': console,
      }
    profile_template_values = {
      'userprofile': userprofile,
      }
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<body onload="initialise_style();">\n')

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/forumheader.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write('<br />')
    if (self.request.query_string == "me") or (userprofile.user == users.get_current_user()):
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/profileedit.html')
    else:
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/profiledisplay.html')
    self.response.out.write(template.render(path, profile_template_values))

    self.response.out.write('<br /><div class="forumlist"><center>My Group Memberships (' + str(len(mygroups)) + ')</center>')
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/authgrouplist.html')
    self.response.out.write(template.render(path, mygroup_templates_values))
    self.response.out.write('</div>')

    self.response.out.write('<br /><div class="forumlist"><center>My Pending Applications (' + str(len(myapplications)) + ')</center>')
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/authgrouplist.html')
    self.response.out.write(template.render(path, application_templates_values))
    self.response.out.write('</div>')

    self.response.out.write('<br /><div class="forumlist"><center>Other Groups (' + str(len(othergroups)) + ')</center>')
    if (self.request.query_string == "me") or (userprofile.user == users.get_current_user()):
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/authgroupjoinlist.html')
    else:
      path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/authgrouplist.html')
    self.response.out.write(template.render(path, notmygroup_templates_values))
    self.response.out.write('</div>')
    
    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    path = os.path.join(os.path.dirname(__file__), 'djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, body_template_values))

    self.response.out.write("</body></html>")

class ChangeAlias(webapp.RequestHandler):
  def post(self):
    profile = profileextension.GetProfileById(self.request.query_string)
    if profile.user != users.get_current_user():
      self.response.clear()
      self.response.set_status(401, "You are not authorised to modify this profile")
      return
    
    profile.alias = self.request.get('alias')
    db.put(profile)
    memcache.set("profilebyid" + profile.userid, profile)

    self.redirect('/messageboard/profile?me')

class DailyDigest(webapp.RequestHandler):
  def get(self):
    message = mail.EmailMessage()
    message.sender = "nosoperor@googlemail.com"
    message.to = "nosoperor@googlemail.com"

    bcclist = []
    subscriptions = forumclasses.DigestSubscription.all()
    for s in subscriptions:
      self.response.out.write(s.member.email() + "\n")
      bcclist.append(s.member.email())
    if len(bcclist) > 0:
      message.bcc = bcclist

    message.subject = "Nos Operor Corporation Daily forum summary"

    message.body = "Threads modified in the last 24 hours:\n"
    message.html = "<p>Threads modified in the last 24 hours:</p>"
    root = self.request.url[0:len(self.request.url)-11]
    threads = forumclasses.ForumThread.all()
    threads.filter('lastUpdated >', datetime.now() - timedelta(hours=24))
    for t in threads:
      message.body += (root + 'thread?' + str(t.key()) + '\n')
      message.html += '<a href="' + (root + 'thread?' + str(t.key()) + '\n') + '">' + t.title + '</a><br />'
      self.response.out.write(root + 'thread?' + str(t.key()) + '\n')

    message.send()

application = webapp.WSGIApplication([('/messageboard', ForumList),
                                      ('/messageboard/forum', SpecificForum),
                                      ('/messageboard/thread', SpecificThread),
                                      ('/messageboard/CreateThread', CreateThread),
                                      ('/messageboard/postnewthread', PostNewThread),
                                      ('/messageboard/CreatePost', CreatePost),
                                      ('/messageboard/postnewpost', PostNewPost),
                                      ('/messageboard/newcontent', NewContent),
                                      ('/messageboard/creategroup', CreateGroup),
                                      ('/messageboard/joingroup_request', JoinGroupRequest),
                                      ('/messageboard/deletepost', DeletePost),
                                      ('/messageboard/profile', DisplayProfile),
                                      ('/messageboard/modifyprofilealias', ChangeAlias),
                                      ('/cron/messageboard/dailydigest', DailyDigest)],
                                     debug=True)

def main():
  webapp.template.register_template_library('djangoaddons.filters')
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
