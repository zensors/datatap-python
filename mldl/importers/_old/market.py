# Boxes only my friend.
import sys
import argparse
import os.path
import glob

import mldl.concisejson as json
import mldl.validator

import uuid

"""
How to run this:

python -m mldl.importers.market \
    datasets/Market-1501-v15.09.15
    --output=out/*.image.jsonl
"""

def get_id(filename: str, ds_name="market-1501"):
    person_id = int(filename.split("_")[0])
    if person_id < 1:
        return None
    return str(uuid.uuid5(uuid.uuid5(uuid.NAMESPACE_URL, ds_name), str(person_id)))


def main(argv, ds_name="market-1501"):
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="directory for market dataset")
    parser.add_argument("--prefix", default="./images/", help="images prefix")
    parser.add_argument("--output", default="out/*.image.jsonl", help="output path")
    parser.add_argument("--dataset-name", default=ds_name, help="output path")
    args = parser.parse_args()
    aug_imgs_path = os.path.join(args.dir, "bounding_box_train_bgaug/*.jpg")
    train_imgs_path = os.path.join(args.dir, "bounding_box_train/*.jpg")
    test_imgs_path = os.path.join(args.dir, "bounding_box_test/*.jpg")
    query_imgs_path = os.path.join(args.dir, "query/*.jpg")
    aug_imgs = glob.glob(aug_imgs_path)
    train_imgs = glob.glob(train_imgs_path)
    test_imgs = glob.glob(test_imgs_path)
    query_imgs = glob.glob(query_imgs_path)
    for split, imgs in zip(["train", "train-bgaug", "test", "query"], [train_imgs, aug_imgs, test_imgs, query_imgs]):
        split_dir = os.path.join(args.output, split)
        os.makedirs(split_dir, exist_ok=True)
        with open(os.path.join(split_dir, "0.image.jsonl"), "w") as f:
            for img in imgs:
                filename = os.path.split(img)[-1]
                person_id = get_id(filename, args.dataset_name)
                if person_id is None:
                    continue
                f.write(json.dumps({
                    "paths": [args.prefix + filename],
                    "label": {
                        "objectDetection": {
                            "classes": {
                                "person": {
                                    "instances": [{
                                        "id": person_id,
                                        "boundingBox": [[0.0, 0.0], [1.0, 1.0]]
                                    }],
                                    "clusters": [],
                                }
                            }
                        }
                    },
                }))
                f.write("\n")

if __name__ == "__main__":
    main(sys.argv)
