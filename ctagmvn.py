#!/usr/bin/env python

import argparse
import filesystem
import os
import pom
import shutil
import threading
import zipfile


class FileNotFoundError(Exception):
    def __init__(self, filename):
        self.filename = filename


def getFile(filename):
    """ Read and return text file contents.

    Parameters:
    filename    absolute or relative filename.

    Return file contents as string or throw FileNotFoundError if file does not
    exist.

    """
    try:
        f = open(filename)
    except IOError:
        raise FileNotFoundError(filename)
    contents = ""
    for line in f.readlines():
        contents += line.strip()
    return contents


def fetchDependencies(pomPath):
    dependencyList = pom.DependencyList(pomPath)
    sourceFetch = pom.SourceFetch(pomPath)
    fetchers = [dependencyList, sourceFetch]
    running = []
    for each in fetchers:
        thread = threading.Thread(target=each.run)
        running.append(thread)
        thread.start()
    for each in running:
        each.join()
    return dependencyList.getList()


def fullJarDirectoryPath(repository, dependency):
    """ Return full path to the dependency directory.

    Parameters:
    repository      Path to the maven repository directory under .m2
                    directory. Must exist.
    dependency      Maven dependency in the form group:artifact:version.

    """
    fullJarPath = repository
    count = 0
    for token in dependency.split(":"):
        if count < 2:
            fullJarPath = os.path.join(
                fullJarPath,
                *token.split("."))
        # Don't split the last token, it's the version
        else:
            fullJarPath = os.path.join(
                fullJarPath,
                token)
        count += 1
    return fullJarPath


def sourceJarFilename(dependency):
    """ Return the source jar's filename.

    Parameters:
    dependency      Maven dependency in the form group:artifact:version.

    """
    pieces = dependency.split(":")
    return "-".join([pieces[1], pieces[2], "sources.jar"])


class JarDependencies(object):
    def __init__(self):
        self._filesystem = None

    def deriveSourcePaths(self, dependencies, m2directory):
        """ Find dependencies' source code jars.

        Parameters:
        dependencies   list of maven dependencies in form
                       groupId:artifactId:version.
        m2directory    absolute path to maven's .m2 directory. If None, default
                       location is used.

        Return list of source jar paths, the ones that existed.

        """
        if not m2directory:
            m2directory = os.path.join(os.path.expanduser("~"), ".m2")
        repository = os.path.join(m2directory, "repository")
        if not self._filesystem.exists(repository):
            message = (
                "Can't get dependency source jars."
                " No such path: {0}".format(repository))
            raise FileNotFoundError(message)

        jarPaths = []
        for each in dependencies:
            dependencyDirectory = fullJarDirectoryPath(repository, each)
            filename = sourceJarFilename(each)
            fullFilePath = os.path.join(dependencyDirectory, filename)
            if self._filesystem.exists(fullFilePath):
                jarPaths.append(fullFilePath)

        return jarPaths

    def setFilesystem(self, filesystem):
        self._filesystem = filesystem


def copySourceJars(sourceJarPaths, destination):
    """ Copy source code jars to destination. """
    for jarPath in sourceJarPaths:
        shutil.copy(jarPath, destination)


def stripPath(pathList):
    """ Remove paths from pathList, return list of filenames. """
    return [os.path.basename(x) for x in pathList]


def checkZipForIllegalMembers(zipf, filename):
    """ Raise error if zipf contains members that start with / or contain ..
    """
    for member in zipf.namelist():
        if ".." in member:
            raise ValueError("Zip that contained '..': " + filename)
        if member.startswith("/"):
            raise ValueError(
                "Zip member ({0}) starts with '/' in file: {1}".format(
                    member,
                    filename))


def extractSources(directory, filenames):
    """ Extract files in the directory to the directory.

    Parameters:
    directory    in which the files (filenames) are located and into which the
                 jar file contents are extracted to.
    filenames    of the jar files to be extracted.

    """
    for fname in filenames:
        absolute = os.path.join(directory, fname)
        zipf = zipfile.ZipFile(absolute, "r")
        checkZipForIllegalMembers(zipf, fname)
        zipf.extractall(directory)


def main(pomPath, config):
    """ Copy and extract pom dependency sources.

    Parameters:
    pomPath  absolute path to the pom.xml file.
    config   dictionary of configuration options.

    """
    dependencies = fetchDependencies(pomPath)
    jarDeps = JarDependencies()
    jarDeps.setFilesystem(filesystem.Real())
    if "m2path" in config:
        sourceJarFilepaths = jarDeps.deriveSourcePaths(
            dependencies,
            config["m2path"])
    else:
        sourceJarFilepaths = jarDeps.deriveSourcePaths(dependencies, None)
    copySourceJars(sourceJarFilepaths, config["destination"])
    extractSources(config["destination"], stripPath(sourceJarFilepaths))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "destination",
        help="Directory into which source code is extracted to")
    parser.add_argument(
        "pom",
        help="Path to the pom.xml file from which dependencies are analyzed")
    parser.add_argument(
        "-m",
        "--m2-directory",
        help=("Path to the maven .m2 directory. " +
              "The default is used if this isn't defined"))
    args = parser.parse_args()
    config = {
        "destination": args.destination
    }
    if args.m2_directory:
        config["m2path"] = args.m2_directory
    try:
        main(args.pom, config)
    except FileNotFoundError as e:
        print "File not found:", e.filename
