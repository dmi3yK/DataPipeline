from typing import Any, List, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .streams import runtime_mapping
from .streams.stream import KYVEStream


class SourceKyve(AbstractSource):

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            # check if endpoint is available and returns valid data
            response = requests.get(f"{config['url_base']}/kyve/query/v1beta1/pool/{config['pool_id']}")
            if response.ok:
                return True, None
            else:
                # todo improve error handling for cases like pool not found
                return False, response.json()
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        # todo check if we can get it from class
        response = requests.get(f"{config['url_base']}/kyve/query/v1beta1/pool/{config['pool_id']}")
        runtime = response.json().get("pool").get("data").get("runtime")

        # select a typed stream from the mapping, if no typed mapping exists, fall back to default
        KYVE_TYPED_Stream = runtime_mapping.get(runtime, KYVEStream)

        return [KYVE_TYPED_Stream(config=config)]
