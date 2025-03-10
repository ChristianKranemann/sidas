#!/usr/bin/env python3

import logging
import time

import click

from ..core import (
    AssetId,
    CoordinateUsecase,
    Coordinator,
    MaterializeUsecase,
    MaterializeUsecaseInput,
)

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    pass


@cli.command()
def coordinate() -> None:
    coordinator = Coordinator.load_coordinator()
    usecase = CoordinateUsecase(coordinator)
    usecase()


@cli.command()
def run() -> None:
    coordinator = Coordinator.load_coordinator()
    coordinator.validate()
    usecase = CoordinateUsecase(coordinator)
    while True:
        usecase()
        time.sleep(10)


@cli.command()
@click.argument("asset")
def materialize(asset: str) -> None:
    coordinator = Coordinator.load_coordinator()
    asset_id = AssetId(asset)
    usecase = MaterializeUsecase(coordinator)
    data = MaterializeUsecaseInput(asset_id)
    usecase(data)


if __name__ == "__main__":
    cli()
