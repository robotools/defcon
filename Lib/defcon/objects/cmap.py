import unicodedata
from defcon.tools import unicodeTools
from defcon.objects.base import BaseDictObject


class UnicodeData(BaseDictObject):

    _notificationName = "UnicodeData.Changed"

    def __init__(self):
        super(UnicodeData, self).__init__()
        self._glyphNameToForcedUnicode = {}
        self._forcedUnicodeToGlyphName = {}

    # -----------
    # set and get
    # -----------

    def removeGlyphData(self, glyphName, values):
        for value in values:
            if value not in self._dict:
                continue
            glyphList = self._dict[value]
            glyphList.remove(glyphName)
            if not glyphList:
                del self._dict[value]
        # remove the forced reference to the glyph
        if glyphName in self._glyphNameToForcedUnicode:
            fourcedValue = self._glyphNameToForcedUnicode[glyphName]
            del self._glyphNameToForcedUnicode[glyphName]
            del self._forcedUnicodeToGlyphName[fourcedValue]
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

    def addGlyphData(self, glyphName, values):
        for value in values:
            # update unicode to glyph name
            glyphList = self._dict.get(value)
            if glyphList is None:
                glyphList = []
            if glyphName not in glyphList:
                glyphList.append(glyphName)
            self._dict[value] = glyphList
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

    def __delitem__(self, value):
        glyphList = self._dict.get(value)
        if glyphList is None:
            return
        for glyphName in glyphList:
            # remove forced references
            if glyphName in self._glyphNameToForcedUnicode:
                forcedValue = self._glyphNameToForcedUnicode[glyphName]
                del self._forcedUnicodeToGlyphName[forcedValue]
                del self._glyphNameToForcedUnicode[glyphName]
        del self._dict[value]
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

    def __setitem__(self, value, glyphList):
        if value not in self._dict:
            self._dict[value] = []
        for glyphName in glyphList:
            self._dict[value].append(glyphName)
            # remove now out dated forced references
            if glyphName in self._glyphNameToForcedUnicode:
                forcedValue = self._glyphNameToForcedUnicode[glyphName]
                del self._forcedUnicodeToGlyphName[forcedValue]
                del self._glyphNameToForcedUnicode[glyphName]
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

    def clear(self):
        raise NotImplementedError

    def update(self, other):
        for value, glyphList in other.items():
            for glyphName in glyphList:
                if glyphName in self._glyphNameToForcedUnicode:
                    forcedValue = self._glyphNameToForcedUnicode[glyphName]
                    del self._forcedUnicodeToGlyphName[forcedValue]
                    del self._glyphNameToForcedUnicode[glyphName]
            self._dict[value] = list(glyphList)
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

    # -------
    # Loaders
    # -------

    def _setupForcedValueDict(self):
        for value, glyphList in self.values():
            if not glyphList:
                glyphName = None
            else:
                glyphName = glyphList[0]
            if value >= _privateUse1Min and value <= _privateUse1Max:
                self._forcedUnicodeToGlyphName[value] = glyphName
            elif value >= _privateUse2Min and value <= _privateUse2Max:
                self._forcedUnicodeToGlyphName[value] = glyphName
            elif value >= _privateUse3Min  and value <= _privateUse3Max:
                self._forcedUnicodeToGlyphName[value] = glyphName

    def _loadForcedUnicodeValue(self, glyphName):
        # already loaded
        if glyphName in self._glyphNameToForcedUnicode:
            return
        # glyph has a real unicode
        if self.unicodeForGlyphName(glyphName) is not None:
            return
        # start at the highest point, falling back to the bottom of the PUA
        startPoint = max(self._forcedUnicodeToGlyphName.keys() + [_privateUse1Min])
        # find the value and store it
        value = _findAvailablePUACode(self._forcedUnicodeToGlyphName)
        self._forcedUnicodeToGlyphName[value] = glyphName
        self._glyphNameToForcedUnicode[glyphName] = value

    # ---------------
    # Value Retrieval
    # ---------------

    def unicodeForGlyphName(self, glyphName):
        font = self.getParent()
        if glyphName not in font:
            return None
        glyph = font[glyphName]
        unicodes = glyph.unicodes
        if not unicodes:
            return None
        return unicodes[0]

    def glyphNameForUnicode(self, value):
        glyphList = self.get(value)
        if not glyphList:
            return None
        return glyphList[0]

    def pseudoUnicodeForGlyphName(self, glyphName):
        realValue = self.unicodeForGlyphName(glyphName)
        if realValue is not None:
            return realValue
        # glyph doesn't have a suffix
        if glyphName.startswith(".") or glyphName.startswith("_"):
            return None
        if "." not in glyphName and "_" not in glyphName:
            return None
        # get the base
        base = glyphName.split(".")[0]
        # in the case of ligatures, grab the first glyph
        base = glyphName.split("_")[0]
        # get the value for the base
        return self.unicodeForGlyphName(base)

    def forcedUnicodeForGlyphName(self, glyphName):
        realValue = self.unicodeForGlyphName(glyphName)
        if realValue is not None:
            return realValue
        if glyphName not in self._glyphNameToForcedUnicode:
            self._loadForcedUnicodeValue(glyphName)
        return self._glyphNameToForcedUnicode[glyphName]

    def glyphNameForForcedUnicode(self, value):
        if value in self:
            glyphName = self[value]
            if isinstance(glyphName, list):
                glyphName = glyphName[0]
            return glyphName
        # A value will not be considered valid until it has
        # been mapped to a glyph name. Therefore, unknown
        # values should return None
        if value not in self._forcedUnicodeToGlyphName:
            return None
        return self._forcedUnicodeToGlyphName[value]

    # -------------
    # Decomposition
    # -------------

    def _findDecomposedBaseForGlyph(self, glyphName, allowPseudoUnicode):
        if allowPseudoUnicode:
            uniValue = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            uniValue = self.unicodeForGlyphName(glyphName)
        if uniValue is None:
            return
        if uniValue is not None:
            decomposition = recursiveDecomposition(uniValue)
            if decomposition != -1:
                if decomposition in font.unicodeData:
                    baseGlyphName = font.unicodeData[decomposition][0]
                    if "." in glyphName.unicodeData:
                        suffix = glyphName.split(".", 1)[1]
                        baseWithSuffix = baseGlyphName + "." + suffix
                        if baseWithSuffix in font:
                            baseGlyphName = baseWithSuffix
                    return baseGlyphName
        return glyphName

    # -------
    # Sorting
    # -------

    def sortGlyphNames(self, glyphNames, sortDescriptors=[dict(type="unicode")]):
        """
        This sorts the list of glyphs following the sort descriptors
        provided in the sortDescriptors list. Ths works by iterating over
        the sort descriptors and subdividing. For example, if the first
        sort descriptor is a suffix type, internally, the result of the
        sort will look something like this:
            [
                [glyphs with no suffix],
                [glyphs with suffix 1],
                [glyphs with suffix 2]
            ]
        When the second sort descriptor is processed, the results of previous
        sorts are subdivided even further. For example, if the second
        sort type is script:
            [[
                [glyphs with no suffix, script 1], [glyphs with no suffix, script 2],
                [glyphs with suffix 1, script 1], [glyphs with suffix 1, script 2],
                [glyphs with suffix 2, script 1], [glyphs with suffix 2, script 2]
            ]]
        And so on. The returned list will be flattened.

        Sort Descriptor - A dict containing the following:
        type - The type of sort to perform. See below for options.
        ascending - Boolean representing if the glyphs should be in
            ascending or descending order. Optional. The default is True.
        allowPseudoUnicode - Boolean representing if pseudo Unicode
            values are used. If not, real Unicode values will be used
            if necessary. Optional. The default is False.

        Sort Types:
        alphabetical - Self-explanitory.
        unicode - Sort based on Unicode value.
        script - Sort based on Unicode script.
        category - Sort based on Unicode category.
        block - Sort vased on Unicode block.
        suffix - Sort based on glyph name suffix.
        decompositionBase = Sort based on the base glyph defined in the decomposition rules.
        """
        blocks = [glyphNames]
        typeToMethod = dict(
            alphabetical=self._sortByAlphabet,
            unicode=self._sortByUnicode,
            category=self._sortByCategory,
            block=self._sortByBlock,
            script=self._sortByScript,
            suffix=self._sortBySuffix,
            decompositionBase=self._sortByDecompositionBase
        )
        for sortDescriptor in sortDescriptors:
            sortType = sortDescriptor["type"]
            ascending = sortDescriptor.get("ascending", True)
            allowPseudoUnicode = sortDescriptor.get("allowPseudoUnicode", False)
            sortMethod = typeToMethod[sortType]

            newBlocks = []
            for block in blocks:
                sortedBlock = self._sortRecurse(blocks, sortMethod, ascending, allowPseudoUnicode)
                newBlocks.append(sortedBlock)
            blocks = newBlocks
        return self._flattenSortResult(blocks)

    def _flattenSortResult(self, result):
        final = []
        for i in result:
            if isinstance(i, list):
                final.extend(self._flattenSortResult(i))
            else:
                final.append(i)
        return final

    def _sortRecurse(self, blocks, sortMethod, ascending, allowPseudoUnicode):
        if not blocks:
            return []
        if isinstance(blocks[0], list):
            sortedBlocks = []
            for block in blocks:
                block = self._sortRecurse(block, sortMethod, ascending, allowPseudoUnicode)
                sortedBlocks.append(block)
            return sortedBlocks
        else:
            return sortMethod(blocks, ascending, allowPseudoUnicode)

    def _sortByAlphabet(self, glyphNames, ascending, allowPseudoUnicode):
        result = sorted(glyphNames)
        if not ascending:
            result = reversed(result)
        result = list(result)
        return result

    def _sortBySuffix(self, glyphNames, ascending, allowPseudoUnicode):
        suffixToGlyphs = {None : []}
        for glyphName in glyphNames:
            if "." not in glyphName or glyphName.startswith("."):
                suffix = None
            else:
                suffix = glyphName.split(".", 1)[1]
            if suffix not in suffixToGlyphs:
                suffixToGlyphs[suffix] = []
            suffixToGlyphs[suffix].append(glyphName)
        result = []
        result.append(suffixToGlyphs.pop(None))
        for suffix, glyphList in sorted(suffixToGlyphs.items()):
            result.append(glyphList)
        return result

    def _sortByUnicode(self, glyphNames, ascending, allowPseudoUnicode):
        withValue = []
        withoutValue = []
        for glyphName in glyphNames:
            if allowPseudoUnicode:
                value = self.pseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.unicodeForGlyphName(glyphName)
            if value is None:
                withoutValue.append(glyphName)
            else:
                withValue.append((value, glyphName))
        withValue = [glyphName for uniValue, glyphName in sorted(withValue)]
        if not ascending:
            withValue = list(reversed(withValue))
            withoutValue = list(reversed(withoutValue))
            result = [withoutValue, withValue]
        else:
            result = [withValue, withoutValue]
        return result

    def _sortByScript(self, glyphNames, ascending, allowPseudoUnicode):
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, unicodeTools.script, unicodeTools.orderedScripts)

    def _sortByBlock(self, glyphNames, ascending, allowPseudoUnicode):
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, unicodeTools.block, unicodeTools.orderedBlocks)

    def _sortByCategory(self, glyphNames, ascending, allowPseudoUnicode):
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, unicodeTools.category, unicodeTools.orderedCategories)

    def _sortByUnicodeLookup(self, glyphNames, ascending, allowPseudoUnicode, tagLookup, orderedTags):
        tagToGlyphs = {}
        for glyphName in glyphNames:
            if allowPseudoUnicode:
                value = self.pseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.unicodeForGlyphName(glyphName)
            if value is None:
                tag = None
            else:
                tag = tagLookup(value)
            if tag not in tagToGlyphs:
                tagToGlyphs[tag] = []
            tagToGlyphs[tag].append(glyphName)
        if not orderedTags:
            orderedTags = sorted(tagToGlyphs.keys())
            if None in orderedTags:
                orderedTags.remove(None)
        sortedResult = []
        for tag in orderedTags + [None]:
            if tag in tagToGlyphs:
                sortedResult.append(tagToGlyphs[tag])
        if not ascending:
            sortedResult = list(reversed(sortedResult))
        return sortedResult

    def _sortByDecompositionBase(self, glyphNames, ascending, allowPseudoUnicode):
        baseToGlyphNames = {None:[]}
        for glyphName in glyphNames:
            if allowPseudoUnicode:
                value = self.pseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.unicodeForGlyphName(glyphName)
            if value is None:
                base = None
            else:
                base = unicodeTools.decompositionBase(value)
                base = self.glyphNameForUnicode(base)
                # try to add the glyph names suffix to the base.
                # this will handle mapping aacute.alt to a.alt
                # instead of aacute.alt to a.
                if base is not None:
                    if "." in glyphName and not glyphName.startswith("."):
                        suffix = glyphName.split(".")[1]
                        if base + "." + suffix in self.getParent():
                            base = base + "." + suffix
            if base not in baseToGlyphNames:
                baseToGlyphNames[base] = []
            baseToGlyphNames[base].append(glyphName)
        # get the list of lgyphs with no base.
        noBase = baseToGlyphNames.pop(None)
        # find all bases that are not in the overall glyph names list
        missingBase = []
        for base in sorted(baseToGlyphNames):
            if base is None:
                continue
            if base not in noBase:
                missingBase.append(base)
        # work through the found bases
        processedBases = set()
        sortedResult = []
        for base in noBase:
            if base in processedBases:
                continue
            processedBases.add(base)
            # the base could be in the list more than once.
            # if so, add the proper number of instances of the base.
            count = noBase.count(base)
            r = [base for i in xrange(count)]
            # add the referencing glyphs
            r += baseToGlyphNames.get(base, [])
            sortedResult.append(r)
        # work through the missing bases
        for base in sorted(missingBase):
            sortedResult.append(baseToGlyphNames[base])
        # reverse if necessary
        if not ascending:
            sortedResult = list(reversed(sortedResult))
        return sortedResult


