from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import Any, Type, TypeVar

from .config import SIDA_COORDINATOR_MODULES_ENV_KEY

T = TypeVar("T")


def load_assets[T](instance_type: Type[T]) -> list[T]:
    assets: list[T] = []
    module_names = os.environ[SIDA_COORDINATOR_MODULES_ENV_KEY].split(",")

    logging.info("##########################################################")
    logging.info(f"trying to import instances of {instance_type}")
    logging.info("##########################################################")

    for module_name in module_names:
        logging.info(f"current module name {module_name}")
        module = import_module(module_name, __name__)
        for item in dir(module):
            if item == "__builtins__":
                continue
            if item == "__cached__":
                continue
            if item == "__path__":
                continue
            if item == "__doc__":
                continue
            if item == "__spec__":
                continue
            if item == "__name__":
                continue
            if item == "__loader__":
                continue
            if item == "__file__":
                continue
            if item == "__package__":
                continue
            element: Any = getattr(module, item)

            if isinstance(element, (list, tuple, set)):
                for entry in element:  # type: ignore[var-annotated]
                    if isinstance(entry, instance_type):
                        assets.append(entry)
            if isinstance(element, dict):
                for entry in element.values():  # type: ignore[var-annotated]
                    if isinstance(entry, instance_type):
                        assets.append(entry)
            if isinstance(element, instance_type):
                assets.append(element)
    return assets
