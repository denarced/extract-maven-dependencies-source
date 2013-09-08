#!/usr/bin/env python

from lxml import etree
import ctagmvn
import filesystem
import os
import pom
import tempfile
import unittest

def surroundWithPomXmlDeclarationAndProject(xml):
    return """<?xml version="1.0"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
        """ + xml + """
        </project>"""

class GetFileReadTest(unittest.TestCase):
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
            self.fileContent, # expected
            content) # actual

class GetFileExistenceTest(unittest.TestCase):
    def testExceptionIsRaisedForNonExistentFile(self):
        filepath = "/tmp/thiscannotexistsorthistestismeaningless"
        assert not os.path.exists(filepath)
        self.assertRaises(ctagmvn.FileNotFoundError, ctagmvn.getFile, filepath)

class ExtractDependenciesTest(unittest.TestCase):
    def testNoneInputParameter(self):
        self.assertEmptyResponse(None)

    def testEmptyInputParameter(self):
        self.assertEmptyResponse("")

    def testEffectivelyEmptyInputParameter(self):
        self.assertEmptyResponse(" ")

    def testNoDependenciesPom(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("")
        self.assertEmptyResponse(pomContent)

    def testNoDependencyElementsPom(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("""
                <dependencies>
                </dependencies>""")
        self.assertEmptyResponse(pomContent)

    def assertEmptyResponse(self, param):
        self.assertEqual([], ctagmvn.extractDependencies(param))

    def testHappyPath(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("""
                <dependencies>
                    <dependency>
                        <groupId>org.springframework</groupId>
                        <artifactId>spring-core</artifactId>
                        <version>3.1.4.RELEASE</version>
                    </dependency>
                </dependencies>
            """)
        expected = ["org.springframework:spring-core:3.1.4.RELEASE"]
        self.assertEqual(expected, ctagmvn.extractDependencies(pomContent))

    def testExtractWithMavenPropertyPlaceholders(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("""
                <properties>
                    <spring.version>3.1.4.RELEASE</spring.version>
                </properties>
                <dependencies>
                    <dependency>
                        <groupId>org.springframework</groupId>
                        <artifactId>spring-core</artifactId>
                        <version>${spring.version}</version>
                    </dependency>
                </dependencies>
            """)
        expected = ["org.springframework:spring-core:3.1.4.RELEASE"]
        self.assertEqual(expected, ctagmvn.extractDependencies(pomContent))

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
        expected = ["/home/denarced/.m2/repository/org/springframework/spring-core/3.1.4.RELEASE/spring-core-3.1.4.RELEASE-sources.jar"]
        dependencies = ["org.springframework:spring-core:3.1.4.RELEASE"]
        self.filesystem.allPathsExist(True)
        self.assertEqual(
            expected, 
            self.jarDependencies.deriveSourcePaths(dependencies, None))

class ExtractPropertiesTest(unittest.TestCase):
    def testHappyPath(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("""
                <properties>
                    <spring.version>3.1.4.RELEASE</spring.version>
                </properties>
            """)
        project = etree.fromstring(pomContent)
        properties = ctagmvn.extractProperties(project)
        self.assertEqual("3.1.4.RELEASE", properties["spring.version"])

    def testNoPropertiesElement(self):
        pomContent = surroundWithPomXmlDeclarationAndProject("")
        project = etree.fromstring(pomContent)
        properties = ctagmvn.extractProperties(project)
        self.assertEqual(0, len(properties))

class ReplaceWithPropertiesTest(unittest.TestCase):
    def testSimpleReplace(self):
        p = "spring.version"
        v = "3.1.4.RELEASE"
        self.verify("${" + p + "}", v, {p: v})

    def testReplaceWithNonReplacedPrefix(self):
        p = "tomcat.port"
        v = "411"
        self.verify("10${" + p + "}", "10" + v, {p: v})

    def testReplaceWithNonExistentProperty(self):
        godlike = "${godlike}"
        self.verify(godlike, godlike, {})

    def verify(self, text, expected, properties):
        actual = ctagmvn.replaceWithProperties(text, properties)
        self.assertEqual(expected, actual)

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
    unittest.main()
