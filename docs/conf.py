# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# ruff: noqa: ERA001

project = "supertask"
copyright = "2022-2025, The Panodata Developers"  # noqa: A001
author = "The Panodata Developers"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.ifconfig",
    "sphinxcontrib.mermaid",
    "sphinxext.opengraph",
]

if os.getenv("SPHINX_AUTOAPI") == "true":
    extensions.append("autoapi.extension")

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "readme.md"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.

html_title = "Supertask"

html_theme_options = {
    "sidebar_hide_name": False,
    # https://github.com/pradyunsg/furo/blob/main/src/furo/assets/styles/variables/_colors.scss
    # "light_logo": "logo-light.svg",
    # "dark_logo": "logo-dark.svg",
    # #CC3333 is persian red.
    "light_css_variables": {
        "color-brand-primary": "darkcyan",
        "color-brand-content": "darkcyan",
        "color-brand-visited": "darkcyan",
        # "color-admonition-background": "orange",
    },
    "dark_css_variables": {
        "color-brand-primary": "darkcyan",
        "color-brand-content": "darkcyan",
        "color-brand-visited": "darkcyan",
        # "color-admonition-background": "orange",
    },
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}

html_show_sourcelink = True

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

# -- Intersphinx ----------------------------------------------------------

intersphinx_mapping = {
    # "influxio": ("https://influxio.readthedocs.io/", None),
}
linkcheck_ignore = []
linkcheck_anchors_ignore_for_url = [
    # Anchor 'L53' not found
    "https://github.com/.*",
]

# Disable caching remote inventories completely.
# http://www.sphinx-doc.org/en/stable/ext/intersphinx.html#confval-intersphinx_cache_limit
# intersphinx_cache_limit = 0


# -- Extension configuration -------------------------------------------------

autoapi_dirs = ["supertask"]
# autoapi_generate_api_docs = False
# autoapi_keep_files = True

sphinx_tabs_valid_builders = ["linkcheck"]
todo_include_todos = True

# Configure sphinx-copybutton
copybutton_remove_prompts = True
copybutton_line_continuation_character = "\\"
copybutton_prompt_text = r">>> |\.\.\. |\$ |sh\$ |PS> |cr> |mysql> |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# Configure sphinxext-opengraph
ogp_site_url = "https://supertask.readthedocs.io/"
ogp_enable_meta_description = True
# ogp_image = "http://example.org/image.png"
# ogp_description_length = 300


# -- Options for MyST -------------------------------------------------

myst_heading_anchors = 3
myst_enable_extensions = [
    "attrs_block",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "strikethrough",
    "substitution",
    "tasklist",
]
myst_substitutions = {}
