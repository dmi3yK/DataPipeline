import gzip
import json
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from airbyte_cdk.sources.streams import IncrementalMixin
from airbyte_cdk.sources.streams.http import HttpStream


class KYVEStream(HttpStream, IncrementalMixin):
    url_base = None

    cursor_field = "offset"
    page_size = 100

    # Set this as a noop.
    primary_key = None

    def __init__(self, config: Mapping[str, Any], **kwargs):
        super().__init__(**kwargs)
        # Here's where we set the variable from our input to pass it down to the source.
        self.pool_id = config["pool_id"]
        self.url_base = config["url_base"]
        self._offset = config["start_id"]

        self.page_size = config["page_size"]
        self.max_pages = config.get("max_pages", None)
        # For incremental querying
        self._cursor_value = None

    def path(self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None,
             next_page_token: Mapping[str, Any] = None) -> str:
        return f"/kyve/query/v1beta1/finalized_bundles/{self.pool_id}"

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
        try:
            # set the state to store the latest bundle_id
            latest_bundle = response.json().get("finalized_bundles")[-1]
            self._cursor_value = latest_bundle.get("id")
        except IndexError:
            return []

        r = []
        for bundle in response.json().get("finalized_bundles"):
            storage_id = bundle.get("storage_id")
            # retrieve file from Arweave
            response_from_arweave = requests.get(f"https://arweave.net/{storage_id}")
            decompressed = gzip.decompress(response_from_arweave.content)
            # todo future: fail on incorrect hash, enabled after regenesis
            # bundle_hash = bundle.get("bundle_hash")
            # local_hash = hmac.new(b"", msg=decompressed, digestmod=hashlib.sha256).digest().hex()
            # assert local_hash == bundle_hash, print("HASHES DO NOT MATCH")
            decompressed_as_json = json.loads(decompressed)

            # extract the value from the key -> value mapping
            for _ in decompressed_as_json:
                r.append(_)
        return r

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        # in case we set a max_pages parameter we need to abort
        if self.max_pages and self._offset >= self.max_pages * self.page_size:
            return

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
