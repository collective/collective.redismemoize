# Configuration file for the Sphinx documentation builder.
# collective.redismemoize build configuration file


# -- Path setup --------------------------------------------------------------

from collective.redismemoize import __version__
from datetime import datetime
from datetime import UTC
from packaging.version import Version


# -- Project information -----------------------------------------------------

project = "collective.redismemoize"
author = "Plone Community"
trademark_name = "Plone"
now = datetime.now(UTC)
year = str(now.year)
copyright = year  # noqa: A001

# The full version, including alpha/beta/rc tags.
release = __version__
# The short X.Y version.
version = "v" + (Version(str(release)).base_version)


# -- General configuration ----------------------------------------------------

templates_path = ["_templates"]

extensions = [
    "myst_parser",
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",  # plone.api
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",  # plone.api
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_sitemap",
    "sphinx_tippy",
    "sphinxcontrib.httpdomain",  # plone.restapi
    "sphinxcontrib.httpexample",  # plone.restapi
    "sphinxcontrib.mermaid",
    "sphinxext.opengraph",
]

# Keep quotes and dashes as written.
smartquotes = False

# Options for the linkcheck builder
linkcheck_ignore = [
    # Ignore local and example URLs
    r"http://0.0.0.0",
    r"http://127.0.0.1",
    r"http://localhost",
    # Ignore file downloads
    r"^/_static/",
    # Ignore pages that require authentication
    r"https://github.com/collective/collective.redismemoize/issues/new",
    # Ignore github.com pages with anchors
    r"https://github.com/.*#.*",
]
linkcheck_allowed_redirects = {}
linkcheck_anchors = True
linkcheck_timeout = 5
linkcheck_retries = 1

source_suffix = {
    ".md": "markdown",
}

master_doc = "index"

exclude_patterns = []

suppress_warnings = []


# -- Options for HTML output -------------------------------------------------

html_theme = "plone_sphinx_theme"
html_logo = "_static/logo.svg"
html_favicon = "_static/favicon.ico"
# The default value includes icon-links. Override it with that item omitted,
# then add it to html_theme_options[footer_content_items].
html_sidebars = {
    "**": [
        "navbar-logo",
        "search-button-field",
        "sbt-sidebar-nav",
    ]
}
html_theme_options = {
    "article_header_start": ["toggle-primary-sidebar"],
    "extra_footer": (
        "<p>Redis is a registered trademark of Redis Ltd., "
        "used here to describe compatibility.</p>"
    ),
    "footer_content_items": [
        "author",
        "copyright",
        "last-updated",
        "extra-footer",
        "icon-links",
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/collective/collective.redismemoize",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
            "attributes": {
                "target": "_blank",
                "rel": "noopener me",
                "class": "nav-link custom-fancy-css",
            },
        },
    ],
    "logo": {
        "text": "collective.redismemoize",
    },
    "navigation_with_keys": True,
    "path_to_docs": "docs/docs",
    "repository_branch": "main",
    "repository_url": "https://github.com/collective/collective.redismemoize",
    "search_bar_text": "Search",
    "show_toc_level": 2,
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
}

html_use_opensearch = "https://collective.github.io/collective.redismemoize"

html_title = f"{project} v{release}"

html_use_index = True

html_extra_path = [
    "robots.txt",
]

html_static_path = [
    "_static",
]


# -- Options for autodoc ----------------------------------------------------

autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
autodoc_typehints = "description"
# collective.redismemoize.testing builds on test frameworks the
# documentation does not install.
autodoc_mock_imports = [
    "plone.app.contenttypes.testing",
    "plone.app.testing",
    "plone.testing",
]

# The Python API page lists the modules; their pages are written by hand.
autosummary_generate = False


# -- Options for sphinx_sitemap to html -----------------------------

html_baseurl = "https://collective.github.io/collective.redismemoize/"
sitemap_url_scheme = "{link}"
sitemap_filename = "sitemap-custom.xml"


# -- Options for myST markdown conversion to html -----------------------------

myst_enable_extensions = [
    "attrs_block",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "html_image",
    "linkify",
    "strikethrough",
    "substitution",
]

myst_heading_anchors = 3

myst_substitutions = {}


# -- Intersphinx configuration ----------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "plone": ("https://6.docs.plone.org/", None),
}


# -- Mermaid configuration ----------------------------------
mermaid_version = "11.2.0"


# -- OpenGraph configuration ----------------------------------
ogp_site_url = "https://collective.github.io/collective.redismemoize/"
ogp_description_length = 200
ogp_image = "https://collective.github.io/collective.redismemoize/_static/logo.svg"
ogp_site_name = "collective.redismemoize Documentation"
ogp_type = "website"
ogp_custom_meta_tags = [
    '<meta property="og:locale" content="en_US" />',
]


# -- sphinx-notfound-page configuration ----------------------------------
# GitHub Pages serves the project under its repository name.
notfound_urls_prefix = "/collective.redismemoize/"
notfound_template = "404.html"


# -- sphinx-tippy configuration ----------------------------------
tippy_anchor_parent_selector = "article.bd-article"
tippy_enable_doitips = False
tippy_enable_wikitips = False
tippy_props = {
    "interactive": True,
    "placement": "auto-end",
}


# -- Options for HTML help output -------------------------------------------------

htmlhelp_basename = "collective.redismemoizeDocumentation"
