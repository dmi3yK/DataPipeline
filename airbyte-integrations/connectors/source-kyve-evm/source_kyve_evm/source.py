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
    offset = 0

    # Set this as a noop.
    primary_key = None

    def __init__(self, pool_id: int, **kwargs):
        super().__init__(**kwargs)
        # Here's where we set the variable from our input to pass it down to the source.
        self.pool_id = pool_id

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
        # In case we use incremental streaming, we start with the stored offset
        if self.cursor_field in stream_state:
            params.update({"pagination.offset": stream_state.get(self.cursor_field)})

        return params

    def parse_response(
            self,
            response: requests.Response,
            stream_state: Mapping[str, Any],
            stream_slice: Mapping[str, Any] = None,
            next_page_token: Mapping[str, Any] = None,
    ) -> Iterable[Mapping]:
        # The response is a simple JSON whose schema matches our stream's schema exactly,
        # so we just return a list containing the response.
        return [response.json()]

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        json_response = response.json()
        next_key = json_response.get("pagination", {}).get("next_key")
        if next_key:
            self.offset += self.page_size
            return {"pagination.offset": self.offset}

    @property
    def state(self) -> Mapping[str, Any]:
        if self._cursor_value:
            return {self.cursor_field: self._cursor_value}
        else:
            return {self.cursor_field: None}

    @state.setter
    def state(self, value: Mapping[str, Any]):
        self._cursor_value = value[self.cursor_field]

    def read_records(self, *args, **kwargs) -> Iterable[Mapping[str, Any]]:
        for record in super().read_records(*args, **kwargs):
            latest_bundle = record.get("finalized_bundles")[-1]
            self._cursor_value = latest_bundle.get("id")
            yield record


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
        return [EVM(pool_id=config["pool_id"])]
