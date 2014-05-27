"""
# Copyright 2004,2009 Toby Dickenson
# Changes 2014 (c) Bjorn Pettersen
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import sys
import modulefinder
from collections import defaultdict

# i = 0

# we're not interested in imports of std python packages.
PYLIB_PATH = {
    # in virtualenvs that see the system libs, these will be different.
    os.path.split(os.path.split(modulefinder.__file__)[0])[0].lower(),
    os.path.split(os.__file__)[0].lower()
}

#print "PYLIBPATH:", PYLIB_PATH

class MyModuleFinder(modulefinder.ModuleFinder):
    def __init__(self, *args, **kwargs):
        self.include_pylib_all = False      # include all of python std lib (incl. C modules)
        self.include_pylib = False          # include python std lib modules.
        self._depgraph = defaultdict(dict)
        self._types = {}
        self._last_caller = None
        modulefinder.ModuleFinder.__init__(self, *args, **kwargs)

    def import_hook(self, name, caller=None, fromlist=None, level=None):
        old_last_caller = self._last_caller
        try:
            self._last_caller = caller
            return modulefinder.ModuleFinder.import_hook(self,name,caller,fromlist)
        finally:
            self._last_caller = old_last_caller
            
    def import_module(self, partnam, fqname, parent):
        # global i
        r = modulefinder.ModuleFinder.import_module(self, partnam, fqname, parent)
        if r is not None and self._last_caller is not None:
            # print "R:", r, dir(r)
            # print "path:", r.__file__
            # i += 1
            # if i > 50:
            #     sys.exit()
            # self._depgraph[self._last_caller.__name__][r.__name__] = 1
            if r.__file__ or self.include_pylib_all:
                rpath = os.path.split(r.__file__)[0].lower()
                pylib_p = [rpath.startswith(pp) for pp in PYLIB_PATH]
                # if rpath not in PYLIB_PATH or self.include_pylib:
                if not any(pylib_p) or self.include_pylib:
                    self._depgraph[self._last_caller.__name__][r.__name__] = r.__file__
        return r
    
    def load_module(self, fqname, fp, pathname, (suffix, mode, type)):
        r = modulefinder.ModuleFinder.load_module(self, fqname, fp, pathname, (suffix, mode, type))
        if r is not None:
            self._types[r.__name__] = type
        return r


class DepGraph(object):
    def __init__(self, fname):
        path = sys.path[:]
        debug = 0
        exclude = []
        mf = MyModuleFinder(path, debug, exclude)
        mf.run_script(fname)
        self.depgraph = mf._depgraph
        self.types = mf._types


if __name__ == '__main__':
    import json
    _fname = sys.argv[1]
    _graph = DepGraph(_fname)
    sys.stdout.write(
        json.dumps(_graph.__dict__, indent=4)
    )
