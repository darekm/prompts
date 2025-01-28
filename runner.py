import sys
import unittest

import xmlrunner

from tests import (
    test_evaluate_fk
)


def makesuite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromModule(test_evaluate_fk))

    return suite


def run():
    s = makesuite()
    r = unittest.TextTestRunner(verbosity=3)
    return r.run(s)


def runxml():
    s = makesuite()
    r = xmlrunner.XMLTestRunner(output='test-results')
    return r.run(s)


if __name__ == '__main__':
    result = runxml()
    sys.exit(not result.wasSuccessful())
