import profileextension

#http://www.djangosnippets.org/snippets/853/
from postmarkup import render_bbcode

from google.appengine.ext import webapp
register = webapp.template.create_template_register()


def bbcode(value):
    """
    Generates (X)HTML from string with BBCode "markup".
    By using the postmark lib from:
    @see: http://code.google.com/p/postmarkup/
    """ 
    return render_bbcode(value)
register.filter(bbcode)

def useralias(value):
    return profileextension.GetAlias(value)
register.filter(useralias)
