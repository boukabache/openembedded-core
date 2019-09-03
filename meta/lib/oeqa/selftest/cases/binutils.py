# SPDX-License-Identifier: MIT
import os
import sys
import re
import logging
from oeqa.core.decorator import OETestTag
from oeqa.selftest.case import OESelftestTestCase
from oeqa.utils.commands import bitbake, get_bb_var, get_bb_vars

def parse_values(content):
    for i in content:
        for v in ["PASS", "FAIL", "XPASS", "XFAIL", "UNRESOLVED", "UNSUPPORTED", "UNTESTED", "ERROR", "WARNING"]:
            if i.startswith(v + ": "):
                yield i[len(v) + 2:].strip(), v
                break

@OETestTag("machine")
class BinutilsCrossSelfTest(OESelftestTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not hasattr(cls.tc, "extraresults"):
            cls.tc.extraresults = {}

        if "ptestresult.sections" not in cls.tc.extraresults:
            cls.tc.extraresults["ptestresult.sections"] = {}

    def test_binutils(self):
        self.run_binutils("binutils")

    def test_gas(self):
        self.run_binutils("gas")

    def test_ld(self):
        self.run_binutils("ld")

    def run_binutils(self, suite):
        features = []
        features.append('CHECK_TARGETS = "{0}"'.format(suite))
        self.write_config("\n".join(features))

        recipe = "binutils-cross-testsuite"
        bb_vars = get_bb_vars(["B", "TARGET_SYS", "T"], recipe)
        builddir, target_sys, tdir = bb_vars["B"], bb_vars["TARGET_SYS"], bb_vars["T"]

        bitbake("{0} -c check".format(recipe))

        ptestsuite = "binutils-{}".format(suite) if suite != "binutils" else suite
        self.tc.extraresults["ptestresult.sections"][ptestsuite] = {}

        sumspath = os.path.join(builddir, suite, "{0}.sum".format(suite))
        if not os.path.exists(sumspath):
            sumspath = os.path.join(builddir, suite, "testsuite", "{0}.sum".format(suite))

        failed = 0
        with open(sumspath, "r") as f:
            for test, result in parse_values(f):
                self.tc.extraresults["ptestresult.{}.{}".format(ptestsuite, test)] = {"status" : result}
                if result == "FAIL":
                    self.logger.info("failed: '{}'".format(test))
                    failed += 1

        self.assertEqual(failed, 0)
