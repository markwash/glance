import errno
import os
import pickle
import re
import subprocess
import sys


class Project(object):
    
    def __init__(self, basedir):
        self.basedir = basedir
        self.testfiles = None

    def generate(self):
        self.testfiles = []
        for dirpath, dirnames, filenames in os.walk(self.basedir):
            self.testfiles.extend(
                [TestFile(self, os.path.join(dirpath, n))
                    for n in filenames
                    if n.endswith('.py')]
            )

        to_remove = []
        for i, testfile in enumerate(self.testfiles):
            success = testfile.generate()
            if not success:
                to_remove.append(i)

        for i in reversed(to_remove):
            del self.testfiles[i]



class TestFile(object):
    def __init__(self, project, filepath):
        self.project = project
        self.filepath = filepath
        self.testcases = None

    def __str__(self):
        return self.filepath

    def __repr__(self):
        return str(self)

    def generate(self):
        classnames = cached(_harvest_class_names, self.filepath)
        output = cached(_run_test_file, self.filepath)
        if 'Ran 0 tests' in output:
            return False
        if 'ERROR' in output:
            print output
        self._harvest_test_output(output, classnames)
        return True

    def _harvest_test_output(self, output, classnames):
        self.testcases = []
        test_case_re = re.compile('^([A-Za-z]\S*)\s*$')
        test_fn_re = re.compile('^\s+test.*$')
        current = None
        payload = []
        for line in output.split('\n'):
            match = test_case_re.match(line)
            if match:
                if current is not None and current in classnames:
                    testcase = TestCase(self, current, payload)
                    self.testcases.append(testcase)
                current = match.group(1)
                payload = []
                continue

            match = test_fn_re.match(line)
            if match:
                payload.append(line)
                continue
        
        if current is not None and current in classnames:
            testcase = TestCase(self, current, payload)
            self.testcases.append(testcase)

class TestCase(object):
    def __init__(self, testfile, name, test_lines):
        self.testfile = testfile
        self.name = name
        self.tests = []
        for line in test_lines:
            self.tests.append(Test(self, line))
        self._time = None

    def __str__(self):
        return '%s:%s %0.1f %0.2f' % (self.testfile, self.name, self.time,
                                     1.0 * self.skipped / self.count)

    def __repr__(self):
        return str(self)

    @property
    def time(self):
        if self._time is None:
            self._time = 0.0
            for test in self.tests:
                self._time += test.time
        return self._time

    @property
    def count(self):
        return len(self.tests)

    @property
    def skipped(self):
        if not hasattr(self, '_skipped'):
            self._skipped = 0
            for test in self.tests:
                if test.result == 'SKIP':
                    self._skipped += 1
        return self._skipped

    @property
    def coverage(self):
        if not hasattr(self, '_coverage'):
            cov = None
            for test in self.tests:
                if cov is None:
                    cov = test.coverage
                else:
                    cov = merge_coverage(cov, test.coverage)
            self._coverage = cov
        return self._coverage

    @property
    def unique_coverage(self):
        if not hasattr(self, '_unique_coverage'):
            uniq = self.coverage
            for testfile in self.testfile.project.testfiles:
                for testcase in testfile.testcases:
                    if testcase is self:
                        continue
                    uniq = diff_coverage(uniq, testcase.coverage)
            self._unique_coverage = uniq
        return self._unique_coverage

    @property
    def unique_coverage_line_count(self):
        if not hasattr(self, '_uniq_cov_line_count'):
            count = coverage_line_count(self.unique_coverage)
            self._uniq_cov_line_count = count
        return self._uniq_cov_line_count


