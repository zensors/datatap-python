from typing import Callable, Generator
import tensorflow as tf

class Strategy:
    def experimental_distribute_datasets_from_function(
        self,
        fn: Callable[[tf.distribute.InputContext], tf.data.Dataset]
    ) -> tf.distribute.DistributedDataset: ...

class MultiWorkerMirroredStrategy(Strategy):
    pass