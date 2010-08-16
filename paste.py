#!/usr/bin/env python
from cgi import FieldStorage, escape
from wsgiref.simple_server import make_server

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter

from string import letters, digits
from random import choice
from os.path import isfile, basename

### Options
filename_path = 'pastes'
filename_length = 10
filename_characters = letters + digits

### Pygments stuff
def highlight_code(code, lang):
    return highlight(code, get_lexer_by_name(lang), HtmlFormatter())

def list_languages():
    return sorted(map(lambda x: (x[0], x[1][0]), get_all_lexers()),
                  key=lambda x: x[1].lower())

### Paste form
def checkbox(name, label, checked=False, value="on"):
    res = '<label><input type="checkbox" name="' + name + '" value="' + value + '" '
    if checked:
        res += 'checked="checked"'
    res += '/>' + label + '</label>\n'
    return res

def option_boxes():
    return checkbox('escape', 'HTML escaping', checked=True)

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
    res += '<input type="submit" name="Paste it §" />'
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
    f = open(filename, "r")
    return f.read()

### App
def paste(environ, start_response):
    params = FieldStorage(fp=environ['wsgi.input'],
                              environ=environ,
                              keep_blank_values = True)
    html_pre = '<h1>Paste it §</h1>'
    if 'id' in params:
        body = read_paste(filename_path + '/' + params.getvalue('id'))
        if 'raw' in params:
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return body
        if 'ne' in params:
            body = escape(body)
        if 'hl' in params:
            body = str(highlight_code(body, params.getvalue('hl')))
        else:
            html_pre += '<pre>'
            html_post = '</pre>'
    elif 'paste' in params:
        options = '?id=' + basename(dump_paste(params.getvalue('paste')))
        if params.getvalue('hl', '') != '':
            options += "&hl=" + params.getvalue('hl')
        if params.getvalue('escape', 'off') == 'on':
            options += "&ne"
            
        body = 'Your paste is located <a href="' + options + '">here</a>'
    else:
        body = paste_form()

    html_post = ""

    start_response('200 OK', [('Content-Type', 'text/html')])
    return html_pre + body + html_post

def start(port):
    srv = make_server('localhost', port, paste)
    srv.serve_forever()

if __name__ == '__main__':
    start(8080)
