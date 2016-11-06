# MIT License
#
# Copyright (c) 2016 Olivier Bachem
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
################################################################################
# Easily create lightweight, standalone HTML reports with common objects       #
################################################################################
- Light-weight: only simple reports can be created from standard elements
- Common-data types: strings, pandas data frames, np.matrices, dictionaries,
    lists, matplotlib plts, plotly plots are supported
- Standalone: resulting in a single HTML file (albeit with www dependencies)
- Auto: publish to an automatically named directory?
- Minimal design based on bootstrap
- Auto-navigation based on bootstrap-toc
- Small footprint of HTML file

Todos:
- Name
- Finalize tests
- Readme.md
- Proper documentation

Extensions:
- Proper plotting of maps (prob with a different library)
"""

__version__ = 0.1

# Only depends upon the standard library in its basic form
import string
import webbrowser
import time
import os
import logging
import re
import SimpleHTTPServer
import SocketServer
import urllib2
import hashlib
_logger = logging.getLogger(__name__)


################################################################################
# Stuff for rendering
################################################################################

# Abstract base classes
#-------------------------------------------------------------------------------
class RenderObject(object):
    """Abstract base class for everything that can be rendered"""

    def _render(self, level):
        """Should return a string with HTML code of object"""
        raise NotImplementedError()


class Node(RenderObject):
    """Abstract base class for all classes that allow to add children"""

    def add(self, child):
        """Add a single children to the node"""
        if not hasattr(self, "children"):
            self.children = []
        self.children.append(_parse_obj(child))
        return child

    def _render_children(self, level):
        """Render children and concatenate source"""
        if not hasattr(self, "children"):
            self.children = []
        return "".join([i._render(level) for i in self.children])

# Dispatch function
#-------------------------------------------------------------------------------
def _parse_obj(obj):
    """Convert supported types into RenderObject otherwise throw error"""
    if isinstance(obj, RenderObject):
        return obj
    elif isinstance(obj, (basestring, int, float)):
        return String(str(obj))
    elif _NPY and isinstance(obj, np.ndarray):
        return Array(obj)
    elif _PDS and isinstance(obj, pd.core.frame.DataFrame):
        return DFrame(obj)
    elif _PLY and isinstance(obj, go.Figure):
        return Plot(obj)
    elif _MPL and isinstance(obj, matplotlib.figure.Figure):
        return MPlot(obj)
    else:
        raise ValueError("Type '%s' not supported for rendering!" % type(obj))

# Classes that allow children
#-------------------------------------------------------------------------------

# Regular expressions used for slugs
_re1 = re.compile(r'[^\w\s-]')
_re2 = re.compile(r'[\s]+')


class Report(Node):
    """Main class that allows creating reports"""

    def __init__(self, title):
        """Create new report with the provided `title`"""
        self.children=[]
        self.title = title

    def to_html(self, integrated=False):
        """Return report as HTML string
        
        Arguments:
          integrated (bool): If True, all css/js files are included in output.
            If False, web CDNs are used instead.

        If the report should be saved to disk, use `save` method instead.
        """
        return self._render(
                integrated=integrated,
                web=(not integrated),
                local=False,
            )

    def save(self, folder=None, filename=None, prefix=None, integrated=False,
             web=True, local=True, auto_open=True):
        """Save the report as a HTML file to disk
        
        Arguments:
          folder: (string) The folder in which to save the report. If set to 
            `None`, the report will be saved to the default path (see `get_path`).
          filename: (string) The filename used to save the report. If set to 
            `None`, the filename is inferred by "slufifying" the `title`.
          prefix: (string) The prefix to be added to the filename. If set to
            `None`, the current date and time will be used.
          integrated (bool): If True, all css/js files are included in output.
            This sets both `web` and `local` to False.
          web (bool): If True, css/js files are included from web CDNs.
          local (bool): If True, css/js files are added to directory.
          auto_open (bool): If True, the report is opened after creation.
        """
        # Folder
        if folder is None:
            folder = get_path()
        if not os.path.exists(folder):
            os.makedirs(folder)
        # Path
        if filename is None:
            filename = "%s.html" % _re2.sub('_', _re1.sub('', self.title).strip())
        if prefix is None:
            prefix = time.strftime("%Y_%m_%d-%H_%M_%S-")
        path = os.path.join(folder, prefix + filename)
        # Check integrations
        if integrated:
            web = False
            local = False
        if not (web or integrated or local):
            raise ValueError("One of `integrated`, `web` and `local` must be"
                             " True.")
        # Create the report
        if local:
            _save_res(folder)        
        with open(path, "w") as fout:
            fout.write(self._render(
                integrated=integrated,
                web=web,
                local=local
            ))

        # Auto-open
        if auto_open:
            webbrowser.open("file://%s" % os.path.abspath(path))
        
        
    def _render(self, integrated, web, local):
        """Render the report to string"""
        return _REPORT_TEMPLATE.substitute(
            title=self.title,
            content=self._render_children(1),
            soft=__name__,
            vers=__version__,
            time=time.strftime("%c"),
            header=_make_header(
                integrated=integrated,
                web=web,
                local=local
            )
        )

    
class Heading(Node):
    """HTML heading where level is automaticaly inferred"""
    def __init__(self, title):
        """Create new HTML Heading with content"""
        self.title = title
        self.children = []

    def _render(self, level):
        return _HEADING_TEMPLATE.substitute(
            title=self.title,
            content=self._render_children(level + 1),
            n=level)


class Grid(Node):
    """Grid based on Bootstrap CSS"""
    def __init__(self, n_cols=4):
        """Creates new grid

        Arguments:
          n_cols: (int in [1, 2, 3, 4, 6, 12]) Number of columns."""
        self.children = []
        if n_cols not in [1, 2, 3, 4, 6, 12]:
            raise ValueError(
                "Number of columns needs to be in [1, 2, 3, 4, 6, 12]!")
        self.n_cols = n_cols

    def _render(self, level):
        k = self.n_cols
        r = []
        for i, c in enumerate(self.children):
            if i % k == 0:
                r.append("<div class='row'>")
            r.append("<div class='col-md-%d'>%s</div>" %
                     (12 / k, c._render(level)))
            if (i + 1) % k == 0 or i + 1 == len(self.children):
                r.append("</div>")
        return "".join(r)

    
# Classes that are final nodes
#-------------------------------------------------------------------------------
 

class String(RenderObject):
    """Simple string to render (doesn't escape)"""

    def __init__(self, text):
        """Create object with HTML source `text`"""
        if not isinstance(text, str):
            raise ValueError("Only strings are supported!")
        self._text = text

    def _render(self, level):
        return self._text


class P(RenderObject):
    """Simple paragraph to render (doesn't escape)"""

    def __init__(self, text):
        """Create paragraph with HTML source `text`"""
        self._text = _parse_obj(text)

    def _render(self, level):
        return "<p>%s</p>" % self._text._render(level)


class Dict(RenderObject):
    """Render dictionaries as HTML table"""
    def __init__(self, di):
        """Create Table of dictionary `di`"""
        self.di = di

    def _render(self, level):
        e = []
        for k, v in self.di.items():
            e.append("<tr><th><b>%s</b></th><td>%s</td></tr>" %
                     (str(k), str(v)))
        return "<table class='%s'><tbody>%s</tbody></table>" % (_TABLE_CLS,
                                                                "".join(e))


class Array(RenderObject):
    """Render numpy arrays as HTML table"""
    def __init__(self, array, max_cols=15, max_rows=50):
        """Create new HTML Table out of numpy array

        Arguments:
          array: (np.ndarray) Numpy array
          max_cols: (int) maximal number of columns to display
          max_row: (int) maximal number of row to display
        """
        self.array = array
        self.max_cols = max_cols
        self.max_rows = max_rows

    def _render(self, level):
        a = self.array
        if a.ndim == 2 and _PDS:
            df = pd.DataFrame(a[0:min(a.shape[0], self.max_rows), 0:min(
                a.shape[1], self.max_cols)])
            return "<div class='table-responsive'>%s</div>" % df.to_html(
                classes=_TABLE_CLS,
                index=False,
                header=False,
                float_format=lambda x: '%.2g' % x)
        else:
            return str(a)


class DFrame(RenderObject):
    """Render Pandas data frames as HTML table"""

    def __init__(self, df):
        """Create Pandas data frame out of  `df`"""
        self.df = df

    def _render(self, level):
        if _PDS:
            return "<div class='table-responsive'>%s</div>" % self.df.to_html(
                classes=_TABLE_CLS, float_format=lambda x: '%.3g' % x)
        else:
            return str(self.df)


class Plot(RenderObject):
    """Class that renders plotly figures"""

    def __init__(self, fig):
        """Create plot from plotly figure `fig`"""
        self.fig = fig

    def _render(self, level):
        if _PLY:
            return plotly.offline.plot(
                self.fig,
                output_type="div",
                include_plotlyjs=False,
                show_link=False)
        else:
            raise ImportError("Plotly library could not be loaded!")


class MPlot(RenderObject):
    """Class that renders plotly figures"""

    def __init__(self, fig):
        """Create plotly plot from matplotlib figure `fig`"""
        self.fig = fig

    def _render(self, level):
        if _PLY:
            return plotly.offline.plot_mpl(
                self.fig,
                output_type="div",
                include_plotlyjs=False,
                show_link=False)
        else:
            raise ImportError("Plotly library could not be loaded!")


################################################################################
# Bootstrap templates
################################################################################
_TABLE_CLS = "table table-condensed table-striped table-hover table-bordered"

_REPORT_TEMPLATE = string.Template("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>${title}</title>
    ${header}
    <style type="text/css" media="screen">
      body {font-family: 'Raleway', sans-serif}
    </style>
    <script>
        $$(function() {
            var navSelector = '#toc';
            var $$myNav = $$(navSelector);
            Toc.init($$myNav);
            $$('body').scrollspy({
                target: navSelector
            });
        });
     </script>
  </head>
  <body data-spy="scroll" data-target="#toc">
    <div class="container" >
      <div  class="page-header">
        <h1 data-toc-skip>${title}</h1>
      </div>
      <div class="row">
         <div class="col-md-9">
            ${content}
         </div>
         <div class="col-md-3 hidden-print">
            <nav id="toc" data-spy="affix"></nav>
         </div>
      </div>
      <hr>
      <footer>Created with ${soft} (v${vers}) on ${time}</footer>
    </div>
  </body>
</html>
""")

_HEADING_TEMPLATE = string.Template(
    "<div><h${n}>${title}</h${n}>${content}</div>")


################################################################################
# Automatic path handling
################################################################################


_PATH = None  # Variable to save default path to save reports


def set_path(path):
    """Set the default path to save reports"""
    _logger.info("Setting default path to ''..." % path)
    _PATH = path


def get_path():
    """Get the default path to save reports"""
    return os.path.expanduser(
        os.environ.get("LWREPORT_PATH", "~/lwreports/")
        if _PATH is None else _PATH)


def open_path():
    """Open the default path to save reports"""
    return webbrowser.open("file://%s" % os.path.abspath(get_path()))


################################################################################
# Handling of headers and external CSS/JS ressources
################################################################################

_CSS = [
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css",
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css",
    "https://cdn.rawgit.com/afeld/bootstrap-toc/v0.4.1/dist/bootstrap-toc.min.css",
]
_JS = [
    "https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js",
    "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js",
    "https://cdn.rawgit.com/afeld/bootstrap-toc/v0.4.1/dist/bootstrap-toc.min.js",
    "https://cdn.plot.ly/plotly-latest.min.js",
]


def _make_header(web, local, integrated):
    """Automatically create header"""
    res = []
    for c in _CSS:
        if local:
            res.append('<link rel="stylesheet" href="%s">' % _res_filename(
                c, "css"))
        if web:
            res.append('<link rel="stylesheet" href="%s">' % c)
        if integrated:
            res.append('<style type="text/css" media="screen">%s</style>' %
                       _get_url(c))
    for c in _JS:
        if local:
            res.append('<script src="%s"></script>' % _res_filename(c, "js"))
        if web:
            res.append('<script src="%s"></script>' % c)
        if integrated:
            res.append('<script>%s</script>' % _get_url(c))
    return "".join(res)


def _save_res(folder):
    """Download ressources and save to local folder"""
    for c in _CSS:
        _save_single(folder, c, "css")
    for c in _JS:
        _save_single(folder, c, "js")


def _save_single(folder, url, ext):
    """Download a single ressource and save to local folder"""
    if not os.path.exists(folder): os.mkdir(folder)
    path = os.path.join(folder, _res_filename(url, ext))
    content = _get_url(url)
    with open(path, "w") as fout:
        fout.write(content)


def _res_filename(url, ext):
    """Returns filename for css/js ressource"""
    return ".%s%s.%s" % (ext, hashlib.md5(_get_url(url)).hexdigest(), ext)


_CACHE = {} # global to cache url requests

def _get_url(url):
    """Cached retrival of URLs in one session"""
    if not url in _CACHE:
        _CACHE[url] = urllib2.urlopen(url).read()
    return _CACHE[url]


################################################################################
# Support different libraries if available, otherwise ignore gracefully
################################################################################
# Matplotlib
try:
    _logger.debug("Trying to load Matplotlib!")
    import matplotlib as mpl
    import matplotlib.figure
    _MPL = True
except ImportError:
    _logger.info("Matplotlib not available!")
    _MPL = False

# Plotly
try:
    _logger.debug("Trying to load plotly!")
    import plotly
    import plotly.graph_objs as go
    _PLY = True
except ImportError:
    _logger.info("Plotly not available!")
    _PLY = False

# Numpy
try:
    _logger.debug("Trying to load numpy!")
    import numpy as np
    _NPY = True
except ImportError:
    _logger.info("Numpy not available!")
    _NPY = False

# Pandas
try:
    _logger.debug("Trying to load pandas!")
    import pandas as pd
    _PDS = True
except ImportError:
    _logger.info("Pandas not available!")
    _PDS = False


################################################################################
# CLI
################################################################################
def main():
    open_path()


if __name__ == "__main__":
    main()
