from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import memcache

import forumclasses

class UserProfile(db.Model):
  userid = db.StringProperty()
  user = db.UserProperty()
  alias = db.StringProperty()

  def GetPostCount(self):
    id = self.user.user_id()
    count = memcache.get('authorpostcount' + id)
    if count is None:
      post_query = forumclasses.ForumPost.gql("WHERE author = :1 ", self.user)
      posts = post_query.fetch(1000)
      count = len(posts)
      memcache.set('authorpostcount' + id, count, 60)
    return count

def GetProfileById(userId):
  if userId is None:
    raise ValueError

  profile = memcache.get("profilebyid" + userId)
  if profile is None:
    query = UserProfile.gql("WHERE userid = :1 ", userId)
    profile = query.get()
    memcache.set("profilebyid" + userId, profile)
  return profile

def GetAlias(user):
  if (user is None):
    return None
  profile = GetOrMakeProfile(user)
  if profile:
    return profile.alias
  else:
    return None

def GetOrMakeProfile(user):
  profile = GetProfileById(user.user_id())

  if (profile is None):
    profile = UserProfile()
    profile.user = user
    profile.userid = user.user_id()
    profile.alias = ""
    db.put(profile)
  return profile
