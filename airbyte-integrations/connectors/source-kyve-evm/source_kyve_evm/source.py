from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams import IncrementalMixin


class EVM(HttpStream):
    url_base = "https://api.beta.kyve.network/kyve/query/v1beta1/finalized_bundles/"

    cursor_field = "to_height"
    page_size = 100

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
        # The api requires that we include the Pokemon name as a query param so we do that in this method.
        params = {"pagination.limit": self.page_size}
        if next_page_token:
            params.update(**next_page_token)
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
            return {"pagination.key": next_key}

    """
    @property
    def state(self) -> Mapping[str, Any]:
        if self._cursor_value:
            return {self.cursor_field: self._cursor_value}
        else:
            return {self.cursor_field: 0}

    @state.setter
    def state(self, value: Mapping[str, Any]):
        self._cursor_value = value[self.cursor_field]

    def read_records(self, *args, **kwargs) -> Iterable[Mapping[str, Any]]:
        for record in super().read_records(*args, **kwargs):
            latest_record_date = record.get("finalized_bundle").get("to_height")
            self._cursor_value = latest_record_date
            yield record

    def _construct_slices(self, start_height: int) -> List[Mapping[str, Any]]:
        # todo: here is the problem of getting the next slice because we do not always hit the max_bundle_size
        response = requests.get(f"https://api.beta.kyve.network/kyve/query/v1beta1/pool/{self.pool_id}")
        if response.ok:
            heights = []
            latest_height = int(response.json().get("pool").get("data").get("current_height"))
            while start_height < latest_height:
                heights.append({self.cursor_field: start_height})
                start_height += 100
            return heights
        else:
            # todo error handling
            pass

    def stream_slices(self, sync_mode, cursor_field: List[str] = None, stream_state: Mapping[str, Any] = None) -> Iterable[
        Optional[Mapping[str, Any]]]:

        if stream_state:
            start_height = int(stream_state.get(self.cursor_field, 0))
        else:
            start_height = 0

        return self._construct_slices(start_height)
    """


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
