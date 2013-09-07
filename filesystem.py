#!/usr/bin/env python

import os

class Real(object):
    def exists(self, path):
        return os.path.exists(path)

class Fake(object):
    def __init__(self):
        self._paths = {}
        self._allPathsExist = False

    def addExistingPath(self, path):
        self._paths[path] = 0

    def allPathsExist(self, allExist):
        self._allPathsExist = allExist

    def exists(self, path):
        if self._allPathsExist:
            return True
        return self._paths.has_key(path)
