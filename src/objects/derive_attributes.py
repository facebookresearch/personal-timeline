from src.objects.LLEntry_obj import LLEntry


# DeriveConfigNode Example:
# {
#     "attribute": "rawImageFilename",
#     "depends_on": ["imageURL"],
#     "function": "fetchImageFromURL"
# }
class DependencyNode:
    def __init__(self, attribute: str, depends_on: list, functionName: str):
        self.attribute = attribute
        self.depends_on = depends_on
        self.function = functionName

    def __str__(self):
        return "\"" + self.attribute + "\" depends_on " + self.depends_on.__str__() + " using \"" + self.function + "\""

# Represents a list of fields and how they can be derived
class AttributeFiller:
    def __init__(self):
        self.dependencies = {
            "rawImageFilename": DependencyNode("rawImageFilename", ["imageURL"], "fetchImageFromURL"),
            "imageFileName": DependencyNode("imageFileName", ["rawImageFilename"], "convertImage"),
            "startTime": DependencyNode("startTime", ["endTime", "playDuration", "durationUnit"], "calculateStartTime"),
            "endTime": DependencyNode("endTime", ["startTime", "playDuration", "durationUnit"], "calculateEndTime"),
            "playDuration":  DependencyNode("playDuration", ["startTime", "endTime"], "calculatePlayDurationMs")
    }

    def fillMissingAttributes(self, lifeLog:LLEntry):
        lifeLog.longitude = 100
        for key in self.dependencies:
            current:DependencyNode = self.dependencies[key]
            self.fillRecursive(lifeLog, current, [])


    def fillRecursive(self, lifelog:LLEntry, dependency:DependencyNode, seen_so_far:list=None):
        print("Filling:", dependency.__str__(), "Seen so far:", seen_so_far.__str__())
        to_be_derived = dependency.attribute
        if to_be_derived in seen_so_far:
            print("Missing data chain. Can't derive", to_be_derived, "Chain:", seen_so_far.__str__())
            return
        seen_so_far.append(to_be_derived)
        tbd_value = lifelog.__getattribute__(to_be_derived)
        print(to_be_derived, "tbd_val:", tbd_value)
        if self.isAbsent(tbd_value):
            parent_attributes = dependency.depends_on
            found_parents:int = 0
            func = dependency.function
            params = []
            for sp in parent_attributes:
                parent_val = lifelog.__getattribute__(sp)
                print(sp, "depends_val:", parent_val)
                if not self.isAbsent(parent_val):
                    print("parent val found:", sp)
                    found_parents+=1
                    params.append(str(parent_val))
                    #Make call to function using parent vals and assign to derive field
                    # lifelog.__setattribute__(to_be_derived, eval(function)
                else:
                    print("Not found:", sp)
            if found_parents == len(parent_attributes):
                func = func + "(\"" +"\",\"".join(params) + "\")"
                print("evaluating:", func)
            else:
                    #See if we can fill parent first
                    print("Looking for parent")
        else:
            print("Value is present")


    def isAbsent(self, val):
        x = (val is None or (isinstance(val, str) and val == ""))
        print(val, "is absent:",x)
        return x

fil = AttributeFiller()
entry = LLEntry("photo","2022-01-05T01:04:42","Google Photos")
fil.fillMissingAttributes(entry)
print(entry.toJson())

