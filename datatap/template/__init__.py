"""
Templates are used to describe how a given annotation (or set of annotations) is structured.

All `Dataset`s and `DatasetVersion`s will have templates attached to them. If you need to
create your own template (for instance, in order to create a new dataset), you can
instantiate them as such:

```py
from datatap.template import ImageAnnotationTemplate, ClassAnnotationTemplate, InstanceTemplate

ImageAnnotationTemplate(classes = {
	"person": ClassAnnotationTemplate(
		instances = InstanceTemplate(
			bounding_box = True,
			segmentation = False, # this could also be omitted, since False is the default
			keypoints = { "head", "left shoulder", "right shoulder" },
			attributes = { "face mask": { "present", "absent" } }
		)
	)
})
```
"""


from .class_annotation_template import ClassAnnotationTemplate
from .image_annotation_template import ImageAnnotationTemplate
from .instance_template import InstanceTemplate
from .multi_instance_template import MultiInstanceTemplate

__all__ = [
	"ClassAnnotationTemplate",
	"ImageAnnotationTemplate",
	"InstanceTemplate",
	"MultiInstanceTemplate",
]
