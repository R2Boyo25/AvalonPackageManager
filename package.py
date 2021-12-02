import requests, json

class Package:
    def __init__(self, jsonobj):
        if type(jsonobj) == str:
            jsonobj = json.loads(jsonobj)

        self.jsonrepr = jsonobj
        self.owner, self.name = jsonobj['full_name'].split('/')
        self.url = jsonobj['html_url']
        self.apiurl = jsonobj['url']

    def __getitem__(self, name):
        try:
            return self.__getAttr__()[name]
        except:
            return None
    
    def __getAttr__(self):
        attrs = {}
        attrs['owner'] = self.owner
        attrs['name'] = self.name
        attrs['url'] = self.url

        return attrs
    
    def __iter__(self):
        return iter([(i, self.__getAttr__()[i]) for i in self.__getAttr__()])

    def __next__(self):
        if not hasattr(self, 'curiter'):
            self.curiter = 0
        
        curkey = self.__iter__()[self.curiter]
        self.curiter += 1
        return curkey, self.__getAttr__()[curkey]

class NPackage:
    def __init__(self, d):
        self.idict = d
    
    def __getitem__(self, item):
        try:
            return self.idict[item]
        except:
            return None
    
    def __setitem__(self, item, value):
        self.idict[item] = value
    
    def keys(self):
        return self.idict.keys()

    def __str__(self):
        return str(self.idict)