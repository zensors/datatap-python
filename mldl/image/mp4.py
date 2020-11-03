import ffmpeg
import PIL.Image
from typing import Optional, Tuple, Mapping, Sequence

from mldl.droplet import VideoAnnotation

from . import loader
from . import pil

# requires ffmpeg to be installed

class FFmpegWriter:
    def __init__(self, url: str, width: int = 800, height: int = 480, fps: Optional[int] = None):
        self.width = width
        self.height = height
        self.fps = fps
        stream = ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="rgb24", s="{}x{}".format(width, height), framerate=fps
        )
        self.process = (
            stream.output(url, pix_fmt="yuv420p")
            .overwrite_output()
            .run_async(pipe_stdin=True, quiet=True)
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, img: PIL.Image.Image):
        w, h = img.size
        if img.mode != "RGB":
            img = img.convert("RGB")
        if w != self.width or h != self.height:
            img = img.resize((self.width, self.height), PIL.Image.BILINEAR)
        self.process.stdin.write(img.tobytes())

    def close(self):
        self.process.stdin.close()
        self.process.wait()

def save_mp4(
    path: str,
    video_annotation: VideoAnnotation,
    fps: Optional[int] = None,
    class_skeletons: Mapping[str, Sequence[Tuple[str, str]]] = {},
    size: Optional[Tuple[int, int]] = None
):
    if size is None:
        size = loader.load_image_from_annotation(video_annotation.frames[0]).size
    with FFmpegWriter(path, size[0], size[1], fps) as video_writer:
        for frame in video_annotation.frames:
            image = pil.generate_pil(
                frame, class_skeletons = class_skeletons, size = size, use_image = True
            )
            video_writer.write(image)
