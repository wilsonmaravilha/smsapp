import jinja2
import os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail



class Message(db.Model):
    """Models an individual Guestbook entry with author, content, and date."""
    author = db.StringProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)
    recipient = db.StringProperty(multiline=True)
    coordinates = db.StringProperty(multiline=True)


def emailmessage_key(emailmessage_name=None):
    """Constructs a Datastore key for a Guestbook entity with emailmessage_name."""
    return db.Key.from_path('EmailMessage', emailmessage_name or 'default_emailmessage')


class MainPage(webapp2.RequestHandler):

    def get(self):
        emailmessage_name=self.request.get('emailmessage_name')
        messages_query = Message.all().ancestor(
            emailmessage_key(emailmessage_name)).order('-date')
        messages = messages_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            self.redirect(users.create_login_url(self.request.uri))
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'messages': messages,
            'url': url,
            'url_linktext': url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class EmailMessage(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'EmailMessage' to ensure each EmailMessage
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        emailmessage_name = self.request.get('emailmessage_name')
        message = Message(parent=emailmessage_key(emailmessage_name))

        if users.get_current_user():
            message.author = users.get_current_user().nickname()
        else:
            self.redirect(users.create_login_url(self.request.uri))
        message.recipient = str(self.request.get('recipient')) + "@BULKSMS.NET"
        message.content = self.request.get('content')
        message.coordinates = self.request.get('currentlatlng')
        message.put()
        query_params = {'emailmessage_name': emailmessage_name}
        self.redirect('/?' + urllib.urlencode(query_params))
        messager = mail.EmailMessage(sender="Wilson Canda <wilsonmaravilha@gmail.com>",
                            subject="message")

        messager.to = message.recipient
        messager.body = message.content

        messager.send()

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/mail', EmailMessage)],
                              debug=True)
