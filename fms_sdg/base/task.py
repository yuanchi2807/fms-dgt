# Standard
from dataclasses import asdict, dataclass
from typing import Any, List, Optional, TypeVar
import abc
import json
import os

DEFAULT_OUTPUT_DIR = "output"


@dataclass
class SdgData(abc.ABC):
    """This class is intended to hold the seed / machine generated instruction data"""

    task_name: Optional[str]

    def to_output_dict(self):
        return asdict(self)


class PostProcessingType(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


class SdgTask(metaclass=PostProcessingType):
    """This class is intended to hold general task information"""

    DATA_TYPE = SdgData

    def __init__(
        self,
        name: str,
        task_description: str,
        created_by: str,
        data_builder: str,
        output_dir: Optional[str] = None,
        seed_data: Optional[List[Any]] = None,
        num_outputs_to_generate: Optional[int] = None,
        **kwargs: Any,
    ):
        self._name = name
        self._task_description = task_description
        self._created_by = created_by
        self._data_builder = data_builder
        self._num_outputs_to_generate = num_outputs_to_generate
        self.machine_data = []

        self._output_dir = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR
        self._output_path = self._get_default_output_path()
        self._seed_data = seed_data

    def __post_init__(self):
        # we use post_init for cases when examples are instantiated with elements from subclass __init__
        self._seed_data = [self.instantiate_example(**s) for s in self._seed_data]

    def instantiate_example(self, **kwargs: Any):
        return self.DATA_TYPE(task_name=self.name, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def seed_data(self):
        return self._seed_data

    @property
    def task_description(self):
        return self._task_description

    @property
    def data_builder(self):
        return self._data_builder

    @property
    def output_path(self) -> str:
        return self._output_path

    @property
    def num_outputs_to_generate(self):
        return self._num_outputs_to_generate

    def is_complete(self):
        return len(self.machine_data) > self.num_outputs_to_generate

    def _get_default_output_path(self):
        path_components = []
        path_components.append(self._output_dir)
        path_components.append(self._name)
        path_components.append("generated_instructions.jsonl")
        return os.path.join(*path_components)

    def save_data(self, new_data: List[SdgData], output_path: str = None) -> None:
        output_path = self._output_path if output_path is None else output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "a") as f:
            for d in new_data:
                f.write(json.dumps(d.to_output_dict()) + "\n")

    def load_data(self, output_path: str = None) -> List[SdgData]:
        output_path = self._output_path if output_path is None else output_path
        with open(output_path, "r") as f:
            try:
                return [
                    self.instantiate_example(**json.loads(l.strip()))
                    for l in f.readlines()
                ]
            except ValueError:
                return []

    def clear_data(self, output_path: str = None) -> List[SdgData]:
        output_path = self._output_path if output_path is None else output_path
        if os.path.exists(output_path):
            os.remove(output_path)


T = TypeVar("T")


def group_data_by_task(data_list: List[T]) -> List[List[T]]:
    tasks = set([data_item.task_name for data_item in data_list])
    return [
        [data_item for data_item in data_list if data_item.task_name == task]
        for task in tasks
    ]