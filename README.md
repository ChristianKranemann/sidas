# sida

```python
import random
import statistics

from sida.extensions import REGISTER_ASSETS_IN_MEMORY
from sida.extensions.assets import DownstreamAsset, ScheduledAsset
from sida.extensions.coordinators import SimpleCoordinator


class Numbers(ScheduledAsset[list[float]]):
    cron_expression = "0 0 * * *"

    def transformation(self) -> list[float]:
        return [random.normalvariate() for i in range(10)]


class Mean(DownstreamAsset[float]):
    def transformation(self, n: Numbers) -> float:
        return statistics.mean(n.data)


class Variance(DownstreamAsset[float]):
    def transformation(self, n: Numbers) -> float:
        return statistics.variance(n.data)


class Report(DownstreamAsset[str]):
    def transformation(self, m: Mean, v: Variance) -> str:
        return f"Todays random numbers: mean {m.data} and var {v.data}"


# define the Persisters
REGISTER_ASSETS_IN_MEMORY(Numbers, Mean, Variance, Report)

# instantiate the assets
n = Numbers()
m = Mean()
v = Variance()
r = Report()

# instantiate a cooridnator
coordinator = SimpleCoordinator()
```

```python
class Numbers(ScheduledAsset[list[float]]):
    cron_expression = "0 0 * * *"

    def __init__(self, resource: File)
    def transformation(self) -> list[float]:
        return [random.normalvariate() for i in range(10)]


def test_report() -> None:
    m = Mean()
    m.data = 0.0

    v = Variance()
    v.data = 1.1

    r = Report()
    assert r.transformation() == "Todays random numbers: mean 0.0 and var 1.0"
```
