#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
from tornado.escape import xhtml_escape as escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, get_all_lexers
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from string import ascii_letters, digits
from random import choice
from os.path import isfile, dirname, basename, exists
from os import mkdir, listdir
from subprocess import Popen, PIPE
from pickle import dump, load
from re import match

### Options
title = 'Paste it §'
doc = '(<a href="http://awesom.eu/~acieroid/articles/paste.html">doc</a>)'
filename_path = 'pastes'
filename_length = 3
filename_characters = ascii_letters + digits
mldown_path = '' # if '', disable the mldown option
mldown_args = []
linenos_type = 'table' # 'table', 'inline' or '' (table is  copy-paste friendly)
production = False
base_url = '/'
if not production:
    base_url += '?id='

def valid_username(username):
    return not ('/' in username)

### Highlight & format
def highlight_code(code, lang, linenos=''):
    res = highlight(code, get_lexer_by_name(lang),
                    HtmlFormatter(linenos=linenos))
    # weird but it works
    return res.encode('iso-8859-1')

def list_languages():
    return sorted(map(lambda x: (x[0], x[1][0]), get_all_lexers()),
                  key=lambda x: x[1].lower())

def lang_from_ext(ext):
    try:
        return get_lexer_for_filename('.' + ext).aliases[0]
    except (ClassNotFound, IndexError):
        return ''

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
    checkboxes += checkbox('ln', 'Line numbers')
    checkboxes += checkbox('raw', 'Raw paste')
    checkboxes += '<br/>'
    return checkboxes

def language_box():
    res = '<select name="hl">'
    res += '<option value="">No highlighting</option>'
    for (language, lang) in list_languages():
        res += '<option value="' + lang + '">' + language + '</option>\n'
    res += '</select><br/>'
    return res

def name_field():
    res = '<label for="user">User (optional):</label><br/>'
    res += '<input type="text" name="user" id="user"/><br/>'
    return res

def comment_field():
    res = '<label for="comment">Comment (optional):</label><br/>'
    res += '<input type="text" name="comment" id="comment"/>'
    return res

def paste_form():
    res = ''
    res += '<form method="post" action="/" enctype="multipart/form-data">'
    res += '<textarea name="paste" rows="20" cols="80"></textarea><br/>'
    res += language_box()
    res += option_boxes()
    res += name_field()
    res += comment_field()
    res += '<input type="submit" value="Paste"/>'
    res += '</form>'
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
    with open(filename, 'w') as f:
        f.write(content)
    return filename

## Users
def read_paste(filename):
    try:
        with open(filename, 'r') as f:
            return f.read()
    except IOError:
      raise tornado.web.HTTPError(404)

def pastes_for_user(user):
    pastes = []
    try:
      for filename in listdir(user_dir(user)):
          if (not match(r'.*\.meta', filename) and
              isfile(user_dir(user) + '/' + filename)):
              pastes.append(filename)
    except OSError:
      pass
    return pastes

## Meta informations
def meta_dir(user, paste):
    if user:
        return ("%s/%s.meta" % (user_dir(user), paste))
    else:
        return ("%s/%s.meta" % (filename_path, paste))

def dump_meta(user, paste, meta):
    filename = meta_dir(user, paste)
    with open(filename, 'w') as f:
        dump(meta, f)

def read_meta(user, paste):
    filename = meta_dir(user, paste)
    if not isfile(filename):
        return {}
    with open(filename, 'r') as f:
        return load(f)

### App
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        html_pre = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
<head>
  <title>''' + title + '''</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" type="text/css" href="/paste.css" title="Clear"/>
  <link rel="stylesheet" type="text/css" href="/paste-margin.css" title="Clear with margin"/>
  <link rel="alternate stylesheet" type="text/css" href="/dark.css" title="Dark"/>
  <link rel="alternate stylesheet" type="text/css" href="/dark2.css" title="Alternative dark"/>
</head>
<body>'''
        html_post = ''
        paste_content = ''
        body = ''
        if self.get_argument('id', False):
            paste = self.get_argument('id').encode('utf-8')
            paste_content = read_paste(filename_path + '/' + paste)
            meta = read_meta(None, paste)
            if '&raw' in self.request.uri:
                self.set_header("Content-Type", "text/plain; charset=utf-8")
                self.write(paste_content)
                return
            elif '&mldown' in self.request.uri:
                self.write(format_mldown(paste_content))
                return
            elif self.get_argument('hl', False) or 'hl' in meta:
                try:
                    hl = self.get_argument('hl', False) or meta['hl']
                    if '&ln' in self.request.uri:
                        paste_content = highlight_code(paste_content, hl,
                                                       linenos_type)
                    else:
                        paste_content = highlight_code(paste_content, hl)
                except ClassNotFound:
                    paste_content = escape(paste_content)
                    html_pre += '<pre>'
                    html_post += '</pre>'
            else:
                if '&ln' in self.request.uri:
                    # TODO: line numbers not aligned with 'table', so
                    # we must use 'inline' (but there's no problem if
                    # the code is highlighted)
                    paste_content = highlight_code(paste_content,
                                                   'text', 'inline')
                else:
                    paste_content = escape(paste_content)
                html_pre += '<pre>'
                html_post += '</pre>'
        elif self.get_argument('paste', False):
            user = escape(self.get_argument('user', '').encode('utf-8'))
            if not valid_username(user):
                raise tornado.web.HTTPError(404)

            paste = basename(dump_paste(self.get_argument('paste').encode('utf-8'),
                                        user))
            options = paste
            meta = {'hl': '',
                    'comment': escape(self.get_argument('comment', '').encode('utf-8'))}
            if user:
                options = '%s/%s' % (user, options)
            if 'raw' in self.request.arguments:
                options += '&raw'
            if 'ln' in self.request.arguments:
                options += '&ln'
            if 'mldown' in self.request.arguments:
                options += '&mldown'
            elif self.get_argument('hl', False):
                hl = self.get_argument('hl').encode('utf-8')
                # options += '&hl=' + hl # Not needed anymore because of meta
                meta['hl'] = hl
            elif self.get_argument('ext', False):
                hl = lang_from_ext(self.get_argument('ext').encode('utf-8'))
                if hl != '':
                    # options += '&hl=' + hl
                    meta['hl'] = hl

            dump_meta(user, paste, meta)
            if '&script' in self.request.body:
                self.set_header("Content-Type", "text/plain; charset=utf-8")
                self.write(options)
                return
            self.redirect(base_url + options);
            return
        elif self.get_argument('user', False):
            user = escape(self.get_argument('user', '').encode('utf-8'))
            if not valid_username(user):
                raise tornado.web.HTTPError(404)
            pastes = pastes_for_user(user)
            body += '<h2>Pastes for %s</h2>' % user
            if pastes == []:
              body += '<p>No paste for this user</p>'
            else:
              body += '<ul>'
              for paste in pastes:
                  meta = read_meta(user, paste)
                  body += ('<li><a href="%s%s/%s">%s</a>' %
                           (base_url, user, paste, paste))
                  if 'comment' in meta and meta['comment'] != '':
                      body += ': %s' % meta['comment']
                  body += '</li>'
              body += '</ul>'
        else:
            html_pre += ('<h1>%s <span style="font-size: 12px">%s</span></h1>' %
                         (title, doc))
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
    (r"/([a-z0-9\-]+\.css)", tornado.web.StaticFileHandler,
     dict(path=dirname(__file__))),
])

if __name__ == "__main__":
    application.listen(8888)
    application.debug = not production
    tornado.ioloop.IOLoop.instance().start()
