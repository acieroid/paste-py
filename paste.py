#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_unix_socket
from tornado.escape import xhtml_escape as escape
from tornado.options import options, define, parse_command_line

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, get_all_lexers
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from os import mkdir, listdir
from os.path import isfile, dirname, basename, exists
from pickle import dump, load
from random import choice
from re import match
from string import ascii_letters, digits
from subprocess import Popen, PIPE
from sys import argv
from urllib import quote

### Options
title = 'Paste it §'
doc = '(<a href="https://github.com/acieroid/paste-py/">doc</a>|<a href="https://raw.github.com/acieroid/paste-py/master/paste.sh">script</a>)'
filename_path = 'pastes'
filename_length = 4
filename_characters = ascii_letters + digits
mldown_path = '' # if '', disable the mldown option
mldown_args = []
linenos_type = 'table' # 'table', 'inline' or '' (table is copy-paste friendly)
base_url = '/'
production = False

spam = ["buy ", "phentermine", "pill", "cialis", "carisoprodol", "soma ",
        " soma", "carisoprodol", " mg", "30mg", "adipex", "business",
        "loan", "credit", "cash ", " cash", "viagra", "phentramine",
        "advance", "pay day", "payday", "weltmine" "metermine", "tramadol",
        "ultram", "duromine", "side effects", "prescription", "vanadom",
        "stomach", "tablets", "tadalafil", "drug", "tamoxifen", "synthroid",
        "vardenafil", "tadalafil", "vitamin", "accutane", "adderral",
        "strattera", "acyclovir", "xanax", "loan"]

def valid_username(username):
    legal = not (('/' in username) or (' ' in username))
    if not legal:
        return False
    for kw in spam:
        if username.lower().find(kw) != -1:
            return False
    return True

### Highlight & format
def highlight_code(code, lang, linenos=''):
    if lang == '':
        lang = 'text'
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
    res += '<input type="text" name="content" style="display: none;">'
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
        return ('%s/%s.meta' % (user_dir(user), paste))
    else:
        return ('%s/%s.meta' % (filename_path, paste))

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

## Logic
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

html_post = '</body></html>'

html_invalid_user = html_pre + '''
<h1>Invalid Username</h1>
<p>The username you supplied is invalid or considered as spam.<br/>
Please try another username or file a <a href="https://github.com/acieroid/paste-py/issues">bug report</a> if you think your username is not spammy and should be allowed.</p>

<p>Go <a href="''' + base_url + '''">back</a>.</p>
''' + html_post

html_spam = html_pre + '''
<h1>Spam Detected</h1>
<p>You probably are spam, so we'll just ignore you<br/>
If you think that's an error, file a <a href="https://github.com/acieroid/paste-py/issues">bug report</a>.</p>

<p>Go <a href="''' + base_url + '''">back</a>.</p>
''' + html_post

def extract_args(uri):
    content = map(lambda s: s.split('='), uri.split('&')[1:])
    content = map(lambda v: len(v) != 2 and [v[0], ''] or v, content)
    return dict(content)

def view_paste(paste, args, handler):
    pre = html_pre
    post = ''
    paste_content = read_paste(filename_path + '/' + paste.decode('utf-8'))
    meta = read_meta(None, paste)
    if 'raw' in args:
        handler.set_header('Content-Type', 'text/plain; charset=utf-8')
        handler.write(paste_content)
        return
    elif 'mldown' in args:
        handler.write(format_mldown(paste_content))
        return
    elif 'hl' in args or 'hl' in meta:
        try:
            hl = ('hl' in args and args['hl']) or meta['hl']
            if 'ln' in args:
                paste_content = highlight_code(paste_content, hl,
                                               linenos_type)
            else:
                paste_content = highlight_code(paste_content, hl)
        except ClassNotFound as e:
            paste_content = escape(paste_content)
            pre += '<pre>'
            post += '</pre>'
    else:
        if 'ln' in args:
            paste_content = highlight_code(paste_content,
                                           'text', linenos_type)
        else:
            paste_content = escape(paste_content)
            pre += '<pre>'
            post += '</pre>'
    post += html_post
    handler.content_type = 'text/html'
    handler.write(pre)
    handler.write(paste_content)
    handler.write(post)

