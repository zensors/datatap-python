from io import BufferedReader


class OpenFile(BufferedReader): # this isn't true but it's close enough for how we're using fsspec
	pass

def open(uri: str) -> OpenFile: ...

