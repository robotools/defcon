import unicodedata
from defcon.tools import unicodeTools
from defcon.objects.base import BaseDictObject


class CMAP(BaseDictObject):

    def __init__(self):
        super(CMAP, self).__init__()

        # self._dict = unicode to glyph names
        self._glyphNameToUnicode = {}
        self._glyphNameToPseudoUnicode = {}
        self._glyphNameToForcedUnicode = {}
        self._forcedUnicodeToGlyphName = {}

    # -------
    # Loaders
    # -------

    def _loadGlyphNameToUnicode(self):
        for uniValue, glyphList in self.items():
            for glyphName in glyphList:
                self._glyphNameToUnicode[glyphName] = uniValue

    def _loadPseudoUnicodeValue(self, glyphName):
        # already loaded
        if glyphName in self._glyphNameToPseudoUnicode:
            return
        # load the glyph to unicode map
        if not self._glyphNameToUnicode:
            self._loadGlyphNameToUnicode()
        # glyph has a real unicode
        if glyphName in self._glyphNameToUnicode:
            return
        # glyph doesn't have a suffix
        skip = False
        if glyphName.startswith(".") or glyphName.startswith("_"):
            skip = True
        if "." not in glyphName and "_" not in glyphName:
            skip = True
        if skip:
            self._glyphNameToPseudoUnicode[glyphName] = None
            return
        # get the base
        if "." in glyphName:
            base = glyphName.split(".")[0]
        # in the case of ligatures, grab the first glyph
        elif "_" in glyphName:
            base = glyphName.split("_")[0]
        # in the case of ligatures with a suffix, decompose even further.
        if "_" in base:
            base = base.split("_")[0]
        # base doesn't have a value
        if base not in self._glyphNameToUnicode:
            value = None
        # base does have a value
        else:
            value = self._glyphNameToUnicode[base]
        self._glyphNameToPseudoUnicode[glyphName] = value

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
        # load the glyph to unicode map
        if not self._glyphNameToUnicode:
            self._loadGlyphNameToUnicode()
        # glyph has a real unicode
        if glyphName in self._glyphNameToUnicode:
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

    def getUnicodeForGlyphName(self, glyphName):
        if not self._glyphNameToUnicode:
            self._loadGlyphNameToUnicode()
        return self._glyphNameToUnicode.get(glyphName)

    def getGlyphNameForUnicode(self, value):
        glyphList = self.get(value)
        if not glyphList:
            return None
        return glyphList[0]

    def getPseudoUnicodeForGlyphName(self, glyphName):
        realValue = self.getUnicodeForGlyphName(glyphName)
        if realValue is not None:
            return realValue
        if glyphName not in self._glyphNameToPseudoUnicode:
            self._loadPseudoUnicodeValue(glyphName)
        return self._glyphNameToPseudoUnicode[glyphName]

    def getForcedUnicodeForGlyphName(self, glyphName):
        realValue = self.getUnicodeForGlyphName(glyphName)
        if realValue is not None:
            return realValue
        if glyphName not in self._glyphNameToForcedUnicode:
            self._loadForcedUnicodeValue(glyphName)
        return self._glyphNameToForcedUnicode[glyphName]

    def getGlyphNameForForcedUnicode(self, value):
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
            uniValue = self.getPseudoUnicodeForGlyphName(glyphName)
        else:
            uniValue = self.getUnicodeForGlyphName(glyphName)
        if uniValue is None:
            return
        if uniValue is not None:
            decomposition = recursiveDecomposition(uniValue)
            if decomposition != -1:
                if decomposition in font.cmap:
                    baseGlyphName = font.cmap[decomposition][0]
                    if "." in glyphName:
                        suffix = glyphName.split(".", 1)[1]
                        baseWithSuffix = baseGlyphName + "." + suffix
                        if baseWithSuffix in font:
                            baseGlyphName = baseWithSuffix
                    return baseGlyphName
        return glyphName

    # -------
    # Sorting
    # -------

    def sortGlyphNames(self, glyphNames, sortDescriptors=[dict(type="alphabetical")]):
        """
        Sort Descriptor
        type = The type of sort to perform. See below for options.
        ascending - Boolean epresenting if the glyphs should be
            in ascending or descending order. The default is True.
        allowPseudoUnicode - Boolean representing if pseudo Unicode
            values are used. If not, real Unicode values will be used
            if necessary. The default is False.

        Sort types:
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
                value = self.getPseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.getUnicodeForGlyphName(glyphName)
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
                value = self.getPseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.getUnicodeForGlyphName(glyphName)
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
                value = self.getPseudoUnicodeForGlyphName(glyphName)
            else:
                value = self.getUnicodeForGlyphName(glyphName)
            if value is None:
                base = None
            else:
                base = unicodeTools.decompositionBase(value)
                base = self.getGlyphNameForUnicode(base)
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

