# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'FlexStack'
copyright = '2025, i2CAT Foundation'
author = 'i2CAT Foundation'
release = '0.9.6'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Read the docs theme options
html_theme_options = {
    'collapse_navigation': False,  # Expand navigation by default
    'sticky_navigation': True,     # Keep navigation sticky while scrolling
    'navigation_depth': 3,         # Adjust this depending on your content depth
    'includehidden': True,         # Show hidden pages in the sidebar
}
