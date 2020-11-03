import argparse
import json

import flask
import PIL.Image
from dask.distributed import Client

import mldl.image.skeletons
import mldl.image.svg
from mldl.neo4j.load import load_dataset


HTML_TEMPLATE = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>title</title>
    </head>
    <body>
        <div style="position: absolute; left: 0; top: 0; right: 0; bottom: 0;">
            <a href="./{prev}.html">Prev</a>
            <a href="./{next}.html">Next</a>
            <iframe src="./{}.svg" style="position: fixed; top: 30px; left: 0; width: 100%; height: calc(100% - 30px); border: none" />
        </div>
    </body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uid", help="Dataset UID")
    parser.add_argument("--host", help="Host")
    parser.add_argument("--port", type=int, help="Port")
    parser.add_argument("--kp-classes", type=str, help="List of classes with keypoints", nargs="*")
    parser.add_argument("--skeletons", type=str, help="List of skeletons for given classes (refer to skeletons.py)", nargs="*")

    args = parser.parse_args()

    client = Client()

    annotations = load_dataset(args.uid, npartitions = 10).compute()

    class_skeletons = {
        args.kp_classes[i]: mldl.image.skeletons.SKELETONS[args.skeletons[i]]
        for i in range(len(args.kp_classes))
    }

    app = flask.Flask(__name__)
    prefix = ""

    @app.route(prefix + "/<int:line_num>.svg")
    def get_svg(line_num):
        index = line_num - 1
        if index < 0 or index >= len(annotations):
            return (
                "Line number should be between 1 and {}".format(len(annotations)),
                404,
            )
        svg = mldl.image.svg.generate_svg(annotations[index], class_skeletons = class_skeletons)
        return flask.Response(svg, mimetype="image/svg+xml")

    @app.route(prefix + "/<int:line_num>.droplet")
    def get_droplet(line_num):
        index = line_num - 1
        if index < 0 or index >= len(annotations):
            return (
                "Line number should be between 1 and {}".format(len(annotations)),
                404,
            )
        return flask.Response(str(annotations[index]))

    @app.route(prefix + "/<int:line_num>.html")
    def get_html(line_num):
        index = line_num - 1
        if index < 0 or index >= len(annotations):
            return (
                "Line number should be between 1 and {}".format(len(annotations)),
                404,
            )
        return HTML_TEMPLATE.format(line_num, prev=line_num - 1, next=line_num + 1)

    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
