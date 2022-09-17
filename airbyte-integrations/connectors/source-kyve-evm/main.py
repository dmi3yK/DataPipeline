#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_kyve_evm import SourceKyveEvm

if __name__ == "__main__":
    source = SourceKyveEvm()
    launch(source, sys.argv[1:])
