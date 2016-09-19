from setuptools import setup
all_deps = ['numpy', 'pandas', 'plotly', 'seaborn', 'matplotlib']
setup(
    name='lwreport',
    version=0.1,
    py_modules=['lwreport', 'test_lwreport'],
    install_requires=[],
    extras_require={'all': all_deps},
    tests_require=["nose"] + all_deps,
    test_suite="nose.collector",
    entry_points='''
        [console_scripts]
        lwr=lwreport:main
        lwrsample=test_lwreport:gen_sample_report [all]
    ''',
)
