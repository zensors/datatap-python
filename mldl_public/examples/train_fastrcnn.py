# torchvision dependencies
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

# mldl dependencies
from mldl_public.dataset.dataset import Dataset, set_neo4j_url
import mldl.utils.torchvision

# We load the MLDL dataset and transform it into what torchvision models understands

# load the dataset, change it to your own uid.
dataset = Dataset.load("f10a05e0-8aaf-4065-9864-a9bf77fb7849", 1000)

classes = list(dataset.validation.take(1)[0].classes.keys())
num_classes = len(classes) + 1 # 0 is the background
class_to_id_map = { c: i+1 for i, c in enumerate(classes) }

# this loads the dataset into a torchvision compatible format, and streams data in the background
torch_dataset = mldl.utils.torchvision.load_bag(dataset.validation, class_to_id_map)

# We are going to start from a model pretrained on COCO, and modify it to use our classes
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
in_features = model.roi_heads.box_predictor.cls_score.in_features
model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

# start the training. note that if you want to do this in production
# you should consider using torch dataloader, instead of directly iterating
# the dataset
model.train()

to_tensor = torchvision.transforms.ToTensor()
for epoch in range(10):
    for image, target in torch_dataset:
        image = to_tensor(image)
        model([image], [target])