class Test(object):
    color_re = re.compile('\x1b\[[0-9]+m')
    line_re = re.compile('^\s+(test\S*)\s+(\S+)(?:\s+(\S+))?\s*$')

    def __init__(self, case, line):
        self.case = case
        line = re.sub(self.color_re, ' ', line)
        match = self.line_re.match(line)
        assert match is not None, repr(line)
        self.name = match.group(1)
        self.result = match.group(2)
        self.time = match.group(3)
        if self.time is None:
            self.time = 0.0
        else:
            self.time = float(self.time)

    @property
    def coverage(self):
        if not hasattr(self, '_coverage'):
            cov = cached(_individual_test_coverage,
                         self.case.testfile.filepath,
                         self.case.name,
                         self.name)

            self._coverage = pickle.loads(cov)
        return self._coverage
        


def main():
    project = Project(sys.argv[1])
    project.generate()
    all_test_cases = []
    for testfile in project.testfiles:
        all_test_cases.extend(testfile.testcases)

    all_test_cases.sort(key=lambda c: c.time, reverse=True)
    print 'Slowest Test Cases'
    print '--------------------------'
    print '\n'.join([str(c) for c in all_test_cases[:20]])
    print


    all_test_cases.sort(key=lambda c: float(c.skipped) / c.count, reverse=True)
    print 'Most Skipped Test Cases'
    print '---------------------------'
    print '\n'.join([str(c) for c in all_test_cases[:20] if c.skipped > 0])
    print


    all_test_cases.sort(key=lambda c: c.unique_coverage_line_count, reverse=True)
    print 'Most unique coverage'
    print '---------------------------'
    print '\n'.join([("%s, %d" % (c, c.unique_coverage_line_count))
                     for c in all_test_cases if c.unique_coverage_line_count > 0])


def _run_test_file(path):
    cmd = 'tox -e py27 -- --nologcapture --tests %s' % path
    print cmd
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return out

def _harvest_class_names(path):
    class_names = set()
    class_re = re.compile('\s*class\s+([^(]+)\(.*$')
    with open(path) as f:
        for line in f:
            match = class_re.match(line)
            if match:
                class_names.add(match.group(1))
    return class_names

def _individual_test_coverage(path, case, test):
    try:
        os.unlink('.coverage')
    except OSError as err:
        if not err.errno == errno.ENOENT:
            raise
    cmd = 'tox -e py27 -- --tests %s:%s.%s --with-coverage'
    cmd = cmd % (path, case, test)
    print cmd
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    return open('.coverage').read()

import shelve
cache = shelve.open('cache')
def cached(func, *args):
    call_info = '%s:%s' % (func.__name__, ':'.join(args))
    if call_info in cache:
        return cache[call_info]
    else:
        result = func(*args)
        cache[call_info] = result
        return result


def merge_coverage(*covs):
    merged = {}
    merged['collector'] = covs[0]['collector']
    merged['arcs'] = {}
    merged['lines'] = merge_linesets(*[cov['lines'] for cov in covs])
    return merged


def merge_linesets(*linesets):
    merged = {}
    for lineset in linesets:
        for key, linenums in lineset.iteritems():
            if not key in merged:
                merged[key] = set(linenums)
            else:
                merged[key] |= set(linenums)
    for key in merged.keys():
        linenums = list(merged[key])
        linenums.sort()
        merged[key] = linenums
    return merged


def diff_coverage(minuend, subtrahend):
    diff = {}
    diff['collector'] = minuend['collector']
    diff['arcs'] = {}
    diff['lines'] = diff_linesets(minuend['lines'], subtrahend['lines'])
    return diff


def diff_linesets(lineset1, lineset2):
    diff = {}
    for key, linenums1 in lineset1.iteritems():
        if not key in lineset2:
            diff[key] = linenums1
        else:
            linenums2 = lineset2[key]
            difflinenums = list(set(linenums1) - set(linenums2))
            difflinenums.sort()
            diff[key] = difflinenums
    return diff

def coverage_line_count(coverage):
    count = 0
    for lines in coverage['lines'].values():
        if len(lines) > 0:
            count += len(lines)
            if lines[0] == -1:
                count -= 1
            if lines == [-1, 1]:
                count -= 1
    return count


if __name__ == '__main__':
    main()
