import cgi
import os
import blog
import GeneralCounter
import recaptcha

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from datetime import datetime
from os import environ

class BlogEntry(webapp.RequestHandler):
  def get(self):
    if (users.is_current_user_admin()):
      page = None
    else:
      page = memcache.get('fullblogpage' + self.request.query_string)
    if (self.request.query_string == ''):
      entries_query = blog.classes.BlogPost.gql("ORDER BY date DESC LIMIT 1")
      thispost = entries_query.get()
    else:
      thispost = blog.classes.BlogPost.get(db.Key(self.request.query_string))
    thispostkey = str(thispost.key())
    GeneralCounter.increment(thispostkey)
    if page is None:
      #console output    
      consolestring = []
      consolestring.append('Generated on ' + str(datetime.now()))
      
      #this post
      comments_query = blog.classes.BlogComment.gql("WHERE ParentPost = :key ORDER BY date DESC", key=thispostkey)

      #first entry
      firstEntry = memcache.get('FirstBlogEntry')
      if firstEntry is None:
        entries_query = blog.classes.BlogPost.gql("ORDER BY date ASC LIMIT 1")
        firstEntry = entries_query.get()
        memcache.set("FirstBlogEntry", firstEntry)
        consolestring.append('ADDED first entry to memcache')
      else:
        consolestring.append('FETCHED first entry from memcache')

      #previous entry
      previousEntry = memcache.get('previousEntry' + thispostkey)
      if previousEntry is None:
        previous_entries_query = blog.classes.BlogPost.gql("WHERE date < :myDate ORDER BY date DESC LIMIT 1", myDate=thispost.date)
        previousEntry = previous_entries_query.get()
        memcache.set('previousEntry' + thispostkey, previousEntry) #no time, previous never changes
        consolestring.append('ADDED previous post for this post to memcache')
      else:
        consolestring.append('FETCHED previous post for this post from memcache')
      if (previousEntry):
        previousKey = str(previousEntry.key())
        previousString = ' <a href="/blog/perma?' + previousKey + '">Previous</a> '
        firstString = ' <a href="/blog/perma?' + str(firstEntry.key()) + '">First</a> '
      else:
        previousString = ' Previous '
        firstString = ' First '

      #next entry
      if self.request.query_string == '':
        nextString = ' Next '
        latestString = ' Latest '
        consolestring.append('No Next post<br />')
      else:
        nextEntry = memcache.get('nextEntry' + thispostkey)
        if nextEntry is None:
          next_entries_query = blog.classes.BlogPost.gql("WHERE date > :myDate ORDER BY date ASC LIMIT 1", myDate=thispost.date)
          nextEntry = next_entries_query.get()
          memcache.set('nextEntry' + thispostkey, nextEntry) #no time, next post never changes, unless a new one is added in which case next is none and rhis runs anyway
          consolestring.append('ADDED next post for this post to memcache')
        else:
          consolestring.append('FETCHED next post for this post from memcache')
        if (nextEntry):
          nextKey = str(nextEntry.key())
          nextString = ' <a href="/blog/perma?' + nextKey + '">Next</a> '
          latestString = ' <a href="/blog/latest">Latest</a> '
        else:
          nextString = ' Next '
          latestString = ' Latest '

      #list of previous posts
      previousposthtml = memcache.get('blogrecentposts')
      if previousposthtml is None:
        previousposthtml = 'Latest Entries:<br /><br />'
        entries_query = blog.classes.BlogPost.gql("ORDER BY date DESC LIMIT 10")
        posts = entries_query.fetch(10)
        for post in posts:
          previousposthtml += '<div class="blogcomment"><a href="/blog/perma?' + str(post.key()) + '">' + post.title + '</a><div class="blogcommentfooter">' + str(post.date) + '</div></div>'
        memcache.set("blogrecentposts", previousposthtml) #no time, blogrecentposts is deleted when pertinent data changes
        consolestring.append('ADDED latest entries list to memcache')
      else:
        consolestring.append('FETCHED latest entries list from memcache')

      chtml = recaptcha.displayhtml(
        public_key = "6LfDtwYAAAAAAEMKJNi2r-CdeILIANZbt2z5-Z_e",
        use_ssl = False,
        error = None)

      head_template_values = {
        'title': "Blog 2.0 : " + thispost.title,
        'styles': ["../stylesheets/main.css", "../stylesheets/BlogBase.css"],
        'lines': [ '<link rel="stylesheet" type="text/css" href="../stylesheets/BlogLight.css" id="LightStyle"/>',
		'<link rel="stylesheet" type="text/css" href="../stylesheets/BlogMedium.css" id="MediumStyle"/>',
		'<link rel="stylesheet" type="text/css" href="../stylesheets/BlogDark.css" id="DarkStyle"/>',
                '<link rel="alternate" type="application/rss+xml" title="Martin\'s Blog RSS Feed" href="http://feeds.feedburner.com/MartinsBlog2" />',],
        'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js" ]
      }
      body_template_values = {
        'BlogPost': thispost,
        'blogcomments': comments_query.fetch(1000),
        'key': thispostkey,
        'first': firstString,
        'previous': previousString,
        'next': nextString,
        'latest': latestString,
        'previousposts' : previousposthtml,
        'viewcount' : GeneralCounter.get_count(thispostkey),
        'console' : consolestring,
        'isadmin' : users.is_current_user_admin(),
        'captchahtml' : chtml,
        }

      path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/pagehead.html')
      page = template.render(path, head_template_values)

      page += "<body onload=\"initialise_style()\">"

      path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/bloghead.html')
      page += template.render(path, body_template_values)

      path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/blogbody.html')
      page += template.render(path, body_template_values)

      path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/pagefooter.html')
      page += template.render(path, body_template_values)

      path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/consolefooter.html')
      page += template.render(path, body_template_values)

      page += "</body></html>"

      if (not users.is_current_user_admin()):
        memcache.set('fullblogpage' + self.request.query_string, page, 60*10) #time, allows the view counter to update
    self.response.out.write(page)

