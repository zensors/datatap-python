from os import path

import importlib_resources as resources

def save_html(output_dir: str, num_frames: int, frame_rate: int):
    index_html = resources.read_text("mldl.image.assets", "index.html")
    index_js = resources.read_text("mldl.image.assets", "index.js")
    index_css = resources.read_text("mldl.image.assets", "index.css")

    index_html = index_html.replace("{{ frameRate }}", str(frame_rate))
    index_html = index_html.replace("{{ numFrames }}", str(num_frames))

    open(path.join(output_dir, "index.html"), "w+").write(index_html)
    open(path.join(output_dir, "index.css"), "w+").write(index_css)
    open(path.join(output_dir, "index.js"), "w+").write(index_js)