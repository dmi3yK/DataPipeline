import gzip
import json
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams import IncrementalMixin


class EVM(HttpStream, IncrementalMixin):
    url_base = "https://api.beta.kyve.network/kyve/query/v1beta1/finalized_bundles/"

    cursor_field = "offset"
    page_size = 100

    # Set this as a noop.
    primary_key = None

    def __init__(self, pool_id: int, start_id: int = 0, **kwargs):
        super().__init__(**kwargs)
        # Here's where we set the variable from our input to pass it down to the source.
        self.pool_id = pool_id

        self._offset = start_id

        # For incremental querying
        self._cursor_value = None

    def path(self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None,
             next_page_token: Mapping[str, Any] = None) -> str:
        return f"{self.pool_id}"

    def request_params(
            self,
            stream_state: Mapping[str, Any],
            stream_slice: Mapping[str, Any] = None,
            next_page_token: Mapping[str, Any] = None,
    ) -> MutableMapping[str, Any]:
        # Set the pagesize in the request parameters
        params = {"pagination.limit": self.page_size}

        # Handle pagination by inserting the next page's token in the request parameters
        if next_page_token:
            params.update(**next_page_token)
        # In case we use incremental streaming, we start with the stored _offset
        if self.cursor_field in stream_state:
            params.update({"pagination.offset": stream_state.get(self.cursor_field)})
        else:
            params.update({"pagination.offset": self._offset})

        return params

    def parse_response(
            self,
            response: requests.Response,
            stream_state: Mapping[str, Any],
            stream_slice: Mapping[str, Any] = None,
            next_page_token: Mapping[str, Any] = None,
    ) -> Iterable[Mapping]:
        # set the state to store the latest bundle_id
        latest_bundle = response.json().get("finalized_bundles")[-1]
        self._cursor_value = latest_bundle.get("id")

        r = []
        for bundle in response.json().get("finalized_bundles"):
            storage_id = bundle.get("storage_id")

            # retrieve file from Arweave
            response_from_arweave = requests.get(f"https://arweave.net/{storage_id}")
            decompressed = gzip.decompress(response_from_arweave.content)
            # TODO: Check for data hash -> sha256 of data
            decompressed_as_json = json.loads(decompressed)
            # extract the value from the key -> value mapping
            for _ in decompressed_as_json:
                r.append(_.get("value"))

        return r

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        json_response = response.json()
        next_key = json_response.get("pagination", {}).get("next_key")
        if next_key:
            self._offset += self.page_size
            return {"pagination.offset": self._offset}

    @property
    def state(self) -> Mapping[str, Any]:
        if self._cursor_value:
            return {self.cursor_field: self._cursor_value}
        else:
            return {self.cursor_field: self._offset}

    @state.setter
    def state(self, value: Mapping[str, Any]):
        self._cursor_value = value[self.cursor_field]


class SourceKyveEvm(AbstractSource):
    valid_runtimes = ["@kyve/evm"]

    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            pool_id_input = config["pool_id"]

            response = requests.get(f"https://api.beta.kyve.network/kyve/query/v1beta1/pool/{pool_id_input}")
            if response.ok:
                runtime = response.json().get("pool").get("data").get("runtime")
                if runtime in self.valid_runtimes:
                    return True, None
                else:
                    return False, f"Runtime '{runtime}' is not supported."
            else:
                # todo improve error handling for cases like pool not found
                return False, response.json()
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        return [EVM(pool_id=config["pool_id"], start_id=5947)]
