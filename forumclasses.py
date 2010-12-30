import cgi
import os
import profileextension

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

class DigestSubscription(db.Model):
  member = db.UserProperty()

class AuthorisationGroup(db.Model):
  title = db.StringProperty()
  description = db.StringProperty()

class AuthGroupMembership(db.Model):
  member = db.UserProperty(auto_current_user_add=False)
  group = db.ReferenceProperty(AuthorisationGroup)

class AuthGroupJoinRequest(db.Model):
  member = db.UserProperty(auto_current_user_add=True)
  group = db.ReferenceProperty(AuthorisationGroup)

class Forum(db.Model):
  title = db.StringProperty()
  description = db.TextProperty()
  authgroup = db.ReferenceProperty(AuthorisationGroup)
  sortvalue = db.IntegerProperty()

  def GetForumThreadCount(self):
    id = str(self.key())
    count = memcache.get('forumthreadcount' + id)
    if count is None:
      thread_query = ForumThread.gql("WHERE ParentForum = :1 ", self)
      threads = thread_query.fetch(1000)
      count = len(threads)
      memcache.set('forumthreadcount' + id, count, 60)
    return count

  def AllowedToView(self):
    if self.authgroup == None:
      return True
    f_query = AuthGroupMembership.gql("WHERE member = :1 AND group = :2", users.get_current_user(), self.authgroup)
    return not f_query.count(1) == 0

class ForumThread(db.Model):
  ParentForum = db.ReferenceProperty(Forum)
  title = db.StringProperty(multiline=False)
  date = db.DateTimeProperty(auto_now_add=True)
  lastUpdated = db.DateTimeProperty(auto_now_add=False)
  authgroup = db.ReferenceProperty(AuthorisationGroup)

  def GetThreadPostCount(self):
    id = str(self.key())
    count = memcache.get('threadpostcount' + id)
    if count is None:
      post_query = ForumPost.gql("WHERE ParentThread = :1 ", self)
      posts = post_query.fetch(1000)
      count = len(posts)
      memcache.set('threadpostcount' + id, count, 60)
    return count

  def AllowedToView(self):
    if self.authgroup == None:
      return self.ParentForum.AllowedToView()
    t_query = AuthGroupMembership.gql("WHERE member = :1 AND group = :2", users.get_current_user(), self.authgroup)
    return not t_query.count(1) == 0

class ForumPost(db.Model):
  ParentThread = db.ReferenceProperty(ForumThread)
  author = db.UserProperty(auto_current_user_add=True)
  content = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  authgroup = db.ReferenceProperty(AuthorisationGroup)

  def GetAuthorPostCount(self):
    return profileextension.GetOrMakeProfile(self.author).GetPostCount()

  def GetAuthorProfileLink(self):
    return "/messageboard/profile?" + self.author.user_id()

  def AllowedToView(self):
    if self.authgroup == None:
      return self.ParentThread.AllowedToView()
    else:
      p_query = AuthGroupMembership.gql("WHERE member = :1 AND group = :2", users.get_current_user(), self.authgroup)
      return not p_query.count(1) == 0

  def GetAllowedContent(self):
    if self.AllowedToView():
      return self.content
    else:
      return "You are not authorised to view this post"

  def IsModeratable(self):
    return self.author == users.get_current_user() or users.is_current_user_admin()
