from src.objects.LLEntry_obj import LLEntry


class LLEntryInvertedIndex:
    def __init__(self):
        self.index = {}
    def addEntry(self, key:str, entry: LLEntry):
        if key not in self.index.keys():
            self.index[key] = []
        self.index[key].append(entry)

    def getEntries(self, key):
        if key in self.index.keys():
            return self.index[key]
        else:
            return None
    def __str__(self):
        return self.index.__str__()