# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

# TODO: Path to packages and modules for API documentation
sys.path.insert(0, os.path.abspath("../F-Heat_QGIS"))
# sys.path.insert(0, os.path.abspath(".."))

project = 'FHEAT'
copyright = '2024, FH Münster University of Applied Sciences'
author = 'H. Willenbrink, L. Goray, P. Sommer'
release = '2024-09-01'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# extensions = [
#     'sphinx.ext.autodoc',
#     'sphinx.ext.napoleon',
#     'sphinx.ext.viewcode',
# ]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.todo",
    "sphinx.ext.imgmath",
    "sphinx.ext.viewcode",
]

# Mock import for static html builds
autodoc_mock_imports = [
    'pandas',
    'geopandas',
    'shapely',
    'demandlib',
    'matplotlib',
    'openpyxl',
    'numpy',
    'owslib',
    'networkx',
    'qgis',
    'PyQt5'
    # Add more dependencies
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# 'alabaster' as default option

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
