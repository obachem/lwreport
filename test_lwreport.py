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
Tests
"""
import tempfile
import shutil
from collections import OrderedDict
import lwreport as lwr
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import matplotlib.pyplot as plt


def sample_report():
    """Creates a sample report"""
    # We create a sample report
    report = lwr.Report("Light-weight Standalone Reports")

    # Description
    report.add(lwr.P("The <emph>lwreport</emph> library allows to create "
                     "standalone HTML reports extremely easily. A lot of "
                     "different elements are available!</p>"))

    # Iteratively add stuff by using add shortcut
    h1 = report.add(lwr.Heading("Heading 1"))
    h2 = h1.add(lwr.Heading("Heading 2"))
    h3 = h2.add(lwr.Heading("Heading 3"))
    h4 = h3.add(lwr.Heading("Heading 4"))
    h5 = h4.add(lwr.Heading("Heading 5"))
    h5.add(lwr.P("Any HTML code can simply be added. <b>Pretty cool!</b>"))

    # Output dictionaries (use OrderedDict to control display order)
    di = OrderedDict()
    di["Name"] = "James Bond"
    di["Nationality"] = "British"
    di["Height (m)/weight (kg)"] = [1.8, 84]

    h1 = report.add(lwr.Heading("Dictionaries"))
    h1.add(lwr.P("Dictionaries are automatically rendered as tables."))
    h1.add(lwr.Dict(di))

    # Numpy arrays
    h1 = report.add(lwr.Heading("Numpy arrays"))
    h1.add(lwr.P("2-dimensional arrays are automatically formatted as tables!"))
    X = np.arange(900).reshape((30, 30))
    h1.add(X)

    # Pandas data frame
    h1 = report.add(lwr.Heading("Pandas data frame"))
    h1.add(lwr.P("Pandas data frames are automatically formatted as tables"))
    X = np.arange(100).reshape((10, 10))
    df = pd.DataFrame(X, ["R%d" % i for i in range(10)],
                      ["C%d" % i for i in range(10)])
    h1.add(df)

    # Plotly plots
    h1 = report.add(lwr.Heading("Plotly plots"))
    h1.add(lwr.P("It's ridiculously easity to add plotly plots."))
    x = np.linspace(0, 10)
    s = go.Scatter(x=x, y=np.sin(x), name="Sine")
    c = go.Scatter(x=x, y=np.cos(x), name="Cosine")
    h1.add(go.Figure(data=[s, c]))
    data = [dict(
        type='choropleth',
        locations=["CHE"],
        z=[1.0],
        autocolorscale=True, )]

    layout = dict(
        title='Where is Switzerland?',
        geo=dict(
            scope='world',
            projection=dict(type='Mercator'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)'), )

    fig = go.Figure(data=data, layout=layout)
    h1.add(fig)

    # Matplotlib plots
    h1 = report.add(lwr.Heading("Matplotlib plots"))
    h1.add(lwr.P("Even matplotlib plots are rendered through plotly."))
    fig, ax = plt.subplots()
    x, y = np.arange(100, dtype=np.float64).reshape((2, 50))
    sc = ax.scatter(x, y)
    ax.grid()
    h1.add(fig)

    # Easily create a Grid with elements
    h1 = report.add(lwr.Heading("Grids"))
    h1.add(lwr.P("The report can be split into simple grids!"))
    for n in [2, 3, 4, 6]:
        h2 = h1.add(lwr.Heading("Grid of %d" % n))
        grid = h2.add(lwr.Grid(n_cols=n))
        for i in range(2 * n):
            grid.add(lwr.Heading("Element %d" % i)).add(lwr.P("Text %d" % i))
    return report

def test():
    """Test that tests and showcases full functionality"""
    report = sample_report()
    r = report.to_html()
    try:
        d = tempfile.mkdtemp()
        report.save(folder=d, auto_open=False)
        report.save(folder=d, prefix="", auto_open=False)
        report.save(folder=d, filename="test", auto_open=False)
        report.save(folder=d, auto_open=False, web=False)
        report.save(folder=d, auto_open=False, integrated=True)
    finally:
        shutil.rmtree(d)

def gen_sample_report():
    """Create a sample report"""
    sample_report().save()
