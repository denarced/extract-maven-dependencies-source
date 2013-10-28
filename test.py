#!/usr/bin/env python

import ctagmvn
import filesystem
import os
import pom
import tempfile
import unittest


def surroundWithPomXmlDeclarationAndProject(xml):
    ns = "http://maven.apache.org/POM/4.0.0"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    location = ("http://maven.apache.org/POM/4.0.0 "
                "http://maven.apache.org/xsd/maven-4.0.0.xsd")
    strFormat = """<?xml version="1.0"?>
        <project xmlns="{ns}" xmlns:xsi="{xsi}" xsi:schemaLocation="{loc}">
        """
    declaration = strFormat.format(
        ns=ns,
        xsi=xsi,
        loc=location)
    return declaration + xml + """
        </project>"""


class GetFileReadTest(unittest.TestCase):
    """ Test ctagmvn.getFile. """
    def setUp(self):
        self.tempFile = tempfile.NamedTemporaryFile()
        self.fileContent = "something is written here"
        self.tempFile.write(self.fileContent)
        self.tempFile.flush()

    def tearDown(self):
        self.tempFile.close()

    def testFileContentReading(self):
        content = ctagmvn.getFile(self.tempFile.name)
        self.assertEqual(
            self.fileContent,  # expected
            content)  # actual


class GetFileExistenceTest(unittest.TestCase):
    def testExceptionIsRaisedForNonExistentFile(self):
        filepath = "/tmp/thiscannotexistsorthistestismeaningless"
        assert not os.path.exists(filepath)
        self.assertRaises(ctagmvn.FileNotFoundError, ctagmvn.getFile, filepath)


class JarDependenciesTest(unittest.TestCase):
    def setUp(self):
        self.jarDependencies = ctagmvn.JarDependencies()
        self.filesystem = filesystem.Fake()
        self.jarDependencies.setFilesystem(self.filesystem)

    def testExceptionOnNonExistentM2(self):
        self.assertRaises(
            ctagmvn.FileNotFoundError,
            self.jarDependencies.deriveSourcePaths,
            ["org.springframework:spring-core:3.1.4.RELEASE"],
            None)

    def testHappyPath(self):
        expected = [(
            "/home/denarced/.m2/repository/org/springframework/"
            "spring-core/3.1.4.RELEASE/spring-core-3.1.4.RELEASE-sources.jar")]
        dependencies = ["org.springframework:spring-core:3.1.4.RELEASE"]
        self.filesystem.allPathsExist(True)
        self.assertEqual(
            expected,
            self.jarDependencies.deriveSourcePaths(dependencies, None))


class DependencyListTest(unittest.TestCase):
    def testHappyPath(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("""
            <groupId>com.denarced</groupId>
            <artifactId>tester</artifactId>
            <version>0.0.1</version>
            <modelVersion>4.0.0</modelVersion>
            <dependencies>
                <dependency>
                    <groupId>org.springframework</groupId>
                    <artifactId>spring-webmvc</artifactId>
                    <version>3.1.4.RELEASE</version>
                </dependency>
            </dependencies>""")
        f = tempfile.NamedTemporaryFile()
        f.write(pomContent)
        f.flush()
        depList = pom.DependencyList(f.name)
        depList.run()
        f.close()
        self.assertTrue(len(depList.getList()) > 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
