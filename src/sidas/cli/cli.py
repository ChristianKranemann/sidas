#!/usr/bin/env python3

import logging

import click

from ..core import (
    AssetId,
    Coordinator,
)

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    pass


@cli.command()
def run() -> None:
    coordinator = Coordinator.load_coordinator()
    coordinator.run()


@cli.command()
@click.argument("asset")
def materialize(asset: str) -> None:
    asset_id = AssetId(asset)
    coordinator = Coordinator.load_coordinator()
    coordinator.materialize(asset_id)


if __name__ == "__main__":
    cli()
