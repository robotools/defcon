#!/usr/bin/env python
from __future__ import print_function
import sys
from setuptools import setup

try:
    import fontTools
except:
    print("*** Warning: defcon requires fontTools, see:")
    print("    https://github.com/behdad/fonttools")

try:
    import ufoLib
except:
    print("*** Warning: defcon requires ufoLib, see:")
    print("    https://github.com/unified-font-object/ufoLib")

if "sdist" in sys.argv:
    try:
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
    except:
        print("*** Warning: could not make html documentation")



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
    package_dir={"":"Lib"},
    test_suite="defcon.test",
)