class PostPage(webapp.RequestHandler):
  def post(self):
    challenge = self.request.get('recaptcha_challenge_field')
    response = self.request.get('recaptcha_response_field')
    remoteip = environ['REMOTE_ADDR']
    cResponse = recaptcha.submit(challenge, response, "6LfDtwYAAAAAAJWWqojaQTY3WYvV6-3QqXq2Tlm_", remoteip)

    if cResponse.is_valid:
      blogComment = blog.classes.BlogComment()
      blogComment.content = self.request.get('content')
      blogComment.ParentPost = self.request.query_string
      user = users.get_current_user()
      if user:
        blogComment.authorEmail = user.email()
        blogComment.authorName = user.nickname()
      else:
        blogComment.authorEmail = self.request.get('anonymous')
        blogComment.authorName = self.request.get('author')
      blogComment.put()
      memcache.delete('fullblogpage' + self.request.query_string)
      self.redirect('/blog/perma?' + self.request.query_string + "#" + str(blogComment.key()))
    else:
      self.redirect('/blog/perma?' + self.request.query_string)

class BlogRss(webapp.RequestHandler):
  def get(self):
    rss_data = memcache.get('blogrss')
    if rss_data is None:
      #generate rss data
      posts = blog.classes.BlogPost.all()
      posts.order('-date')
      rss_data = []
      rss_data.append('<?xml version="1.0"?>\n')
      rss_data.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n')
      rss_data.append('<channel>\n')
      rss_data.append('<atom:link href="http://martindevans.appspot.com/blog/rss.xml" rel="self" type="application/rss+xml" />\n')
      rss_data.append('<title>Martins Blog 2.0</title>\n')
      rss_data.append('<link>http://martindevans.appspot.com</link>\n')
      rss_data.append('<description>Another blog on programming with XNA, C#, .NET and other stuff</description>\n')
      rss_data.append('<language>en</language>\n')
      rss_data.append('<managingEditor>martindevans@gmail.com (Martin Evans)</managingEditor>\n')
      rss_data.append('<webMaster>martindevans@gmail.com (Martin Evans)</webMaster>\n')
      rss_data.append('<ttl>60</ttl>\n')
      for post in posts:
        rss_data.append('<item>\n')
        rss_data.append('<title>' + post.title.replace("&", "&amp;") + '</title>\n')
        rss_data.append('<link>http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '</link>\n')
        rss_data.append('<guid>http://martindevans.appspot.com/blog/perma?' + str(post.key()) + '</guid>\n')
        rss_data.append('<pubDate>' + str(post.date.strftime("%a, %d %b %Y %H:%M:%S GMT")) + '</pubDate>\n')
        rss_data.append('</item>\n')
      rss_data.append('</channel>')
      rss_data.append('</rss>')
      memcache.add("blogrss", rss_data) #no time, memcache entry is removed when a new blog post is made

    self.response.headers['Content-Type'] = 'application/xml'
    for s in rss_data:
      self.response.out.write(s)

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

def clean(string):
  result = ''
  for c in string:
    if c != '?':
      if c != '&':
        if c == ' ' or c == ',':
          return result
        else:
          result += c
  return result

class BlogStats(webapp.RequestHandler):
  def get(self):
    console = []
    
    stats = memcache.get('blogstats_imghtml')
    if stats is None:
      console.append("ADDED image string to memcache")
      data = []
      labels = []
      entries = blog.classes.BlogPost.gql("ORDER BY date ASC LIMIT 30")
      for post in entries:
        data.append(GeneralCounter.get_count(str(post.key())))
        labels.append(post.title)

      stats = '<img src=\"http://chart.apis.google.com/chart?chs=1000x300&chbh=a&chd=t:'
      stats += ','.join([str(x) for x in data])
      stats += '&chds=0,' + str(max(data, key=int))
      stats += '&chl=' + '|'.join([str(clean(x)) for x in labels])
      stats += '&chm=N*f0,000000,0,-1,11'
      stats += '&cht=bvs" alt="Sample chart" />'
      
      memcache.add('blogstats_imghtml', stats, 60*10)
    else:
      console.append("FETCHED image string from memcache")

    head_template_values = {
        'title': "Blog 2.0 : Statistics",
        'styles': ["../stylesheets/main.css", "../stylesheets/BlogBase.css"],
        'lines': [ "<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/BlogLight.css\" id=\"LightStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/BlogMedium.css\" id=\"MediumStyle\"/>",
		"<link rel=\"stylesheet\" type=\"text/css\" href=\"../stylesheets/BlogDark.css\" id=\"DarkStyle\"/>", ],
        'scripts': [ "../javascript/Cookies.js", "../javascript/Style.js" ]
      }

    #first entry
    firstEntry = memcache.get('FirstBlogEntry')
    if firstEntry is None:
      entries_query = blog.classes.BlogPost.gql("ORDER BY date ASC LIMIT 1")
      firstEntry = entries_query.get()
      memcache.set("FirstBlogEntry", firstEntry)
      console.append('ADDED first entry to memcache<br />')
    else:
      console.append('FETCHED first entry from memcache<br />')
    
    bloghead_template_values = {
      'first': ' <a href="/blog/perma?' + str(firstEntry.key()) + '">First</a> ',
      'latest': ' <a href="/blog/latest">Latest</a> ',
      }
    
    foot_template_values = {
      'console' : console
      }

    path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/pagehead.html')
    self.response.out.write(template.render(path, head_template_values))

    self.response.out.write("<body onload=\"initialise_style()\">")

    path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/bloghead.html')
    self.response.out.write(template.render(path, bloghead_template_values))

    self.response.out.write("<center>")
    self.response.out.write(stats)
    self.response.out.write("</center>")

    path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/pagefooter.html')
    self.response.out.write(template.render(path, {}))

    path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/fragments/consolefooter.html')
    self.response.out.write(template.render(path, foot_template_values))

    self.response.out.write("</body></html>")

class BlogCommentDelete(webapp.RequestHandler):
  def post(self):
    if (users.is_current_user_admin()):
      comment = db.get(db.Key(self.request.get('commentkey')))
      blog.classes.BlogComment.delete(comment)
      memcache.delete('fullblogpage' + self.request.get('blogentrykey'))
      self.redirect('/blog/perma?' + self.request.get('blogentrykey'))

application = webapp.WSGIApplication(
                                     [('/blog/latest', BlogEntry),
                                      ('/blog/signblog', PostPage),
                                      ('/blog/perma', BlogEntry),
                                      ('/blog/rss.xml', BlogRss),
                                      ('/blog/stats', BlogStats),
                                      ('/blog/deletecomment', BlogCommentDelete),
                                      ('/blog.*', BlogEntry)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
