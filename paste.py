#!/usr/bin/env python
from cgi import parse_qs, escape
from wsgiref.simple_server import make_server

from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter

from string import characters, digits
from random import choice

### Options
filename_path = 'pastes'
filename_length = 10
filename_characters = string.characters + string.digits

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
    return (checkbox('hl-p', 'Highlighting', checked=True) + 
            checkbox('escape-p', 'HTML escaping'))

def language_box():
    res = '<select name="hl">'
    for (lang, language) in list_languages():
        res += '<option value="' + lang + '">' + language + '</option>\n'
    res += '</select>'
        
def paste_form():
    res = ''
    res += '<form method="post" action="/" enctype="multipart/form-data">'
    res += '<textarea name="paste" rows="20" cols="80"/><br/>'
    res += language_box()
    res += option_boxes()
    return res

### Access to disk (read & write paste)
def random_filename():
    res = filename_path + '/'
    for i in xrange(filename_length):
        res += random.choice(filename_characters)
    return res

def new_path():
    filename = random_filename()
    while path.isfile(filename):
        filename = random_filename()
    return filename

def dump_paste(content):
    filename = new_path()
    f = open(filename, "w")
    f.write(content)
    f.close()
    return filename

def read_paste(filename):
    f = open(filename, "r")
    return f.read()

### App
def paste(environ, start_response):
    # TODO

def start(port):
    srv = make_server('localhost', port, paste)
    srv.serve_forever()

if __name__ == '__main__':
    start(8080)
