"""
PointPen for reversing the winding direction of contours.

NOTE: The module is deprecated and the ``ReverseContourPointPen`` class has
been moved to ``ufoLib.pointPen`` module.
"""

from ufoLib.pointPen import AbstractPointPen, ReverseContourPointPen
import warnings


warnings.warn(
    "Importing the `defcon.pens.reverseContourPointPen` module is deprecated. "
    "Use `from ufoLib.pointPen import ReverseContourPointPen` instead.",
    DeprecationWarning, stacklevel=2)
