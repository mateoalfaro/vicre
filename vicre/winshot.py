"""Windows screenshot backend: all monitors stitched, saved as a PNG file URI."""

import os
import pathlib
import tempfile


def capture_uri():
    from PIL import ImageGrab

    image = ImageGrab.grab(all_screens=True)
    fd, path = tempfile.mkstemp(prefix="vicre-", suffix=".png")
    os.close(fd)
    image.save(path, "PNG")
    return pathlib.Path(path).as_uri()
