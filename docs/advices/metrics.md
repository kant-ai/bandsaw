# Gathering metrics for task executions

In order to get better insight into bottlenecks and consumption of computing
resources Bandsaw provides the
[`bandsaw.advices.metrics.MetricsAdvice`](../../api/#bandsaw.advices.metrics.MetricsAdvice),
that allows to track metrics like CPU load or memory usage while tasks are executed.
This enables developers to discover hotspots and bottlenecks within their workflow
and identify optimization potential.

The advice uses the [`Multimeter`](https://docs.kant.ai/multimeter/) library for
collecting the values. It uses the library to write the metrics into a file and
attaches the result under the name 'metrics.<ext>' to the session. The extension
of the filename depends on the file format that is being configured.

## Configuration

### meter (multimeter.Multimeter)
`meter` is a required positional argument. It contains the pre-configured Multimeter
instance that will be used for measuring the metrics during task execution.
The `Multimeter` is configured by its
[constructor](https://docs.kant.ai/multimeter/latest/api/#multimeter.multimeter.Multimeter.__init__).
In order to gather any value, it must be given atleast 1 probe, e.g. `ResourceProbe`.
For more information on how it is being used, please refer to
[https://docs.kant.ai/multimeter/latest/user_guide/#multimeter](https://docs.kant.ai/multimeter/latest/user_guide/#multimeter).

### directory (str)
The directory where the files with the gathered metrics are written to. For each
session a separate file is being created with the name <session-id>.<ext> where
'<ext>' depends on the file format. If this directory is not set or `None`, the
files are written to the session specific temporary directory.

### file_format (multimeter.FileFormat)
The file format which is used for writing the results. Multimeter supports multiple
file formats that can be used. Defaults to `multimeter.JsonFormat`.
For more information refer to
[https://docs.kant.ai/multimeter/latest/storages/file/](https://docs.kant.ai/multimeter/latest/storages/file/).

## Example configuration

```python
import bandsaw
import multimeter

from bandsaw.advices.metrics import MetricsAdvice

configuration = bandsaw.Configuration().add_advice_chain(
    MetricsAdvice(
        multimeter.Multimeter(multimeter.ResourceProbe()),
        directory='/my/metric/directory',
        file_format=multimeter.JsonFormat(),
    )
)
```
