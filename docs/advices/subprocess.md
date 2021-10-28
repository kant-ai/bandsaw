# Running tasks in subprocesses

The python module `bandsaw.advices.subprocess` contains the `SubprocessAdvice` class,
which allows running task computations in a subprocess. Additionally, the subprocess
can use a different python interpreter than the one, that is used for running the rest
of the recipe. This can be used for bringing together tasks with conflicting
dependencies or different python versions.

## Configuration

### directory (str)
The directory, where the intermediate results and temporary data to communicate with
the subprocess will be written to. Can be `None`, in which case a temporary directory
will be used.

### interpreter (bandsaw.interpreter.Interpreter)
The python interpreter to use for executing the task. If `None`, the same interpreter
will be used, that is executing the workflow.

## Example configuration

```python
import bandsaw.advices.subprocess
import bandsaw.interpreter

configuration = bandsaw.Configuration().add_advice_chain(
    bandsaw.advices.subprocess.SubprocessAdvice(
        directory='/my/subprocess/directory',
        interpreter=bandsaw.interpreter.Interpreter(
            path=['/my/other/interpreter', '/python/path'],
            executable='/path/to/the/other/python',
        )
    )
)
```
