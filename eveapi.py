import cgi
import os
import httplib, urllib
from xml.dom.minidom import parseString, Node

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class Avatar(webapp.RequestHandler):
  def get(self):
    apikey = self.request.get("apikey")
    userid = self.request.get("userid")
    charactername = self.request.get("charactername")

    params = urllib.urlencode({
        'characterID': 1042486141,
        'userid': 5965679,
        'apikey': '22848FC18B484A5480A6ABBA627CD7E38B040A35A3C642B9A5000F12DA494F55',
        'names' : 'Dr Sepulveda'
    })

    headers = { "Content-type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection("api.eve-online.com")
    conn.request("POST", "/char/CharacterSheet.xml.aspx", params, headers)

    response = conn.getresponse()
    data = response.read()
    
    xml = parseString(data)

    w = self.response.out.write
    characterId = xml.getElementsByTagName("characterID")[0].toxml()
    characterId = characterId[13:]
    characterId = characterId[:characterId.find("<")]
    
    w("<html><head><title>" + charactername + "</title></head><body>")
    w('<img src="http://image.eveonline.com/Character/' + characterId + '_512.jpg" />')
    w("</body></html>")

application = webapp.WSGIApplication([('/eve/avatar.*', Avatar)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
