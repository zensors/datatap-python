# Boxes only my friend.
import sys
import argparse
import os.path
import glob

import mldl.concisejson as json
import mldl.validator

import uuid

from . import market

main = market.main

"""
How to run this:

python -m mldl.importers.duke \
    datasets/DukeMTMC-reID \
    --output=out/*.image.jsonl
"""

if __name__ == "__main__":
    main(sys.argv, "duke-reid")
