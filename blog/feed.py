import blog

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from google.appengine.ext import db

class Rss(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/xml'
    feed = memcache.get("rss_feed")
    if (feed is None):
      feed = ''
      feed += '<?xml version="1.0"?>'
      feed += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">'
      feed += '<channel>'
      feed += '<atom:link href="http://martindevans.appspot.com/blog/feed/rss.xml" rel="self" type="application/rss+xml" />'
      feed += '<title>Blog 2.0</title>'
      feed += '<link>http://martindevans.appspot.com/blog/latest</link>'
      feed += '<description>A blog on programming, game development, parallelism, distributed systems and other technical stuff</description>'
      feed += '<language>en-gb</language>'
      feed += '<copyright>Copyright 2008, Martin Evans (martindevans@gmail.com)</copyright>'
      feed += '<managingEditor>martindevans@gmail.com (Martin Evans)</managingEditor>'
      feed += '<webMaster>martindevans@gmail.com (Martin Evans)</webMaster>'
      feed += '<docs>http://cyber.law.harvard.edu/rss/rss.html</docs>'
      feed += '<ttl>1440</ttl>'
      posts = blog.classes.BlogPost.all()
      posts.order('-date')
      for post in posts:
        feed += '<item>'
        feed += '<title>' + str(xmlise(post.title)) + '</title>'
        feed += '<link>http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '</link>'
        feed += '<guid>http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '</guid>'
        feed += '<pubDate>' + str(post.date.strftime("%a, %d %b %Y %H:%M:%S GMT")) + '</pubDate>'
        feed += '</item>'
      feed += '</channel></rss>'
      memcache.set("rss_feed", feed, 60 * 60 * 24)
    self.response.out.write(feed)

class Atom(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/xml'
    feed = memcache.get("atom_feed")
    if (feed is None):
      posts = blog.classes.BlogPost.all()
      posts.order('-date')
      feed = ''
      feed += '<?xml version="1.0"?>'
      feed += '<feed xmlns="http://www.w3.org/2005/Atom">'
      feed += '<id>http://martindevans.appspot.com/blog/feed/atom.xml</id>'
      feed += '<title>Blog 2.0</title>'
      feed += '<subtitle>A blog on programming, game development, parallelism, distributed systems and other technical stuff</subtitle>'
      feed += '<link href="http://martindevans.appspot.com/blog/latest" />'
      feed += '<link href="http://martindevans.appspot.com/blog/feed/atom.xml" rel="self" type="application/rss+xml" />'
      feed += '<updated>' + str(blog.classes.BlogPost.all().order("-date").get().date.strftime("%Y-%m-%dT%H:%M:%SZ")) +'</updated>'
      feed += '<author><name>Martin Evans</name><email>martindevans@gmail.com</email></author>'
      for post in posts:
        feed += '<entry>'
        feed += '<title>' + str(xmlise(post.title)) + '</title>'
        feed += '<link href="http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '" />'
        feed += '<id>http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '</id>'
        feed += '<content type="html">' + str(post.content) + '</content>'
        feed += '<updated>' + str(post.date.strftime("%Y-%m-%dT%H:%M:%SZ")) + '</updated>'
        feed += '</entry>'
      feed += '</feed>'
      memcache.set("atom_feed", feed, 60 * 60 * 24)
      
    self.response.out.write(feed)

mapping = [
  ('&', '&amp;'),
  ('<', '&lt;'),
  ('>', '&gt;'),
  ('\'', '&apos;'),
  ('"', '&quot;')
  ]

def xmlise(string):
  for k, v in mapping:
    string = string.replace(k, v)
  return string


application = webapp.WSGIApplication([('/blog/feed/rss.xml', Rss),
                                      ('/blog/feed/atom.xml', Atom)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
