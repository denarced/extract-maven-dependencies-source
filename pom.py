#!/usr/bin/env python

import re
import subprocess

def extractDependenciesFromMvnOutput(output):
    deps = []
    for line in output.splitlines():
        line = line.strip()
        if (line.endswith(":compile") or
            line.endswith(":runtime") or
            line.endswith(":test") or
            line.endswith(":provided")):

            m = re.match(""".*[ ]{2,}(.*)""", line)
            if m:
                deps.append(m.group(1))
    return deps

class DependencyList(object):
    def __init__(self, pomPath):
        self._pomPath = pomPath
        self._list = []

    def run(self):
        p = subprocess.Popen(
            ["mvn", "-f", self._pomPath, "dependency:list"], 
            stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        self._list = self._extractDependencyList(stdout)

    def getList(self):
        return self._list

    def _extractDependencyList(self, mvnOutput):
        deps = extractDependenciesFromMvnOutput(mvnOutput)
        # remove extra from strings, form: group, artifact, type, version, something
        stripped = []
        for each in deps:
            pieces = each.split(":")
            stripped.append(":".join([
                pieces[0],
                pieces[1],
                pieces[3]]))
        return stripped

class SourceFetch(object):
    def __init__(self, pomPath):
        self._pomPath = pomPath

    def run(self):
        p = subprocess.Popen(
            ["mvn", "-f", self._pomPath, "dependency:sources"],
            stdout=subprocess.PIPE)
        p.communicate()

