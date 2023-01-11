from typing import Any, Mapping

from .stream import KYVEStream


class Uniswap(KYVEStream):

    def parse_value(self, value: Any) -> Mapping:
        # in the Uniswap runtime, value ewill always be a list
        pass
