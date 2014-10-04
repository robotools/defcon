import unicodedata
from fontTools.agl import AGL2UV
from defcon.tools import unicodeTools
from defcon.objects.base import BaseDictObject


class UnicodeData(BaseDictObject):

    """
    This object serves Unicode data for the font.

    **This object posts the following notifications:**

    ===================  ====
    Name                 Note
    ===================  ====
    UnicodeData.Changed  Posted when the *dirty* attribute is set.
    ===================  ====

    This object behaves like a dict. The keys are Unicode values and the
    values are lists of glyph names associated with that unicode value::

        {
            65 : ["A"],
            66 : ["B"],
        }

    To get the list o glyph names associated with a particular Unicode
    value, do this::

        glyphList = unicodeData[65]

    The object defines many more convenient ways of interacting
    with this data.

    .. warning::

        Setting data into this object manually is *highly* discouraged.
        The object automatically keeps itself in sync with the font and the
        glyphs contained in the font. No manual intervention is required.
    """

    changeNotificationName = "UnicodeData.Changed"

    def __init__(self):
        super(UnicodeData, self).__init__()
        self._glyphNameToForcedUnicode = {}
        self._forcedUnicodeToGlyphName = {}

    # -----------
    # set and get
    # -----------

    def removeGlyphData(self, glyphName, values):
        """
        Remove the data for the glyph with **glyphName** and
        the Unicode values **values**.

        This should never be called directly.
        """
        for value in values:
            if value not in self._dict:
                continue
            glyphList = self._dict[value]
            if glyphName in glyphList:
                glyphList.remove(glyphName)
            if not glyphList:
                del self._dict[value]
        # remove the forced reference to the glyph
        if glyphName in self._glyphNameToForcedUnicode:
            fourcedValue = self._glyphNameToForcedUnicode[glyphName]
            del self._glyphNameToForcedUnicode[glyphName]
            del self._forcedUnicodeToGlyphName[fourcedValue]
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

    def addGlyphData(self, glyphName, values):
        """
        Add the data for the glyph with **glyphName** and
        the Unicode values **values**.

        This should never be called directly.
        """
        for value in values:
            # update unicode to glyph name
            glyphList = self._dict.get(value)
            if glyphList is None:
                glyphList = []
            if glyphName not in glyphList:
                glyphList.append(glyphName)
            self._dict[value] = glyphList
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

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
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

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
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

    def clear(self):
        """
        Completely remove all stored data.

        This should never be called directly.
        """
        self._dict.clear()
        self._forcedUnicodeToGlyphName.clear()
        self._glyphNameToForcedUnicode.clear()

    def update(self, other):
        """
        Update the data int this object with the data from **other**.

        This should never be called directly.
        """
        for value, glyphList in list(other.items()):
            for glyphName in glyphList:
                if glyphName in self._glyphNameToForcedUnicode:
                    forcedValue = self._glyphNameToForcedUnicode[glyphName]
                    del self._forcedUnicodeToGlyphName[forcedValue]
                    del self._glyphNameToForcedUnicode[glyphName]
            self._dict[value] = list(glyphList)
        if self.dispatcher is not None:
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

    # -------
    # Loaders
    # -------

    def _setupForcedValueDict(self):
        for value, glyphList in list(self.values()):
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
        startPoint = max(list(self._forcedUnicodeToGlyphName.keys()) + [_privateUse1Min])
        # find the value and store it
        value = _findAvailablePUACode(self._forcedUnicodeToGlyphName)
        self._forcedUnicodeToGlyphName[value] = glyphName
        self._glyphNameToForcedUnicode[glyphName] = value

    # ---------------
    # Value Retrieval
    # ---------------

    def unicodeForGlyphName(self, glyphName):
        """
        Get the Unicode value for **glyphName**. Returns *None*
        if no value is found.
        """
        font = self.getParent()
        if glyphName not in font:
            return None
        glyph = font[glyphName]
        unicodes = glyph.unicodes
        if not unicodes:
            return None
        return unicodes[0]

    def glyphNameForUnicode(self, value):
        """
        Get the first glyph assigned to the Unicode specified
        as **value**. This will return *None* if no glyph is found.
        """
        glyphList = self.get(value)
        if not glyphList:
            return None
        return glyphList[0]

    def pseudoUnicodeForGlyphName(self, glyphName):
        """
        Get the pseudo-Unicode value for **glyphName**.
        This will return *None* if nothing is found.
        """
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
        base = base.split("_")[0]
        # get the value for the base
        return self.unicodeForGlyphName(base)

    def forcedUnicodeForGlyphName(self, glyphName):
        """
        Get the forced-Unicode value for **glyphName**.
        """
        realValue = self.unicodeForGlyphName(glyphName)
        if realValue is not None:
            return realValue
        if glyphName not in self._glyphNameToForcedUnicode:
            self._loadForcedUnicodeValue(glyphName)
        return self._glyphNameToForcedUnicode[glyphName]

    def glyphNameForForcedUnicode(self, value):
        """
        Get the glyph name assigned to the forced-Unicode
        specified by **value**.
        """
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

    # ---------------------
    # Description Retrieval
    # ---------------------

    def scriptForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the script for **glyphName**. If **allowPseudoUnicode** is
        True, a pseudo-Unicode value will be used if needed. This will
        return *None* if nothing can be found.
        """
        if allowPseudoUnicode:
            value = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            value = self.unicodeForGlyphName(glyphName)
        if value is None:
            return "Unknown"
        return unicodeTools.script(value)

    def blockForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the block for **glyphName**. If **allowPseudoUnicode** is
        True, a pseudo-Unicode value will be used if needed. This will
        return *None* if nothing can be found.
        """
        if allowPseudoUnicode:
            value = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            value = self.unicodeForGlyphName(glyphName)
        if value is None:
            return "No_Block"
        return unicodeTools.block(value)

    def categoryForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the category for **glyphName**. If **allowPseudoUnicode** is
        True, a pseudo-Unicode value will be used if needed. This will
        return *None* if nothing can be found.
        """
        if allowPseudoUnicode:
            value = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            value = self.unicodeForGlyphName(glyphName)
        if value is None:
            return "Cn"
        return unicodeTools.category(value)

    def decompositionBaseForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the decomposition base for **glyphName**. If **allowPseudoUnicode**
        is True, a pseudo-Unicode value will be used if needed. This will
        return *glyphName* if nothing can be found.
        """
        if allowPseudoUnicode:
            uniValue = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            uniValue = self.unicodeForGlyphName(glyphName)
        if uniValue is None:
            return glyphName
        if uniValue is not None:
            font = self.getParent()
            decomposition = unicodeTools.decompositionBase(uniValue)
            if decomposition != -1:
                if decomposition in font.unicodeData:
                    baseGlyphName = font.unicodeData[decomposition][0]
                    if "." in glyphName:
                        suffix = glyphName.split(".", 1)[1]
                        baseWithSuffix = baseGlyphName + "." + suffix
                        if baseWithSuffix in font:
                            baseGlyphName = baseWithSuffix
                    return baseGlyphName
        return glyphName

    def closeRelativeForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the close relative for **glyphName**. For example, if you
        request the close relative of the glyph name for the character (,
        you will be given the glyph name for the character ) if it exists
        in the font. If **allowPseudoUnicode** is True, a pseudo-Unicode
        value will be used if needed. This will return *None* if nothing
        can be found.
        """
        return self._openCloseSearch(glyphName, allowPseudoUnicode, unicodeTools.closeRelative)

    def openRelativeForGlyphName(self, glyphName, allowPseudoUnicode=True):
        """
        Get the open relative for **glyphName**. For example, if you
        request the open relative of the glyph name for the character ),
        you will be given the glyph name for the character ( if it exists
        in the font. If **allowPseudoUnicode** is True, a pseudo-Unicode
        value will be used if needed. This will return *None* if nothing
        can be found.
        """
        return self._openCloseSearch(glyphName, allowPseudoUnicode, unicodeTools.openRelative)

    def _openCloseSearch(self, glyphName, allowPseudoUnicode, lookup):
        if allowPseudoUnicode:
            uniValue = self.pseudoUnicodeForGlyphName(glyphName)
        else:
            uniValue = self.unicodeForGlyphName(glyphName)
        if uniValue is None:
            return
        relativeValue = lookup(uniValue)
        # no defined relative value. return.
        if relativeValue is None:
            return
        # look for a hit on the unicode value.
        # if none exists, return.
        preciseMatch = self.glyphNameForUnicode(relativeValue)
        if preciseMatch is None:
            return
        # pseudo unicode is not allowed. use precise match.
        if not allowPseudoUnicode:
            return preciseMatch
        # add the suffix from the provided glyph name to the
        # recise match and test for existence. if it does
        # exist, return it. otherwise fallback to the
        # precise match.
        if "." in glyphName:
            suffix = glyphName.split(".", 1)[1]
            pseudoMatch = preciseMatch + "." + suffix
            if pseudoMatch in self.getParent():
                return pseudoMatch
        return preciseMatch

    # -------
    # Sorting
    # -------

    def sortGlyphNames(self, glyphNames, sortDescriptors=[dict(type="unicode")]):
        """
        This sorts the list of **glyphNames** following the sort descriptors
        provided in the **sortDescriptors** list. Ths works by iterating over
        the sort descriptors and subdividing. For example, if the first
        sort descriptor is a suffix type, internally, the result of the
        sort will look something like this::

            [
                [glyphsWithNoSuffix],
                [glyphsWith.suffix1],
                [glyphsWith.suffix2]
            ]

        When the second sort descriptor is processed, the results of previous
        sorts are subdivided even further. For example, if the second
        sort type is script::

            [[
                [glyphsWithNoSuffix, script1], [glyphsWithNoSuffix, script2],
                [glyphsWith.suffix1, script1], [glyphsWith.suffix1, script2],
                [glyphsWith.suffix2, script1], [glyphsWith.suffix2, script2]
            ]]

        And so on. The returned list will be flattened into a list of glyph names.

        Each item in **sortDescriptors** should be a dict of the following form:

        ==================  ===========
        Key                 Description
        ==================  ===========
        type                The type of sort to perform. See below for options.
        ascending           Boolean representing if the glyphs should be in
                            ascending or descending order. Optional. The default is True.
        allowPseudoUnicode  Boolean representing if pseudo-Unicode
                            values are used. If not, real Unicode values will be used
                            if necessary. Optional. The default is False.
        function            A function. Used only for **custom** sort types. See details below.
        ==================  ===========

        *Available Sort Types:*

        There are four types of sort types: simple, complex, canned and custom.
        Simple sorts are based on sorting non-magical values, such as Unicode values.
        Complex sorts are heuristic based sorts based on common glyph name practices,
        aesthetic preferences and other hard to quantify ideas. Custom sorts are just
        that, custom sorts. Canned sorts are combinations of simple, complex and custom
        sorts that give optimized ordering results. Complex and canned sorts may change
        with further updates, so they should not be relied on for persistent ordering.

        =================   ===========
        Simple Sort Types   Description
        =================   ===========
        alphabetical        Self-explanitory.
        unicode             Sort based on Unicode value.
        script              Sort based on Unicode script.
        category            Sort based on Unicode category.
        block               Sort based on Unicode block.
        suffix              Sort based on glyph name suffix.
        decompositionBase   Sort based on the base glyph defined in the decomposition rules.
        =================   ===========

        ==================  ===========
        Complex Sort Types  Description
        ==================  ===========
        weightedSuffix      Sort based on glyph names suffix. The ordering of the
                            suffixes is based on the calculated "weight" of the suffix.
                            This value is calculated by noting what type of glyphs have
                            the same suffix. The more glyph types, the more important the
                            suffix. Additionally, glyphs with suffixes that have only
                            numerical differences are grouped together. For example,
                            a.alt, a.alt1 and a.alt319 will be grouped together.
        ligature            Sort into to groups: non-ligatures and ligatures.
                            The determination of whether a glyph is a ligature or
                            not is based on the Unicode value, common glyph names
                            or the use of an underscore in the name.
        =================   ===========

        ==================  ===========
        Canned Sort Types   Description
        ==================  ===========
        cannedDesign        Sort glyphs into a design process friendly order.
        =================   ===========

        =================   ===========
        Custom Sort Type    Description
        =================   ===========
        custom              Sort using a custom function. See details below.
        =================   ===========

        *Sorting with a custom function:*
        If the builtin sort types don't do exactly what you need, you can use a **custom** sort type
        that contains an arbitrary function that handles sorting externally. This follows the same
        sorting logic as detailed above. The custom sort type can be used in conjunction with the
        builtin sort types.

        The function should follow this form::

            mySortFunction(font, glyphNames, ascending=True, allowPseudoUnicode=False)

        The **ascending** and **allowPseudoUnicode** arguments will be the values defined
        in the sort descriptors.

        The function should return a list of lists of glyph names.

        An example::

            def sortByE(font, glyphNames, ascending=True, allowsPseudoUnicodes=False):
                startsWithE = []
                doesNotStartWithE = []
                for glyphName in glyphNames:
                    if glyphName.startswith("startsWithE"):
                        startsWithE.append(glyphName)
                    else:
                        doesNotStartWithE.append(glyphName)
                return [startsWithE, doesNotStartWithE]
        """
        blocks = [glyphNames]
        typeToMethod = dict(
            # simple
            alphabetical=self._sortByAlphabet,
            str=self._sortByUnicode,
            category=self._sortByCategory,
            block=self._sortByBlock,
            script=self._sortByScript,
            suffix=self._sortBySuffix,
            decompositionBase=self._sortByDecompositionBase,
            # complex
            weightedSuffix=self._sortByWeightedSuffix,
            ligature=self._sortByLigature,
            # custom
            custom=self._sortByCustomFunction,
            # canned
            cannedDesign=self._cannedSortDesign,
            # private
            _generalType=self._sortByGeneralType,
            _whitespaceCategory=self._sortByWhitespace,
            _containerPartners=self._sortByContainerPartners,
            _manualGroups=self._sortByManualGroups,
            _notdef=self._sortByNotdef,
        )
        for sortDescriptor in sortDescriptors:
            sortType = sortDescriptor["type"]
            ascending = sortDescriptor.get("ascending", True)
            allowPseudoUnicode = sortDescriptor.get("allowPseudoUnicode", False)
            function = sortDescriptor.get("function", None)
            sortMethod = typeToMethod[sortType]

            newBlocks = []
            for block in blocks:
                sortedBlock = self._sortRecurse(blocks, sortMethod, ascending, allowPseudoUnicode, function)
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

    def _sortRecurse(self, blocks, sortMethod, ascending, allowPseudoUnicode, function):
        if not blocks:
            return []
        if not isinstance(list(blocks)[0], str):
            sortedBlocks = []
            for block in blocks:
                block = self._sortRecurse(block, sortMethod, ascending, allowPseudoUnicode, function)
                sortedBlocks.append(block)
            return sortedBlocks
        else:
            if sortMethod == self._sortByCustomFunction:
                return sortMethod(blocks, ascending, allowPseudoUnicode, function)
            else:
                return sortMethod(blocks, ascending, allowPseudoUnicode)

    # simple sorts

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
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, self.scriptForGlyphName, unicodeTools.orderedScripts)

    def _sortByBlock(self, glyphNames, ascending, allowPseudoUnicode):
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, self.blockForGlyphName, unicodeTools.orderedBlocks)

    def _sortByCategory(self, glyphNames, ascending, allowPseudoUnicode):
        return self._sortByUnicodeLookup(glyphNames, ascending, allowPseudoUnicode, self.categoryForGlyphName, unicodeTools.orderedCategories)

    def _sortByUnicodeLookup(self, glyphNames, ascending, allowPseudoUnicode, tagLookup, orderedTags):
        tagToGlyphs = {}
        for glyphName in glyphNames:
            tag = tagLookup(glyphName, allowPseudoUnicode)
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
        # get the list of glyphs with no base.
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
            r = [base for i in range(count)]
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

    # custom sorts

    def _sortByCustomFunction(self, glyphNames, ascending, allowPseudoUnicode, function):
        return function(self.getParent(), glyphNames, ascending, allowPseudoUnicode)

    # complex sorts

    def _sortByWeightedSuffix(self, glyphNames, ascending, allowPseudoUnicode):
        # split into two groups
        noSuffix = []
        suffixed = []
        for glyphName in glyphNames:
            if glyphName.startswith(".") or "." not in glyphName:
                noSuffix.append(glyphName)
            else:
                suffixed.append(glyphName)
        if not suffixed:
            return noSuffix
        # magnetize the suffixes
        allSuffixes = set([glyphName.split(".", 1)[-1] for glyphName in suffixed])
        allSuffixes = list(sorted(allSuffixes))
        magnets = {}
        while allSuffixes:
            toMatch = toMatchOriginal = allSuffixes.pop(0)
            # split off trailing digits
            # this makes .alt1 match .alt2
            stripped = toMatch
            while stripped:
                c = stripped[-1]
                if c.isdigit():
                    stripped = stripped[:-1]
                else:
                    break
            if stripped:
                toMatch = stripped
            # search for suffixes that start with toMatch
            # and have only numerical differences
            matches = []
            for suffix in allSuffixes:
                if suffix.lower().startswith(toMatch.lower()):
                    if len(suffix) == len(toMatch):
                        matches.append(suffix)
                    else:
                        diffLength = len(suffix) - len(toMatch)
                        misMatch = suffix[:-diffLength]
                        allDigits = False not in [c.isdigit() for c in misMatch]
                        if allDigits:
                            matches.append(suffix)
            for suffix in matches:
                allSuffixes.remove(suffix)
            if not matches:
                toMatch = toMatchOriginal
            # store the result
            magnets[toMatch] = [toMatchOriginal] + matches
        # make a flat mapping of suffix : magnet
        suffixToMagnet = {}
        for magnet, suffixes in list(magnets.items()):
            for suffix in suffixes:
                suffixToMagnet[suffix] = magnet
        # gather data about the suffixes
        suffixMap = {}
        for glyphName in suffixed:
            # get the suffix data dict from the map
            suffix = glyphName.split(".", 1)[-1]
            # get the magnet group
            suffix = suffixToMagnet[suffix]
            if suffix not in suffixMap:
                suffixMap[suffix] = dict(glyphNames=[], letter=0, mark=0, number=0, punctuation=0, symbol=0, space=0)
            suffixData = suffixMap[suffix]
            # add the glyph name
            suffixData["glyphNames"].append(glyphName)
            # update the category flags
            category = self.categoryForGlyphName(glyphName, allowPseudoUnicode=allowPseudoUnicode)
            if category in "Lu Ll Lt":
                suffixData["letter"] = True
            elif category in "Lm Mn Mc Me":
                suffixData["mark"] = True
            elif category in "Nd Nl No":
                suffixData["number"] = True
            elif category in "Pc Pd Pe Pf Pi Po Ps":
                suffixData["punctuation"] = True
            elif category in "Sc Sk Sm So":
                suffixData["symbol"] = True
            elif category == "Zs":
                suffixData["space"] = True
        # rank the suffixes
        sorter = []
        for suffix, suffixData in list(suffixMap.items()):
            sortable = (
                suffixData["letter"],
                suffixData["number"],
                suffixData["symbol"],
                suffixData["punctuation"],
                suffixData["mark"],
                suffixData["space"],
                -len(suffixData["glyphNames"]),
                len(suffix),
                suffix,
                suffixData
            )
            sorter.append(sortable)
        suffixSortedGlyphsNames = [item[-1]["glyphNames"] for item in sorted(sorter)]
        if not ascending:
            for i in suffixSortedGlyphsNames:
                i.reverse()
        sortedResult = [noSuffix] + suffixSortedGlyphsNames
        if not ascending:
            sortedResult.reverse()
        return sortedResult

    def _sortByLigature(self, glyphNames, ascending, allowPseudoUnicode):
        notLigature = []
        ligature = []
        for glyphName in glyphNames:
            base = glyphName.split(".")[0]
            if "_" in base and base not in _notReallyLigatures:
                ligature.append(glyphName)
            elif not allowPseudoUnicode and self.unicodeForGlyphName(glyphName) in _ligatureUniValues:
                ligature.append(glyphName)
            elif allowPseudoUnicode and self.pseudoUnicodeForGlyphName(glyphName) in _ligatureUniValues:
                ligature.append(glyphName)
            elif base in ("ff", "fi", "fl", "ffi", "ffl"):
                ligature.append(glyphName)
            else:
                notLigature.append(glyphName)
        final = [notLigature, ligature]
        if not ascending:
            notLigature.reverse()
            ligature.reverse()
            final.reverse()
        return final

    # canned sorts

    def _cannedSortDesign(self, glyphNames, ascending, allowPseudoUnicode):
        sortDescriptors = [
            dict(type="weightedSuffix", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="ligature", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="_generalType", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="_whitespaceCategory", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="alphabetical", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="unicode", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="category", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="script", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="decompositionBase", allowPseudoUnicode=allowPseudoUnicode),
        ]
        glyphNames = self.sortGlyphNames(glyphNames, sortDescriptors)
        sortDescriptors = [
            dict(type="_containerPartners", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="_manualGroups", allowPseudoUnicode=allowPseudoUnicode),
            dict(type="_notdef", allowPseudoUnicode=allowPseudoUnicode),
        ]
        glyphNames = self.sortGlyphNames(glyphNames, sortDescriptors)
        if not ascending:
            glyphNames.reverse()
        return glyphNames

    # private sorts

    def _sortByGeneralType(self, glyphNames, ascending, allowPseudoUnicode):
        noSuffixUnicode = []
        noSuffixNoUnicode = []
        suffix = []
        for glyphName in glyphNames:
            if glyphName.startswith("."):
                noSuffixNoUnicode.append(glyphName)
            elif "." in glyphName:
                suffix.append(glyphName)
            elif self.unicodeForGlyphName(glyphName):
                noSuffixUnicode.append(glyphName)
            else:
                noSuffixNoUnicode.append(glyphName)
        final = [noSuffixUnicode, noSuffixNoUnicode, suffix]
        if not ascending:
            noSuffixUnicode.reverse()
            noSuffixNoUnicode.reverse()
            suffix.reverse()
            final.reverse
        return final

    def _sortByWhitespace(self, glyphNames, ascending, allowPseudoUnicode):
        space = []
        notSpace = []
        for glyphName in glyphNames:
            if self.categoryForGlyphName(glyphName, allowPseudoUnicode=allowPseudoUnicode) == "Zs":
                space.append(glyphName)
            else:
                notSpace.append(glyphName)
        final = [space, notSpace]
        if not ascending:
            space.reverse()
            notSpace.reverse()
            final.reverse()
        return final

    def _sortByContainerPartners(self, glyphNames, ascending, allowPseudoUnicode):
        glyphOrder = []
        while glyphNames:
            glyphName = glyphNames[0]
            glyphOrder.append(glyphName)
            glyphNames = glyphNames[1:]
            # get the close relative
            closeRelative = self.closeRelativeForGlyphName(glyphName, allowPseudoUnicode=allowPseudoUnicode)
            if closeRelative is not None:
                if closeRelative not in glyphOrder:
                    glyphOrder.append(closeRelative)
                if closeRelative in glyphNames:
                    glyphNames.remove(closeRelative)
        if not ascending:
            glyphOrder.reverse()
        return glyphOrder

    def _sortByNotdef(self, glyphNames, ascending, allowPseudoUnicode):
        notDef = []
        notNotDef = []
        for glyphName in glyphNames:
            if glyphName.startswith(".notdef"):
                notDef.append(glyphName)
            else:
                notNotDef.append(glyphName)
        return notNotDef + notDef

    def _sortByManualGroups(self, glyphNames, ascending, allowPseudoUnicode):
        # build a unicode map for all glyphs
        pseudoUnicodeMapping = {}
        for glyphName in glyphNames:
            if allowPseudoUnicode:
                uniValue = self.pseudoUnicodeForGlyphName(glyphName)
            else:
                uniValue = self.unicodeForGlyphName(glyphName)
            if uniValue not in pseudoUnicodeMapping:
                pseudoUnicodeMapping[uniValue] = []
            pseudoUnicodeMapping[uniValue].append(glyphName)
        for pairGroup in _manualSortGroups:
            # find the matching glyphs
            matched = []
            for uniValue in pairGroup:
                matched += pseudoUnicodeMapping.get(uniValue, [])
            # break the matched into suffix groups
            suffixes = {}
            for glyphName in matched:
                if "." not in glyphName:
                    suffix = None
                else:
                    suffix = glyphName.split(".", 1)[-1]
                if suffix not in suffixes:
                    suffixes[suffix] = []
                suffixes[suffix].append(glyphName)
            # wor through the suffixes
            for matched in list(suffixes.values()):
                # remove matched[1:] them after matched[0]
                if len(matched) > 1:
                    for glyphName in matched[1:]:
                        glyphNames.remove(glyphName)
                    insertionPoint = glyphNames.index(matched[0])
                    glyphNames = glyphNames[:insertionPoint + 1] + matched[1:] + glyphNames[insertionPoint + 1:]
        return glyphNames


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

# -----------------
# Sorting Constants
# -----------------

_notReallyLigatures = "space_uni0326".split(" ")
_ligatureUniValues = [int(i, 16) for i in "FB00 FB01 FB02 FB03 FB04 FB05 FB06".split(" ")]

_manualSortGroups = """
percent
perthousand
0x2031

slash
backslash
fraction
bar
brokenbar

period
comma
colon
semicolon
ellipsis
exclam
exclamdown
exclamdbl
question
questiondown

quotesingle
quotedbl
quoteleft
quoteright
quotedblleft
quotedblright
0x201B
0x201F
quotesinglbase
quotedblbase
guilsinglleft
guilsinglright
guillemotleft
guillemotright

at
ampersand
section
paragraph
0x3D7
0x2113
0x2139
0x2116

asterisk
dagger
daggerdbl
0x2042

periodcentered
bullet

acute
grave
hungarumlaut
circumflex
caron
breve
tilde
macron
dieresis
dotaccent
ring
cedilla
ogonek

asciicircum
asciitilde

plus
minus
plusminus
divide
multiply
equal
less
greater
lessequal
greaterequal
approxequal
notequal

copyright
0x24C5 # circle P
registered
trademark
0x2120 # SM

summation
0x00B5

Euro
florin

0x00B9
0x00B2
0x00B3
""".strip()
_currentGroup = []
_parsed = [_currentGroup]
for line in _manualSortGroups.splitlines():
    if "#" in line:
        line = line.split("#")[0].strip()
        assert line
    if not line:
        if _currentGroup:
            _currentGroup = []
            _parsed.append(_currentGroup)
        continue
    if line.startswith("0x"):
        line = int(line[2:], 16)
    else:
        line = AGL2UV[line]
    _currentGroup.append(line)
for g in _parsed:
    assert len(g)
_manualSortGroups = _parsed

# -----
# Tests
# -----

def _testRemoveGlyphData():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("XXX")
    >>> font.unicodeData.addGlyphData("XXX", [65])
    >>> font.unicodeData.removeGlyphData("A", [65])
    >>> font.unicodeData[65]
    ['XXX']
    """

def _testAddGlyphData():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("XXX")
    >>> font.unicodeData.addGlyphData("XXX", [1000])
    >>> font.unicodeData[1000]
    ['XXX']
    >>> font.unicodeData.addGlyphData("XXX", [65])
    >>> font.unicodeData[65]
    ['A', 'XXX']
    """

def _testDelitem():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> del font.unicodeData[65]
    >>> 65 in font.unicodeData
    False
    >>> font.unicodeData.glyphNameForUnicode(65)
    """

def _testSetitem():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("XXX")
    >>> font.unicodeData[1000] = ["XXX"]
    >>> font.unicodeData[1000]
    ['XXX']
    >>> font.unicodeData[65] = ["YYY"]
    >>> font.unicodeData[65]
    ['A', 'YYY']
    """

def _testUnicodeForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.unicodeData.unicodeForGlyphName("A")
    65
    """

def _testGlyphNameForUnicode():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.unicodeData.glyphNameForUnicode(65)
    'A'
    """

def _testPseudoUnicodeForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.unicodeData.pseudoUnicodeForGlyphName("A")
    65
    >>> font.newGlyph("A.foo")
    >>> font.unicodeData.pseudoUnicodeForGlyphName("A.foo")
    65
    >>> font.newGlyph("B_A")
    >>> font.unicodeData.pseudoUnicodeForGlyphName("B_A")
    66
    """

def _testScriptForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("A.alt")
    >>> font.unicodeData.scriptForGlyphName("A")
    'Latin'
    >>> font.unicodeData.scriptForGlyphName("A.alt")
    'Latin'
    >>> font.unicodeData.scriptForGlyphName("A.alt", False)
    'Unknown'
    """

def _testBlockForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("A.alt")
    >>> font.unicodeData.blockForGlyphName("A")
    'Basic Latin'
    >>> font.unicodeData.blockForGlyphName("A.alt")
    'Basic Latin'
    >>> font.unicodeData.blockForGlyphName("A.alt", False)
    'No_Block'
    """

def _testCategoryForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("A.alt")
    >>> font.unicodeData.categoryForGlyphName("A")
    'Lu'
    >>> font.unicodeData.categoryForGlyphName("A.alt")
    'Lu'
    >>> font.unicodeData.categoryForGlyphName("A.alt", False)
    'Cn'
    """

def _testDecompositionBaseForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.newGlyph("Aacute")
    >>> font["Aacute"].unicode = int("00C1", 16)
    >>> font.unicodeData.decompositionBaseForGlyphName("Aacute", True)
    'A'
    >>> font.newGlyph("Aringacute")
    >>> font["Aringacute"].unicode = int("01FA", 16)
    >>> font.unicodeData.decompositionBaseForGlyphName("Aringacute", True)
    'A'
    >>> font.newGlyph("Aacute.alt")
    >>> font.unicodeData.decompositionBaseForGlyphName("Aacute.alt", True)
    'A'
    >>> font.newGlyph("A.alt")
    >>> font.unicodeData.decompositionBaseForGlyphName("Aacute.alt", True)
    'A.alt'
    """

def _testCloseReleativeForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> font = Font()
    >>> font.newGlyph("parenleft")
    >>> font["parenleft"].unicode = int("0028", 16)
    >>> font.newGlyph("parenright")
    >>> font["parenright"].unicode = int("0029", 16)
    >>> font.newGlyph("parenleft.alt")
    >>> font.newGlyph("parenright.alt")
    >>> font.unicodeData.closeRelativeForGlyphName("parenleft", True)
    'parenright'
    >>> font.unicodeData.closeRelativeForGlyphName("parenleft.alt", True)
    'parenright.alt'
    >>> del font["parenright.alt"]
    >>> font.unicodeData.closeRelativeForGlyphName("parenleft.alt", True)
    'parenright'
    """

def _testOpenRelativeForGlyphName():
    """
    >>> from defcon.objects.font import Font
    >>> font = Font()
    >>> font.newGlyph("parenleft")
    >>> font["parenleft"].unicode = int("0028", 16)
    >>> font.newGlyph("parenright")
    >>> font["parenright"].unicode = int("0029", 16)
    >>> font.newGlyph("parenleft.alt")
    >>> font.newGlyph("parenright.alt")
    >>> font.unicodeData.openRelativeForGlyphName("parenright", True)
    'parenleft'
    >>> font.unicodeData.openRelativeForGlyphName("parenright.alt", True)
    'parenleft.alt'
    >>> del font["parenleft.alt"]
    >>> font.unicodeData.openRelativeForGlyphName("parenright.alt", True)
    'parenleft'
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
