#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cgi import FieldStorage, escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter

from string import letters, digits
from random import choice
from os.path import isfile, basename
from subprocess import Popen, PIPE

### Options
title = u'Paste it §'
filename_path = 'pastes'
filename_length = 3
filename_characters = letters + digits
mldown_path = 'mldown' # if '', disable the mldown option
mldown_args = []
charset = ('charset', 'utf-8')
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
    res += '</select>'
    return res
        
def paste_form():
    res = ''
    res += '<form method="post" action="/" enctype="multipart/form-data">'
    res += '<textarea name="paste" rows="20" cols="80"></textarea><br/>'
    res += language_box()
    res += option_boxes()
    res += '<input type="submit" value="Paste" />'
    return res

### Access to disk (read & write paste)
def random_filename():
    res = filename_path + '/'
    for i in xrange(filename_length):
        res += choice(filename_characters)
    return res

def new_path():
    filename = random_filename()
    while isfile(filename):
        filename = random_filename()
    return filename

def dump_paste(content):
    filename = new_path()
    f = open(filename, 'w')
    f.write(content)
    f.close()
    return filename

def read_paste(filename):
    f = open(filename, 'r')
    return f.read()

### App
def paste(environ, start_response):
    params = FieldStorage(fp=environ['wsgi.input'],
                              environ=environ,
                              keep_blank_values = True)
    html_pre = u'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
<head>
  <title>''' + title + '''</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <link rel="stylesheet" type="text/css" href="paste.css" />
</head>
<body>
<h1>''' + title + '''</h1>'''
    html_post = u''
    body = u''

    if 'id' in params:
        body = read_paste(filename_path + '/' + params.getvalue('id'))
        if 'raw' in params:
            start_response('200 OK', [('Content-Type', 'text/plain'), charset])
            return body
        elif 'mldown' in params:
            start_response('200 OK', [('Content-Type', 'text/html'), charset])
            return format_mldown(body)
        elif 'hl' in params:
            body = (highlight_code(body, params.getvalue('hl')))
        else:
            body = escape(body)
            html_pre += '<pre>'
            html_post += '</pre>'
    elif 'paste' in params:
        options = basename(dump_paste(params.getvalue('paste')))
        if 'mldown' in params:
            options += '&mldown'
        elif params.getvalue('hl', '') != '':
            options += '&hl=' + params.getvalue('hl')
            
        if 'script' in params:
            start_response('200 OK', [('Content-Type', 'text/plain'), charset])
            return options
        body = 'Your paste is located <a href="' + base_url + options + '">here</a>'
    else:
        body = paste_form()

    html_post += '</body></html>'

    start_response('200 OK', [('Content-Type', 'text/html'), charset])
    # body is already encoded (by highlight_code, or read_paste)
    return html_pre.encode('utf-8') + body + html_post.encode('utf-8')

