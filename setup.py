#!/usr/bin/env python

import sys
from setuptools import setup

try:
    import fontTools
except:
    print "*** Warning: defcon requires FontTools, see:"
    print "    fonttools.sf.net"

try:
    import robofab
except:
    print "*** Warning: defcon requires RoboFab, see:"
    print "    robofab.com"

if "sdist" in sys.argv:
    import os
    import subprocess
    import shutil
    docFolder = os.path.join(os.getcwd(), "documentation")
    # remove existing
    doctrees = os.path.join(docFolder, "build", "doctrees")
    if os.path.exists(doctrees):
        shutil.rmtree(doctrees)
    # compile
    p = subprocess.Popen(["make", "html"], cwd=docFolder)
    p.wait()
    # remove doctrees
    shutil.rmtree(doctrees)



setup(name="defcon",
    version="0.1",
    description="A set of flexible objects for representing UFO data.",
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="https://github.com/typesupply/defcon",
    license="MIT",
    packages=[
        "defcon",
        "defcon.objects",
        "defcon.pens",
        "defcon.test",
        "defcon.tools"
    ],
    package_dir={"":"Lib"}
)
