from __future__ import annotations

from dask.bag import Bag
from dask.delayed import Delayed
import multiprocessing as mp

from typing import Iterable, List, Iterator, TypeVar, Generic, Optional

T = TypeVar("T")

def _process_queue(in_q: mp.Queue[Optional[Delayed[T]]], out_q: mp.Queue[Optional[List[T]]]):
	while True:
		item = in_q.get()
		if item is None:
			out_q.put(None)
			return
		out_q.put(item.compute())

class BagIterator(Generic[T], Iterator[T], Iterable[T]):
	partitions: List[Delayed[List[T]]]
	in_queue: mp.Queue[Optional[Delayed[T]]]
	out_queue: mp.Queue[Optional[List[T]]]
	items: List[T]
	def _enqueue(self, count: int=1):
		for _ in range(count):
			if len(self.partitions) == 0:
				self.in_queue.put(None)
				return
			self.in_queue.put(self.partitions.pop())

	def _dequeue(self):
		return self.out_queue.get()

	def __init__(self, bag: Bag[T], preload: int=1):
		self.in_queue = mp.Queue(preload)
		self.out_queue = mp.Queue(preload)
		self.process = mp.Process(target=_process_queue, args=(self.in_queue, self.out_queue)).start()
		self.partitions = bag.to_delayed()
		self.items = []
		self._enqueue(preload)

	def __iter__(self):
		return self

	def __next__(self) -> T:
		if len(self.items) == 0:
			self._enqueue()
			empty: List[T] = []
			new_items = self._dequeue() or empty
			if len(new_items) == 0:
				raise StopIteration
			self.items = new_items
		return self.items.pop()

