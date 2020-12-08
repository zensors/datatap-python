import os

class Environment:
	"""
	A class providing static access to parameters related to the execution
	environment of the module.
	"""

	API_KEY = os.getenv("DATATAP_API_KEY")
	"""
	The default API key used for API calls.
	"""

	BASE_URI = os.getenv("DATATAP_BASE_URI", "https://app.datatap.dev")
	"""
	The base URI used for referencing the dataTap application, e.g. for API
	calls. One might change this to use an HTTP proxy, for example.
	"""
