# MLDL Python Library

The MLDL Python Library is a collection of utilities and examples
related to the MLDL specification.

## MLDL Validator
MLDL Validator validates a JSON Lines file against the MLDL specification

python -m mldl.validator < test.jsonl

## MLDL importers
Imports different file formats into MLDL

## MLDL SVG generator
Generates SVG.

## MLDL Explorer
Explores annotations in a JSON Lines file.
```
python3 -m mldl.explorer \
    /home/zensors/zensors-inc/zcore/python/libraries/mldl/out/coco/2017/train2/00.jsonl \
    --image-path=/home/zensors/coco/2017/train2017 \
    --host 0.0.0.0 --port 5002
```

## Samples
Samples for using the MLDL.

