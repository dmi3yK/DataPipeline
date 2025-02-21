#
# Copyright (c) 2023 BCP Innovations UG, all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_kyve import SourceKyve

if __name__ == "__main__":
    source = SourceKyve()
    launch(source, sys.argv[1:])
