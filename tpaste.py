#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
from tornado.escape import xhtml_escape as escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter

from string import letters, digits
from random import choice
from os.path import isfile, dirname, basename, exists
from os import mkdir, listdir
from subprocess import Popen, PIPE

### Options
title = ''
filename_path = 'pastes'
filename_length = 3
filename_characters = letters + digits
mldown_path = '' # if '', disable the mldown option
mldown_args = []
base_url = ""

### Highlight & format
def highlight_code(code, lang):
    res = highlight(code, get_lexer_by_name(lang), HtmlFormatter())
    # weird but it works
    return res.encode('iso-8859-1')

def list_languages():
    return sorted(map(lambda x: (x[0], x[1][0]), get_all_lexers()),
                  key=lambda x: x[1].lower())

def format_mldown(code):
    if mldown_path == '' or not isfile(mldown_path):
        return ('mldown disabled, source output<br/><pre>' + code + '</pre>')
    pipe = Popen([mldown_path] + mldown_args, stdin=PIPE, stdout=PIPE)
    content = pipe.communicate(code)[0]
    if pipe.returncode == 0:
        return content
    else:
        return ('mldown failed, source output<br/><pre>' + code + '</pre>')

### Paste form
def checkbox(name, label, checked=False, value='on'):
    res = '<label><input type="checkbox" name="' + name + '" value="' + value + '" '
    if checked:
        res += 'checked="checked"'
    res += '/>' + label + '</label>\n'
    return res

def option_boxes():
    checkboxes = ''
    if mldown_path != '':
        checkboxes += checkbox('mldown', 'Format with <a href="http://gitorious.org/mldown">mldown</a>')
    return checkboxes

def language_box():
    res = '<select name="hl">'
    res += '<option value="">No highlighting</option>'
    for (language, lang) in list_languages():
        res += '<option value="' + lang + '">' + language + '</option>\n'
    res += '</select><br/>'
    return res

def name_field():
    res = '<label for="uname">User (optional):</label><br />'
    res += '<input type="text" name="uname" id="uname" />'
    return res

def paste_form():
    res = ''
    res += '<form method="post" action="/" enctype="multipart/form-data">'
    res += '<textarea name="paste" rows="20" cols="80"></textarea><br/>'
    res += language_box()
    res += option_boxes()
    res += name_field()
    res += '<input type="submit" value="Paste" />'
    return res

### Access to disk (read & write paste)
def user_dir(user):
    return "%s/%s" % (filename_path, user)

def random_filename():
    res = ''
    for i in xrange(filename_length):
        res += choice(filename_characters)
    return res

def new_path(user):
    path = ''
    if user is not None:
        path = user_dir(user)
    else:
        path = filename_path

    def fn():
        return '%s/%s' % (path, random_filename())

    filename = fn()
    while isfile(filename):
        filename = fn()

    if user is not None:
        if not exists(path):
            mkdir(path)
    return filename

def dump_paste(content, user):
    filename = new_path(user)
    f = open(filename, 'w')
    f.write(content)
    f.close()
    return filename

def read_paste(filename):
    f = open(filename, 'r')
    return f.read()

def pastes_for_user(user):
    pastes = []
    for filename in listdir(user_dir(user)):
        if isfile(user_dir(user) + '/' + filename):
            pastes.append(filename)
    return pastes


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        html_pre = u'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
<head>
  <title>''' + title + '''</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <link rel="stylesheet" type="text/css" href="/paste.css" />
</head>
<body>
<h1>''' + title + '''</h1>'''
        html_post = ''
        paste_content = ''
        body = ''
        if self.get_argument('id', False):
            paste_content = read_paste(filename_path + '/' + 
                                       self.get_argument('id'))
            if self.get_argument('raw', False):
                self.content_type = 'text/plain'
                self.write(paste_content)
                return
            elif self.get_argument('hl', False):
                paste_content = highlight_code(paste_content,
                                               self.get_argument('hl'))
            else:
                paste_content = escape(paste_content)
                html_pre += '<pre>'
                html_post += '</pre>'
        elif self.get_argument('paste', False):
            user = self.get_argument('user', '')
            options = basename(dump_paste(self.get_argument('paste'),
                                          user))
            if user:
                options = '%s/%s' % (user, options)
            if self.get_argument('mldown', False):
                options += '&mldown'
            elif self.get_argument('hl', False):
                options += '&hl=' + self.get_argument('hl')

            if self.get_argument('script', False):
                self.content_type = 'text/plain'
                self.write(options)
            body = ('Your paste is located <a href="' + base_url +
                    options + '">here</a>')
        elif self.get_argument('user', False):
            user = self.get_argument('user', '')
            pastes = pastes_for_user(user)
            body += '<h2>Pastes for %s</h2>' % user
            body += '<ul>'
            for paste in pastes:
                body += ('<li><a href="' + base_url + usr + '/' +
                         paste + '">' + paste + '</a></li>')
            body += '</ul>'
        else:
            body = paste_form()
    
        html_post += '</body></html>'
        self.content_type = 'text/html'
        self.write(html_pre)
        self.write(body) # either body or paste_content is non-null
        self.write(paste_content)
        self.write(html_post)
    def post(self):
        self.get()
            

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/(paste\.css)", tornado.web.StaticFileHandler, 
     dict(path=dirname(__file__))),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
