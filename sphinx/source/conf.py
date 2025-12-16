import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'gee_acolite'
copyright = '2025, Sergio Heredia'
author = 'Sergio Heredia'
release = '1.0.1'
version = '1.0.1'

# Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosummary',
    'sphinx.ext.githubpages',
    'nbsphinx',
    'IPython.sphinxext.ipython_console_highlighting',
]

# Nbsphinx configuration
nbsphinx_allow_errors = True
nbsphinx_execute = 'never'

# Autosummary configuration
autosummary_generate = False

# Template and static paths
templates_path = ['_templates']
html_static_path = ['_static']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**/generated']

# HTML output configuration
html_theme = 'sphinx_book_theme'
html_extra_path = ['.nojekyll']
html_baseurl = 'https://aouei.github.io/gee_acolite/'

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