def add_paste(user, content, comment, args, handler):
    if not valid_username(user):
        handler.write(html_invalid_user)
        return

    paste = basename(dump_paste(content, user))
    options = paste
    meta = {'hl': '', 'comment': escape(comment)}
    if user:
        options = '%s/%s' % (user, options)
    if 'raw' in args:
        options = 'raw/' + options
    else:
        if 'ln' in args:
            options += '&ln'
        if 'mldown' in args:
            options += '&mldown'
        elif 'hl' in args:
            hl = args['hl']
            meta['hl'] = hl
        elif 'ext' in args:
            hl = lang_from_ext(args['ext'])
            if hl != '':
                # options += '&hl=' + hl
                meta['hl'] = hl

    dump_meta(user, paste, meta)
    if 'script' in args:
        handler.set_header('Content-Type', 'text/plain; charset=utf-8')
        handler.write(quote(options))
        return
    handler.redirect(base_url + options);

def view_index(handler):
    body = paste_form()
    handler.content_type = 'text/html'
    handler.write(html_pre)
    handler.write('<h1>%s <span style="font-size: 12px">%s</span></h1>' %
                  (title, doc))
    handler.write(body)
    handler.write(html_post)

def view_user(user, handler):
    user = escape(user)
    if not valid_username(user):
        raise tornado.web.HTTPError(404)
    pastes = pastes_for_user(user)
    body = '<h2>Pastes for %s</h2>' % user
    if pastes == []:
        body += '<p>No paste for this user</p>'
    else:
        body += '<ul>'
    for paste in pastes:
        meta = read_meta(user, paste)
        body += ('<li><a href="%s%s/%s">%s</a>' %
                 (base_url, user, paste, paste))
        if 'comment' in meta and meta['comment'] != '':
            body += ': %s' % meta['comment'].decode('utf-8')
        body += '</li>'
    body += '</ul>'
    handler.content_type = 'text/html'
    handler.write(html_pre)
    handler.write(body)
    handler.write(html_post)

### App
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        args = extract_args(self.request.uri)
        if self.get_argument('id', False):
            view_paste(self.get_argument('id').encode('utf-8'), args, self)
        elif self.get_argument('paste', False):
            args = {k: v[0].decode('utf-8') # python and utf-8, wtf.
                    for k, v in self.request.arguments.items()}
            # the field 'content' should be empty, unless filled by bots
            if self.get_argument('content', '') != '':
                self.set_status(404)
                self.write(html_spam)
                return
            add_paste(self.get_argument('user', '').encode('utf-8'),
                      self.get_argument('paste').encode('utf-8'),
                      self.get_argument('comment', '').encode('utf-8'),
                      args, self)
        elif self.get_argument('user', False):
            view_user(self.get_argument('user', '').encode('utf-8'), self)
        else:
            view_index(self)
    def post(self):
        self.get()

class ViewHandler(tornado.web.RequestHandler):
    def get(self, name, args, last):
        view_paste(name.encode('utf-8'), extract_args(args), self)

class UserViewHandler(tornado.web.RequestHandler):
    def get(self, user, name, args, last):
        paste = user.encode('utf-8') + '/' + name.encode('utf-8')
        view_paste(paste, extract_args(args), self)

class UserHandler(tornado.web.RequestHandler):
    def get(self, user):
        view_user(user, self)

class RawHandler(tornado.web.RequestHandler):
    def get(self, name):
        view_paste(name.encode('utf-8'), {'raw': ''}, self)

class UserRawHandler(tornado.web.RequestHandler):
    def get(self, user, name):
        view_paste(name.encode('utf-8'), {'raw': '',
                                          'user': user.encode('utf-8')}, self)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/user/([^/]+)/?", UserHandler),
    (r"/raw/([^&]+)", RawHandler),
    (r"/raw/([^/]+)/([^&]+)", UserRawHandler),
    (r"/([a-zA-Z0-9\-]+\.css)", tornado.web.StaticFileHandler,
     dict(path=dirname(__file__))),
    # Those two routes should stay in last position to avoid conflicts
    # with the other routes
    (r"/([^&]+)((&[^&]+)*)", ViewHandler),
    (r"/([^/]+)/([^&]+)((&[^&]+)*)", UserViewHandler),
])

define('addr', group='webserver', default='127.0.0.1',
       help='Address on which to listen')
define('port', group='webserver', default=8888,
       help='Port on which to listen')
define('socket', group='webserver', default=None,
       help='Unix socket file on which to listen')

def run():
    parse_command_line()
    if options.socket:
        print('Listening on {}'.format(options.socket))
        server = HTTPServer(application)
        socket = bind_unix_socket(options.socket)
        server.add_socket(socket)
    else:
        print('Listening on {}:{}'.format(options.addr, options.port))
        application.listen(options.port, address=options.addr)
    application.debug = not production
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    run()
