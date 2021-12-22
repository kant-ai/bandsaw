# Getting started

## Install the library

Install the latest version from [PyPI](https://pypi.org/project/bandsaw/)
using pip:

```bash
pip install bandsaw
```

## Define the individual tasks of your workflow

Import the `@task` decorator from the `bandsaw` package and decorate a function
with it:

```python
import bandsaw

...

@bandsaw.task
def my_function(x):
    ...
    return x

```

## Configure bandsaw

Create a new python module `bandsaw_config` and add first advice that just adds some
additional logging when a task is executed:

```python
import bandsaw

configuration = bandsaw.Configuration().add_advice_chain(
    bandsaw.advices.log.LoggingAdvice(),
)

```

## Run your workflow

When you now run your workflow, `bandsaw` intercepts the execution of `my_function` and
its `LoggingAdvice` prints out additional log messages `before()` and `after()` it, e.g.:

```bash
$ python my_script.py
...
2021-10-27 13:13:51,940  2290 bandsaw.advices.log INFO: BEFORE 0d268ac0..4213:76560cb4..a37d with context {}
...
2021-10-27 13:13:52,127  2290 bandsaw.advices.log INFO: AFTER 0d268ac0..4213:76560cb4..a37d with context {}
...
```

The log messages contain the `task_id` (0d268ac0..4213), which is derived from the code
that is decorated, and the `run_id` (76560cb4..a37d), derived from the arguments that
`my_function` was called with.


## Where to go from here?

Read the [user guide](../user_guide/) for some more in-depth explanation about bandsaw and
its concepts.

Alternatively, bandsaw brings with it a couple of useful advice classes, that can be used
just by adding them to its configuration:

- Running tasks in a subprocess or with a different python interpreter:
    [`bandsaw.advices.subprocess.SubprocessAdvice`](../advices/subprocess/)
- Caching the result of a task:
    [`bandsaw.advices.cache.CachingAdvice`](../advices/caching/)
- Running tasks on a different machine using SSH:
    [`bandsaw.advices.remote.SshAdvice`](../advices/remote/)
- Capturing the resource usage of a task:
    [`bandsaw.advices.metrics.MetricsAdvice`](../advices/metrics/)
- Running tasks on asynchronously (Coming soon):
    [`bandsaw.advices.async.AsyncAdvice`](../advices/async/)
- Creating your own advice:
    [How to write your own advice?](../user_guide/#implementing-custom-advices)
