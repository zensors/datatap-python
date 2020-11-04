from typing import List, Optional
from mldl.utils import basic_repr, OrNullish

from .dataset import Dataset
from ..endpoints import ApiEndpoints
from ..types import JsonDatasetReference

class DatasetReference:
    _endpoints: ApiEndpoints

    name: str
    database: str
    dataset: Optional[Dataset]
    previous_values: List[str]

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDatasetReference):
        return DatasetReference(
            endpoints,
            name = json["name"],
            database = json["database"],
            dataset = OrNullish.bind(json.get("dataset", None), lambda x: Dataset.from_json(endpoints, x)),
            previous_values = json["previousValues"]
        )

    def __init__(self, endpoints: ApiEndpoints, *, name: str, database: str, dataset: Optional[Dataset], previous_values: List[str]):
        self._endpoints = endpoints
        self.name = name
        self.database = database
        self.dataset = dataset
        self.previous_values = previous_values

    def get_previous_datasets(self):
        return [
            Dataset.from_json(self._endpoints, self._endpoints.dataset.query(self.database, dataset_uid))
            for dataset_uid in self.previous_values
        ]

    def __repr__(self):
        return basic_repr("DatasetReference", name = self.name, database = self.database, previous_values = self.previous_values, dataset = self.dataset)
