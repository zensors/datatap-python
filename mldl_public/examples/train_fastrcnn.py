import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

from mldl_public.api.entities import Api
from mldl_public.torch.dataloader import batched_dataloader

# If [MLDL_API_KEY] is not in your environment, then pass it as the first argument
api = Api()

db_list = api.get_database_list()
db = db_list[0]
ds_list = db.get_dataset_list()
ds = ds_list[0]
if ds.latest_version is None:
    raise Exception()

classes = ["__background__"] + sorted(ds.latest_version.template.classes.keys())
num_classes = len(classes)
class_map = { cls: i for i, cls in enumerate(classes) }

loader = batched_dataloader(ds.latest_version, "training", class_mapping = class_map)


# We are going to start from a model pretrained on COCO, and modify it to use our classes
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
in_features = model.roi_heads.box_predictor.cls_score.in_features
model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

# start the training. note that if you want to do this in production
# you should consider using torch dataloader, instead of directly iterating
# the dataset
model.train()

for epoch in range(10):
    for batch in loader:
        model(batch.images, [
            { "boxes": boxes, "labels": labels }
            for boxes, labels in zip(batch.boxes, batch.labels)
        ])
    print(f"Finished epoch {epoch}")

