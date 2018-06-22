# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

from datetime import datetime

from recommonmark.parser import CommonMarkParser

extensions = ["sphinx.ext.autodoc",]
templates_path = ['/home/docs/checkouts/readthedocs.org/readthedocs/templates/sphinx', 'templates', '_templates', '.templates']
source_suffix = ['.rst', '.md']
source_parsers = {
            '.md': CommonMarkParser,
        }
master_doc = 'index'
project = u'CampBot'
copyright = "Charles de Beauchesne " + str(datetime.now().year)
version = 'latest'
release = 'latest'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'campbot'
html_theme = 'sphinx_rtd_theme'
file_insertion_enabled = False
latex_documents = [
  ('index', 'campbot.tex', u'CampBot Documentation',
   u'', 'manual'),
]