from typing import List, Union

from datatap.template.image_annotation_template import \
    ImageAnnotationTemplateJson
from datatap.template.video_annotation_template import \
    VideoAnnotationTemplateJson
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
    template: Union[ImageAnnotationTemplateJson, VideoAnnotationTemplateJson]
    splits: List[str]

