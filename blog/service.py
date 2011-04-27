import blog
from blog import classes

import GeneralCounter
import recaptcha
import os
from os import environ
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import mail

class LatestEntry(webapp.RequestHandler):
    def get(self):        
        self.response.out.write(GetHtml(GetLatestPost()))

class SpecificEntry(webapp.RequestHandler):
    def extractKeyString(self):
        try:
            k = self.request.get("key")
            if (k is ''):
                k = self.request.query_string
            k = db.Key(k)
            return str(k)
        except db.BadKeyError:
            pass

        try:
            ampIndex = self.request.query_string.find('&')
            k = db.Key(self.request.query_string[0:ampIndex])
            return str(k)
        except db.BadKeyError, ValueError:
            pass
    
    def get(self):
        keyString = self.extractKeyString()
        self.response.out.write(GetHtml(GetEntry(keyString)))

class SubmitComment(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            blogComment = blog.classes.BlogComment()
            blogComment.content = self.request.get('content')
            blogComment.ParentPost = self.request.query_string
            blogComment.authorEmail = user.email()
            blogComment.authorName = user.nickname()
            blogComment.put()

            mail.send_mail(sender="Blog Comment <martindevans@gmail.com>",
                           to="martindevans@gmail.com",
                           subject="A blog comment",
                           body=user.nickname() +
                           """just wrote something on your blog at martindevans.appspot.com/blog/perma?""" + self.request.query_string)

        self.redirect("/blog/perma?" + self.request.query_string)

class BlogViews(webapp.RequestHandler):
    def get(self):
        self.response.out.write(str(GetViews(self.request.query_string)))

class FilterPage(webapp.RequestHandler):
	def get(self):
		results = []
	
		tag = classes.BlogTag.all().filter("title = ", self.request.get("tag")).get()
		if (tag is not None):
			links = classes.BlogTagLink.all().filter("Tag = ", tag)
			for l in links:
				if l.Post not in results:
					results.append(l.Post)
		results.sort(key=lambda post: post.date)
		results.reverse()

                def getTagHyperlink(tagTitle):
                    return "<a href=\"/blog/filter?tag=" + tagTitle + "\">" + tagTitle + "</a>"
	
		def makeDescriptiveString(blogPost):
			links = classes.BlogTagLink.all().filter("Post = ", blogPost)
			return "<a href=perma?" + str(blogPost.key()) + ">" + blogPost.title + "</a><br />" + blogPost.date.strftime("%d %b %Y") + "<br />Tagged : " + ", ".join([getTagHyperlink(l.Tag.title) for l in links])
	
		result = {}
		result["title"] = str(len(results)) + " Entries Tagged \"" + tag.title + "\""
		result["content"] = "<br /><br />".join([makeDescriptiveString(p) for p in results])
	
		template_values = {
			'first_post': GetFirstPost(),
			'previous_post': None,
			'entry': result,
        }
    
		path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/blog/bloglayout.html')
		html = template.render(path, template_values)
	
		self.response.out.write(html.decode("utf-8"))
		
class RecentEntries(webapp.RequestHandler):
    def get(self):
        #DEBUGGING!
        #memcache.flush_all()
        
        previouspostjs = memcache.get('blogrecentposts')
        if previouspostjs is None:
            entries_query = blog.classes.BlogPost.gql("ORDER BY date DESC")
            posts = entries_query.fetch(30)
            previouspostjs = "[" + ",".join(['["' + post.title + '","' + str(post.key()) + '"]' for post in posts]) + "];"
            memcache.set("blogrecentposts", previouspostjs, 60 * 60)
        self.response.out.write(previouspostjs)

class NextEntry(webapp.RequestHandler):
    def get(self):
		try:
			key = db.Key(self.request.query_string)
			nextEntryHtml = memcache.get('nextEntryHtml' + self.request.query_string)
			if nextEntryHtml is None:
				entry = GetEntry(self.request.query_string)
				next_entries_query = blog.classes.BlogPost.gql("WHERE date > :myDate ORDER BY date ASC LIMIT 1", myDate=entry.date)
				nextEntryHtml = next_entries_query.get()
				if (nextEntryHtml is None):
					nextEntryHtml = "Next"
				else:
					nextEntryHtml = '<a href="/blog/perma?' + str(nextEntryHtml.key()) + '">Next</a>'
				#no timeout, next post never changes, unless a new one is added in which case next is none and this runs anyway
				memcache.set('nextEntry' + self.request.query_string, nextEntryHtml)
			self.response.out.write(nextEntryHtml)
		except db.BadKeyError:
			self.response.out.write("Next")
		
class TagCloud(webapp.RequestHandler):
    def get(self):
        #DEBUGGING!
        #memcache.flush_all()
        
        cloud = memcache.get("tagcloud")
        if (cloud is None):
            cloud = GenerateTagCloud()
            memcache.set("tagcloud", cloud, 60 * 60 * 24)
        self.response.out.write(cloud)

def GenerateTagCloud():
    tags = [(t.title, GetTagCount(t)) for t in classes.BlogTag.all()]
    tags.sort(lambda x, y: int(x[1]-y[1]), reverse=True)
    return "[" + ','.join(['["' + t[0] + '",' + str(t[1]) + "]" for t in tags]) + "];"

def GetTagCount(tag):
    links = classes.BlogTagLink.all()
    links.filter("Tag = ", tag)
    return links.count()

class EntryTags(webapp.RequestHandler):
    def get(self):
		try:
			key = db.Key(self.request.query_string)
			tags = classes.BlogTagLink.all()
			tags.filter("Post = ", db.get(key))
			words = ["<a href=\"/blog/filter?tag=" + t.Tag.title + "\">" + t.Tag.title + "</a>" for t in tags]
			self.response.out.write(', '.join(words))
		except db.BadKeyError:
			pass

    def post(self):
		key = self.request.get("key")
	
		if (users.is_current_user_admin()):			
			tag = classes.BlogTag.all().filter("title = ", self.request.get("tagname")).get()
			if tag is None:
				tag = classes.BlogTag()
				tag.title = self.request.get("tagname")
				tag.put()
			
			link = classes.BlogTagLink()
			link.Tag = tag
			link.Post = db.get(db.Key(key))
			link.put()
		self.redirect("/blog/perma?" + key)

def GetViews(keystring):
    return GeneralCounter.get_count(keystring)

class AdminFooter(webapp.RequestHandler):
    def get(self):
        if (users.is_current_user_admin()):
            template_values = {
                'key' : self.request.query_string,
            }
    
            path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/blog/postadmin.html')
            self.response.out.write(template.render(path, template_values))
        else:
            self.response.out.write("")

class AjaxViewCallback(webapp.RequestHandler):
    def get(self):
        blogpost = GetEntry(self.request.query_string)

        if (blogpost is not None):        
            GeneralCounter.increment(str(blogpost.key()))

        try:
            visit = blog.classes.Visit()
            visit.Post = blogpost
            visit.put()
        except e:
            self.response.out.write("")

        self.response.out.write("//" + str(blogpost is None))

def GetHtml(blogpost):
    #DEBUGGING!
    #memcache.flush_all()
    #renders = blog.classes.BlogRender.all()
    #for r in renders:
    #    r.delete()

    keystring = str(blogpost.key()) + "fullhtmlview"

    #get it from memcache
    html = memcache.get(keystring)
    if html is None:
        #get it from datastore instead
        html = blog.classes.BlogRender.get_by_key_name(keystring)
        if (html is None):
            #render to datastore
            html = blog.classes.BlogRender(key_name=keystring)
            html.content = RenderHtml(blogpost)
            html.put()
        html = html.content
        memcache.set(keystring, html)
    return html

def RenderHtml(blogpost):
    first_post = GetFirstPost()
    if (blogpost.key() == first_post.key()):
        first_post = None
    previous_post = GetPreviousPost(blogpost)
    
    template_values = {
        'first_post': first_post,
        'previous_post': previous_post,
        'entry': blogpost,
        }
    
    path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/blog/bloglayout.html')
    html = template.render(path, template_values)

    return html.decode("utf-8")

class CommentSection(webapp.RequestHandler):
    def get(self):
		try:
			key = db.Key(self.request.query_string)
			post = db.get(key)
			
			template_values = {
				'key' : str(post.key()),
				'comments' : classes.BlogComment.all().filter("ParentPost = ", str(post.key())),
				'user' : users.get_current_user(),
				'loginhref': users.create_login_url('/blog/perma?' + str(post.key())),
				'logouthref': users.create_logout_url('/blog/perma?' + str(post.key()))
				}
			
			path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/blog/commentsection.html')
			self.response.out.write(template.render(path, template_values))
		except db.BadKeyError:
			pass

class DeleteRender(webapp.RequestHandler):
    def get(self):
        if (users.is_current_user_admin):
            key = self.request.get("key")

            keystring = key + "fullhtmlview"
            html = blog.classes.BlogRender.get_by_key_name(keystring)
            if (html is not None):
                html.delete()

            memcache.set(keystring, None)
        
            self.redirect("/blog/perma?" + key)

def GetEntry(keystring):
    post = memcache.get(keystring + "entryinstance")
    if post is None:
        post = db.get(db.Key(keystring))
        memcache.set(keystring + "entryinstance", post)
    return post

def GetPreviousPost(blogpost):
    return blog.classes.BlogPost.gql("WHERE date < :myDate ORDER BY date DESC LIMIT 1", myDate=blogpost.date).get()

def GetLatestPost():
    post = memcache.get("LatestBlogPost")
    if post is None:
        entries_query = blog.classes.BlogPost.gql("ORDER BY date DESC LIMIT 1")
        post = entries_query.get()
        memcache.set("LatestBlogPost", post, 60 * 60 * 24)
    return post

def GetFirstPost():
    post = memcache.get("FirstBlogPost")
    if post is None:
        entries_query = blog.classes.BlogPost.gql("ORDER BY date ASC LIMIT 1")
        post = entries_query.get()
        memcache.set("FirstBlogPost", post)
    return post

application = webapp.WSGIApplication(
                                     [('/blog/latest', LatestEntry),
                                      ('/blog/perma', SpecificEntry),
                                      ('/blog/signblog', SubmitComment),
                                      ('/blog/getcomments', CommentSection),
                                      #('/blog/stats', BlogStats),
                                      #('/blog/deletecomment', BlogCommentDelete),
                                      ('/blog/views', BlogViews), #fetch view count for specific blog entry
                                      ('/blog/recent', RecentEntries), #fetch a list of recent entries
                                      ('/blog/cloud', TagCloud),
                                      ('/blog/tags', EntryTags),
                                      ('/blog/next', NextEntry), #fetch a hyperlink to the next entry key from a given entry
                                      ('/blog/admin', AdminFooter),
                                      ('/blog/deleterender', DeleteRender),
                                      ('/blog/ajaxviewcallback', AjaxViewCallback),
				      ('/blog/filter.*', FilterPage),
                                      ('/blog.*', LatestEntry)
                                      ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
