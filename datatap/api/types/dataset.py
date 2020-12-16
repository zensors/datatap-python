from datatap.template.image_annotation_template import ImageAnnotationTemplateJson
from typing import List
from typing_extensions import TypedDict

class JsonDatasetRepository(TypedDict):
    namespace: str
    name: str

class JsonDataset(TypedDict):
    """
    The API type of a dataset.
    """
    uid: str
    database: str
    repository: JsonDatasetRepository
    template: ImageAnnotationTemplateJson
    splits: List[str]

