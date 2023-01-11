from typing import Any, List, Mapping, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from .streams import runtime_mapping


class SourceKyve(AbstractSource):
    valid_runtimes = ["@kyvejs/evm", "@kyvejs/uniswap"]
    start_id = 0
    runtime = ""

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            pool_id_input = config["pool_id"]

            response = requests.get(f"https://api.korellia.kyve.network/kyve/query/v1beta1/pool/{pool_id_input}")
            if response.ok:
                runtime = response.json().get("pool").get("data").get("runtime")
                self.runtime = runtime
                if runtime in self.valid_runtimes:

                    self.start_id = int(response.json().get("pool").get("data").get("total_bundles")) - 1

                    return True, None
                else:
                    return False, f"Runtime '{runtime}' is not supported."
            else:
                # todo improve error handling for cases like pool not found
                return False, response.json()
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        Stream = runtime_mapping[self.runtime]
        return [Stream(pool_id=config["pool_id"], start_id=self.start_id)]
