from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import Type

from .config import SIDA_COORDINATOR_MODULES_ENV_KEY


def load_assets[T](instance_type: Type[T]) -> list[T]:
    assets = []
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
            element = getattr(module, item)
            # logging.info(f"current element {item} of type {type(element)}: {element} ")
            if isinstance(element, list):
                for e in element:
                    if isinstance(e, instance_type):
                        assets.append(e)
            if isinstance(element, instance_type):
                assets.append(element)
    return assets
