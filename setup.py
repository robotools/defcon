#!/usr/bin/env python

import sys
from distutils.core import setup

try:
    import fontTools
except:
    print "*** Warning: defcon requires FontTools, see:"
    print "    github.com/behdad/fonttools"

try:
    import robofab
except:
    print "*** Warning: defcon requires RoboFab, see:"
    print "    robofab.com"
    
try:
    import ufoLib
except:
    print "*** Warning: defcon requires ufoLib, see:"
    print "    github.com/unified-font-object/ufoLib"

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
    url="http://code.typesupply.com",
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
