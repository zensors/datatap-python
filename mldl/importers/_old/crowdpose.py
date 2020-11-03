import argparse
import sys

import dask.bag
from dask.distributed import Client, LocalCluster

import mldl.concisejson as json
import mldl.validator
from mldl.importers.coco import clip, attach_image_hash, get_digest, coco_object_to_lake

HELP = """
How to run this:

VALIDATION:
python -m mldl.importers.crowdpose \
    --instances="/home/zensors/json/crowdpose_val.json" \
    --output="/home/zensors/crowdpose/val/*.image.jsonl.gz" \
    --clip

TEST/TRAIN (dimensions are flipped in dataset):
python -m mldl.importers.crowdpose \
    --instances="/home/zensors/json/crowdpose_[test/train].json" \
    --output="/home/zensors/crowdpose/[test/train]/*.image.jsonl.gz" \
    --clip --flip-hw
"""


TASK_DESC = []


def describe_task(s: str):
    TASK_DESC.append(s)


def print_task_description():
    print(", ".join(TASK_DESC))
    TASK_DESC.clear()


def get_crowdpose_kp_schema(category: dict):
    keypoint_names = list(map(lambda n: n.replace("_", "-"), category["keypoints"]))
    edges = list(
        map(
            lambda p: {
                "source": keypoint_names[p[0] - 6],
                "target": keypoint_names[p[1] - 6],
            },
            category["skeleton"],
        )
    )
    edges.extend(
        [
            {"source": "head", "target": "neck"},
            {"source": "neck", "target": "left-shoulder"},
            {"source": "neck", "target": "right-shoulder"},
        ]
    )
    nodes = {name: {} for name in keypoint_names}
    return {"graph": {"nodes": nodes, "edges": edges}}


def crowdpose_image_to_lake(image, do_clip=False, image_rel_path="./", classes=[], flip_hw=False):
    annos = image["annotations"]
    zimg = {"label": {"objectDetection": {}}}
    zimg["paths"] = [image_rel_path + image["file_name"]]
    cats = {"person": {"instances": [], "clusters": [],}}
    zimg["label"]["objectDetection"]["classes"] = cats

    # add in objects
    for anno in annos:
        name, zobj = coco_object_to_lake(anno, image, do_clip, "crowdpose", flip_hw)
        group = cats["person"]["clusters"] if anno.get("iscrowd", 0) else cats["person"]["instances"]
        if (
            "keypoints" in zobj
            and "keypointGraphs" not in zimg["label"]["objectDetection"]
        ):
            kp_name = tuple(zobj["keypoints"].keys())[0]
            zimg["label"]["objectDetection"]["keypointGraphs"] = {
                kp_name: get_crowdpose_kp_schema(anno["category"])
            }
        group.append(zobj)

    return zimg


def preprocess(instances_path):
    """Turn the file into a jsonl file so dask is happy about it.
    (Putting multi-hundred MBs of data in one JSON is really a bad idea, who would've thought.)

    CrowdPose: Each line of output produced by this has fields
    {
        annotations: {num_keypoints, iscrowd, keypoints, image_id, bbox, category_id, id}[],
        categories: {supercategory, id, name, keypoints, skeleton}[],
        file_name,
        id,
        height,
        width,
        crowdIndex,
    }
    """
    with open(instances_path, "r") as f:
        instances = json.load(f)
    print("JSON loaded")

    describe_task("Gathering Images and Categories")
    print_task_description()
    image_dict = dict(map(lambda img: (img["id"], img), instances["images"])) # id to {file_name,id,height,width,crowdIndex}
    category_dict = dict(map(lambda cat: (cat["id"], cat), instances["categories"])) # id to {supercategory,id,name,keypoints,skeleton}
    annotations = instances["annotations"] # {num_keypoints,iscrowd,keypoints,image_id,bbox,category_id,id}[]

    print("Folding category into annotations")
    annotations = map(
        lambda anno: {**anno, "category": category_dict[anno["category_id"]]},
        annotations,
    )

    print("Folding annotations into images")
    for image_id in image_dict:
        image_dict[image_id]["annotations"] = []
        image_dict[image_id]["categories"] = instances["categories"]
    for anno in annotations:
        image_dict[anno["image_id"]]["annotations"].append(anno)

    print("Outputting JSON lines for annotations")
    with open("./tmp.jsonl", "w") as f:
        f.writelines(map(lambda anno: json.dumps(anno) + "\n", image_dict.values(),))


def main(argv):
    parser = argparse.ArgumentParser(description=HELP)
    parser.add_argument(
        "--instances",
        required=True,
        help="Instance file for CrowdPose, in the form of crowdpose_[val/train].json",
    )
    parser.add_argument(
        "--images", help="Images if you want image hashes",
    )
    parser.add_argument(
        "--image-rel-path", default="../images/", help="relative path to the images"
    )
    parser.add_argument("--output", default="out/*.jsonl")
    parser.add_argument("--blocksize", default="30MB")
    parser.add_argument("--skip-preprocess", action="store_true")
    parser.add_argument("--clip", action="store_true")
    parser.add_argument("--flip-hw", action="store_true")
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()

    if not args.skip_preprocess:
        describe_task("Loading JSONs")
        print_task_description()
        preprocess(args.instances)
    # done preprocessing

    # initialize client
    cluster = LocalCluster(n_workers=args.workers)
    client = Client(cluster)

    describe_task("Loading to bag")
    print_task_description()
    images = dask.bag.read_text("./tmp.jsonl", blocksize=args.blocksize).map(json.loads)

    describe_task("To Zensors")
    zensors_images = images.map(
        crowdpose_image_to_lake,
        do_clip=args.clip,
        image_rel_path=args.image_rel_path,
        flip_hw=args.flip_hw,
    )

    if args.images is not None:
        describe_task("Calculate image hash")
        zensors_images = zensors_images.map(attach_image_hash, base=args.images)
    else:
        print("WARNING: not calculating image hash - image directory not provided")

    describe_task("Validate")
    # validation slows this down by a bit
    # but please don't disable it.
    zensors_images = zensors_images.map(
        mldl.validator.validate,
        schema_type="image",
        # when error occurs, we need to know what image this is on.
        exception_wrap=lambda d: RuntimeError("Paths: " + ", ".join(d["paths"])),
    )

    describe_task("Output")
    print_task_description()
    zensors_images_json = zensors_images.map(json.concise_dumps)
    zensors_images_json.to_textfiles(args.output)


if __name__ == "__main__":
    main(sys.argv)
