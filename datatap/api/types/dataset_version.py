from datatap.template.image_annotation_template import ImageAnnotationTemplateJson
from typing import List
from typing_extensions import TypedDict

class JsonDatasetVersion(TypedDict):
    """
    The API type of a dataset version.
    """
    name: str
    uid: str
    database: str
    splits: List[str]
    template: ImageAnnotationTemplateJson

