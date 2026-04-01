"""Sphinx configuration for qdk-pythonic documentation."""

project = "qdk-pythonic"
copyright = "2026, qdk-pythonic contributors"
author = "qdk-pythonic contributors"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

exclude_patterns = ["design/**"]

html_theme = "sphinx_rtd_theme"
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
