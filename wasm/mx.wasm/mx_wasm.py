#
# Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
#
# The Universal Permissive License (UPL), Version 1.0
#
# Subject to the condition set forth below, permission is hereby granted to any
# person obtaining a copy of this software, associated documentation and/or
# data (collectively the "Software"), free of charge and under any and all
# copyright rights in the Software, and any and all patent rights owned or
# freely licensable by each licensor hereunder covering either (i) the
# unmodified Software as contributed to or provided by such licensor, or (ii)
# the Larger Works (as defined below), to deal in both
#
# (a) the Software, and
#
# (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
# one is included with the Software each a "Larger Work" to which the Software
# is contributed by such licensors),
#
# without restriction, including without limitation the rights to copy, create
# derivative works of, display, perform, and distribute the Software and make,
# use, sell, offer for sale, import, export, have made, and have sold the
# Software and the Larger Work(s), and to sublicense the foregoing rights on
# either these or other terms.
#
# This license is subject to the following condition:
#
# The above copyright notice and either this complete permission notice or at a
# minimum a reference to the UPL must be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import mx
import mx_subst
import mx_wasm_benchmark  # pylint: disable=unused-import

import errno
import glob
import os

_suite = mx.suite('wasm')

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def remove_extension(filename):
    if filename.endswith(".c"):
        return filename[:-2]
    else:
        mx.abort("Unknown extension: " + filename)

class GraalWasmSourceFileProject(mx.ArchivableProject):
    def __init__(self, suite, name, deps, workingSets, subDir, theLicense, **args):
        self.suite = suite
        self.name = name
        # _results =
        # _output = output or os.path.join(mx.get_mxbuild_dir(self), self.name)
        mx.ArchivableProject.__init__(self, suite, name, deps, workingSets, theLicense, **args)

    # def getOutput(self, replaceVar=mx_subst.results_substitutions):
    #       return ""

    # def getResults(self, replaceVar=mx_subst.results_substitutions):
    #     if self.results is None:
    #         self.results = glob.glob1(self.getOutput(), '*.wasm')
    #     return super(GraalWasmSourceFileProject, self).getResults(replaceVar=replaceVar)

    def getSourceDir(self):
        return os.path.join(self.dir, "src", self.name, self.subDir)

    def getOutputDir(self):
        return os.path.join(self.get_output_base(), self.name)

    def getSources(self):
        for root, dirs, files in os.walk(self.getSourceDir()):
            for filename in files:
                if filename.endswith(".c"):
                    yield (root, filename)

    def getResults(self):
        output_dir = self.getOutputDir()
        for root, filename in self.getSources():
            yield os.path.join(output_dir, remove_extension(filename) + ".wasm")

    def getArchivableResults(self, use_relpath=True, single=False):
        for r in self.getResults():
            mx.log(r)
            yield r

    def output_dir(self):
        return self.getOutputDir()

    def archive_prefix(self):
        return ""

    def getBuildTask(self, args):
        output_base = self.get_output_base()
        return GraalWasmSourceFileTask(self, args, output_base)

class GraalWasmSourceFileTask(mx.ProjectBuildTask):
    def __init__(self, project, args, output_base):
        self.output_base = output_base
        self.project = project
        mx.ProjectBuildTask.__init__(self, args, 1, project)

    def __str__(self):
        return 'Building {} with Emscripten'.format(self.subject.name)

    def build(self):
        source_dir = self.subject.getSourceDir()
        output_dir = self.subject.getOutputDir()
        mkdir_p(output_dir)
        emcc_dir = mx.get_env("EMCC_DIR", None)
        if not emcc_dir:
            mx.abort("No EMCC_DIR specified - the source programs will not be compiled to .wat and .wasm.")
        mx.log("Building files from the source dir: " + source_dir)
        emcc_cmd = os.path.join(emcc_dir, "emcc")
        flags = ["-Os"]
        for root, filename in self.subject.getSources():
            path = os.path.join(root, filename)
            output_path = os.path.join(output_dir, remove_extension(filename) + ".js")
            mx.run([emcc_cmd] + flags + [path, "-o", output_path])

    def needsBuild(self, newestInput):
        return (True, None)

    def clean(self, forBuild=False):
        pass
