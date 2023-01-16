from typing import Any, List, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .streams import runtime_mapping
from .streams.stream import KYVEStream


class SourceKyve(AbstractSource):

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            pool_id_input = config["pool_id"]

            response = requests.get(f"https://api.korellia.kyve.network/kyve/query/v1beta1/pool/{pool_id_input}")
            if response.ok:
                return True, None
            else:
                # todo improve error handling for cases like pool not found
                return False, response.json()
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:

        url_base = "https://api.korellia.kyve.network/kyve/query/v1beta1/finalized_bundles/"

        # todo check if we can get it from class
        response = requests.get(f"https://api.korellia.kyve.network/kyve/query/v1beta1/pool/{config['pool_id']}")
        runtime = response.json().get("pool").get("data").get("runtime")

        # select a typed stream from the mapping, if no typed mapping exists, fall back to default
        KYVE_TYPED_Stream = runtime_mapping.get(runtime, KYVEStream)

        return [KYVE_TYPED_Stream(pool_id=config["pool_id"], offset=config.get("start_id", 0), url_base=url_base)]
