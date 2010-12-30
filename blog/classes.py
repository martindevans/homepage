import cgi
import os

from google.appengine.ext import db

class BlogPost(db.Model):
    title = db.StringProperty(multiline=False)
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class BlogComment(db.Model):
    ParentPost = db.StringProperty()
    authorEmail = db.StringProperty()
    authorName = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class BlogRender(db.Model):
    content = db.TextProperty()

class BlogTag(db.Model):
    title = db.StringProperty(multiline=False)

class BlogTagLink(db.Model):
    Post = db.ReferenceProperty(BlogPost)
    Tag = db.ReferenceProperty(BlogTag)
	
class BlogRollEntry(db.Model):
    Link = db.StringProperty(multiline=False)
    Title = db.StringProperty(multiline=False)

class Visit(db.Model):
    User = db.UserProperty(auto_current_user_add=True)
    Date = db.DateTimeProperty(auto_now_add=True)
    Post = db.ReferenceProperty(BlogPost)
    
