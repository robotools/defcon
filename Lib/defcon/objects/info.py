from defcon.objects.base import BaseObject


class Info(BaseObject):

    # this code is automatically generated

    def __init__(self, dispatcher=None):
        super(Info, self).__init__(dispatcher)
        self._dirty = False
        self._familyName = None
        self._styleName = None
        self._fullName = None
        self._fontName = None
        self._menuName = None
        self._fontStyle = None
        self._note = None
        self._versionMajor = None
        self._versionMinor = None
        self._year = None
        self._copyright = None
        self._notice = None
        self._trademark = None
        self._license = None
        self._licenseURL = None
        self._createdBy = None
        self._designer = None
        self._designerURL = None
        self._vendorURL = None
        self._unitsPerEm = None
        self._ascender = None
        self._descender = None
        self._capHeight = None
        self._xHeight = None
        self._defaultWidth = None
        self._slantAngle = None
        self._italicAngle = None
        self._widthName = None
        self._weightName = None
        self._weightValue = None
        self._fondName = None
        self._otFamilyName = None
        self._otStyleName = None
        self._otMacName = None
        self._msCharSet = None
        self._fondID = None
        self._uniqueID = None
        self._ttVendor = None
        self._ttUniqueID = None
        self._ttVersion = None

    def _get_familyName(self):
        return self._familyName

    def _set_familyName(self, value):
        if self._familyName != value:
            self._familyName = value
            self.dirty = True

    familyName = property(_get_familyName, _set_familyName)

    def _get_styleName(self):
        return self._styleName

    def _set_styleName(self, value):
        if self._styleName != value:
            self._styleName = value
            self.dirty = True

    styleName = property(_get_styleName, _set_styleName)

    def _get_fullName(self):
        return self._fullName

    def _set_fullName(self, value):
        if self._fullName != value:
            self._fullName = value
            self.dirty = True

    fullName = property(_get_fullName, _set_fullName)

    def _get_fontName(self):
        return self._fontName

    def _set_fontName(self, value):
        if self._fontName != value:
            self._fontName = value
            self.dirty = True

    fontName = property(_get_fontName, _set_fontName)

    def _get_menuName(self):
        return self._menuName

    def _set_menuName(self, value):
        if self._menuName != value:
            self._menuName = value
            self.dirty = True

    menuName = property(_get_menuName, _set_menuName)

    def _get_fontStyle(self):
        return self._fontStyle

    def _set_fontStyle(self, value):
        if self._fontStyle != value:
            self._fontStyle = value
            self.dirty = True

    fontStyle = property(_get_fontStyle, _set_fontStyle)

    def _get_note(self):
        return self._note

    def _set_note(self, value):
        if self._note != value:
            self._note = value
            self.dirty = True

    note = property(_get_note, _set_note)

    def _get_versionMajor(self):
        return self._versionMajor

    def _set_versionMajor(self, value):
        if self._versionMajor != value:
            self._versionMajor = value
            self.dirty = True

    versionMajor = property(_get_versionMajor, _set_versionMajor)

    def _get_versionMinor(self):
        return self._versionMinor

    def _set_versionMinor(self, value):
        if self._versionMinor != value:
            self._versionMinor = value
            self.dirty = True

    versionMinor = property(_get_versionMinor, _set_versionMinor)

    def _get_year(self):
        return self._year

    def _set_year(self, value):
        if self._year != value:
            self._year = value
            self.dirty = True

    year = property(_get_year, _set_year)

    def _get_copyright(self):
        return self._copyright

    def _set_copyright(self, value):
        if self._copyright != value:
            self._copyright = value
            self.dirty = True

    copyright = property(_get_copyright, _set_copyright)

    def _get_notice(self):
        return self._notice

    def _set_notice(self, value):
        if self._notice != value:
            self._notice = value
            self.dirty = True

    notice = property(_get_notice, _set_notice)

    def _get_trademark(self):
        return self._trademark

    def _set_trademark(self, value):
        if self._trademark != value:
            self._trademark = value
            self.dirty = True

    trademark = property(_get_trademark, _set_trademark)

    def _get_license(self):
        return self._license

    def _set_license(self, value):
        if self._license != value:
            self._license = value
            self.dirty = True

    license = property(_get_license, _set_license)

    def _get_licenseURL(self):
        return self._licenseURL

    def _set_licenseURL(self, value):
        if self._licenseURL != value:
            self._licenseURL = value
            self.dirty = True

    licenseURL = property(_get_licenseURL, _set_licenseURL)

    def _get_createdBy(self):
        return self._createdBy

    def _set_createdBy(self, value):
        if self._createdBy != value:
            self._createdBy = value
            self.dirty = True

    createdBy = property(_get_createdBy, _set_createdBy)

    def _get_designer(self):
        return self._designer

    def _set_designer(self, value):
        if self._designer != value:
            self._designer = value
            self.dirty = True

    designer = property(_get_designer, _set_designer)

    def _get_designerURL(self):
        return self._designerURL

    def _set_designerURL(self, value):
        if self._designerURL != value:
            self._designerURL = value
            self.dirty = True

    designerURL = property(_get_designerURL, _set_designerURL)

    def _get_vendorURL(self):
        return self._vendorURL

    def _set_vendorURL(self, value):
        if self._vendorURL != value:
            self._vendorURL = value
            self.dirty = True

    vendorURL = property(_get_vendorURL, _set_vendorURL)

    def _get_unitsPerEm(self):
        return self._unitsPerEm

    def _set_unitsPerEm(self, value):
        if self._unitsPerEm != value:
            self._unitsPerEm = value
            self.dirty = True

    unitsPerEm = property(_get_unitsPerEm, _set_unitsPerEm)

    def _get_ascender(self):
        return self._ascender

    def _set_ascender(self, value):
        if self._ascender != value:
            self._ascender = value
            self.dirty = True

    ascender = property(_get_ascender, _set_ascender)

    def _get_descender(self):
        return self._descender

    def _set_descender(self, value):
        if self._descender != value:
            self._descender = value
            self.dirty = True

    descender = property(_get_descender, _set_descender)

    def _get_capHeight(self):
        return self._capHeight

    def _set_capHeight(self, value):
        if self._capHeight != value:
            self._capHeight = value
            self.dirty = True

    capHeight = property(_get_capHeight, _set_capHeight)

    def _get_xHeight(self):
        return self._xHeight

    def _set_xHeight(self, value):
        if self._xHeight != value:
            self._xHeight = value
            self.dirty = True

    xHeight = property(_get_xHeight, _set_xHeight)

    def _get_defaultWidth(self):
        return self._defaultWidth

    def _set_defaultWidth(self, value):
        if self._defaultWidth != value:
            self._defaultWidth = value
            self.dirty = True

    defaultWidth = property(_get_defaultWidth, _set_defaultWidth)

    def _get_slantAngle(self):
        return self._slantAngle

    def _set_slantAngle(self, value):
        if self._slantAngle != value:
            self._slantAngle = value
            self.dirty = True

    slantAngle = property(_get_slantAngle, _set_slantAngle)

    def _get_italicAngle(self):
        return self._italicAngle

    def _set_italicAngle(self, value):
        if self._italicAngle != value:
            self._italicAngle = value
            self.dirty = True

    italicAngle = property(_get_italicAngle, _set_italicAngle)

    def _get_widthName(self):
        return self._widthName

    def _set_widthName(self, value):
        if self._widthName != value:
            self._widthName = value
            self.dirty = True

    widthName = property(_get_widthName, _set_widthName)

    def _get_weightName(self):
        return self._weightName

    def _set_weightName(self, value):
        if self._weightName != value:
            self._weightName = value
            self.dirty = True

    weightName = property(_get_weightName, _set_weightName)

    def _get_weightValue(self):
        return self._weightValue

    def _set_weightValue(self, value):
        if self._weightValue != value:
            self._weightValue = value
            self.dirty = True

    weightValue = property(_get_weightValue, _set_weightValue)

    def _get_fondName(self):
        return self._fondName

    def _set_fondName(self, value):
        if self._fondName != value:
            self._fondName = value
            self.dirty = True

    fondName = property(_get_fondName, _set_fondName)

    def _get_otFamilyName(self):
        return self._otFamilyName

    def _set_otFamilyName(self, value):
        if self._otFamilyName != value:
            self._otFamilyName = value
            self.dirty = True

    otFamilyName = property(_get_otFamilyName, _set_otFamilyName)

    def _get_otStyleName(self):
        return self._otStyleName

    def _set_otStyleName(self, value):
        if self._otStyleName != value:
            self._otStyleName = value
            self.dirty = True

    otStyleName = property(_get_otStyleName, _set_otStyleName)

    def _get_otMacName(self):
        return self._otMacName

    def _set_otMacName(self, value):
        if self._otMacName != value:
            self._otMacName = value
            self.dirty = True

    otMacName = property(_get_otMacName, _set_otMacName)

    def _get_msCharSet(self):
        return self._msCharSet

    def _set_msCharSet(self, value):
        if self._msCharSet != value:
            self._msCharSet = value
            self.dirty = True

    msCharSet = property(_get_msCharSet, _set_msCharSet)

    def _get_fondID(self):
        return self._fondID

    def _set_fondID(self, value):
        if self._fondID != value:
            self._fondID = value
            self.dirty = True

    fondID = property(_get_fondID, _set_fondID)

    def _get_uniqueID(self):
        return self._uniqueID

    def _set_uniqueID(self, value):
        if self._uniqueID != value:
            self._uniqueID = value
            self.dirty = True

    uniqueID = property(_get_uniqueID, _set_uniqueID)

    def _get_ttVendor(self):
        return self._ttVendor

    def _set_ttVendor(self, value):
        if self._ttVendor != value:
            self._ttVendor = value
            self.dirty = True

    ttVendor = property(_get_ttVendor, _set_ttVendor)

    def _get_ttUniqueID(self):
        return self._ttUniqueID

    def _set_ttUniqueID(self, value):
        if self._ttUniqueID != value:
            self._ttUniqueID = value
            self.dirty = True

    ttUniqueID = property(_get_ttUniqueID, _set_ttUniqueID)

    def _get_ttVersion(self):
        return self._ttVersion

    def _set_ttVersion(self, value):
        if self._ttVersion != value:
            self._ttVersion = value
            self.dirty = True

    ttVersion = property(_get_ttVersion, _set_ttVersion)


if __name__ == "__main__":
    import doctest
    doctest.testmod()