# -----
# Tools
# -----

# PUA lookups

_privateUse1Min = int("E000", 16)
_privateUse1Max = int("F8FF", 16)
_privateUse2Min = int("F0000", 16)
_privateUse2Max = int("FFFFD", 16)
_privateUse3Min = int("100000", 16)
_privateUse3Max = int("10FFFD", 16)
_viablePUACount = (_privateUse1Max - _privateUse1Min) + (_privateUse2Max - _privateUse2Min) + (_privateUse3Max - _privateUse3Min)

def _findAvailablePUACode(existing, code=None):
    assert len(existing) < _viablePUACount

    if code is None:
        code = _privateUse1Min
    else:
        code += 1

    # force the code into a viable position. this will prevent
    # iteration over values that are not in PUA.
    if code > _privateUse1Max and code < _privateUse2Min:
        code = _privateUse2Min
    elif code > _privateUse2Max and code < _privateUse3Min:
        code = _privateUse3Min
    elif code > _privateUse3Max:
        code = _privateUse1Min

    if code >= _privateUse1Min and code <= _privateUse1Max:
        if code not in existing:
            return code
        else:
            return _findAvailablePUACode(existing, code)
    elif code >= _privateUse2Min and code <= _privateUse2Max:
        if code not in existing:
            return code
        else:
            return _findAvailablePUACode(existing, code)
    else:
        if code < _privateUse3Min or code > _privateUse3Max:
            code = _privateUse3Min
        if code not in existing:
            return code
        else:
            return _findAvailablePUACode(existing, code)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
