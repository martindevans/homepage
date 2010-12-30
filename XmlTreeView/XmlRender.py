from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import os
import uuid

import xml.dom.minidom

class XmlNode():
    DomNode = None
    UniqueId = None
    Depth = 0
    
    def __init__(self, domNode, depth):
        self.DomNode = domNode
        self.UniqueId = uuid.uuid4()
        self.Depth = depth

    def GetChildren(self):
        children = []
        for c in self.DomNode.childNodes:
            if (c.nodeType != c.TEXT_NODE):
                children.append(XmlNode(c, self.Depth + 1))
        return children

    def PixelOffset(self):
        return self.Depth * 30
    
    def Content(self):
        content = []
        for node in self.DomNode.childNodes:
            if node.nodeType == node.TEXT_NODE:
                content.append(node.data)
        return ''.join(content)

    def Render(self):
        template_values = {
            "self":self,
        }

        path = os.path.join(os.path.dirname(__file__), '../djangoTemplates/XmlNodeView.html')
        return template.render(path, template_values).decode("utf-8")

def ReadDocument(path):
    return xml.dom.minidom.parse(path)

def Render(XmlDocument):
    return XmlNode(XmlDocument.childNodes[0], 0).Render()

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
