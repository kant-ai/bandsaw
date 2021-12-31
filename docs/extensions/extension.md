# Extensions

Besides advices, bandsaw allows to extend its functionality by using its
[`bandsaw.extensions.Extension`](../../api/#bandsaw.extensions.Extension) concept.
The base class defines a set of methods, that can be implemented to be notified
by bandsaw about certain events.

## Interface
At the moment the base class defines the following methods:

### on_init()

```python
def on_init(self, configuration):
    ...
```
[`on_init()`](../../api/#bandsaw.extensions.Extension.on_init) is called by bandsaw
when the configuration, that contains this extension is completely initialized. This
happens only **once** per run (per interpreter) and is done before every other
extension methods, so it can be used for one-time setting up the extension.

!!! warning Warning
    Even though an extension is initialized only once in a single interpreter, it can
    be called multiple times in multiple python interpreters, e.g. when a session is
    transferred to a different machine.

### on_session_created()

```python

def on_session_created(self, session):
    ...
```

[`on_session_created()`](../../api/#bandsaw.extensions.Extension.on_session_created) is
called when bandsaw created a new session for executing a task. The session is given
to the extension and can be modified by it e.g. by setting additional context. The
task of the session has not been computed at this time and neither were advices applied.
Methods  that change the state of session in relation to its execution, like
`initiate()`, `proceed()` or `conclude()` must not be called by an extension.

### on_session_finished()

```python
def on_session_finished(self, session):
    ...
```

[`on_session_finished()`](../../api/#bandsaw.extensions.Extension.on_session_finished)
is called when bandsaw has finished executing a task. The result has been computed
and all advices have been applied at this point. The extension can use the given
session, to extract information about the execution, but modifications of the
session don't have any effect.
Methods that change the state of session in relation to its execution, like
`initiate()`, `proceed()` or `conclude()` must not be called by an extension.


## Configuration

All extensions have to be added to the bandsaw configuration in order to be used.

```python
import bandsaw

configuration = bandsaw.Configuration()
...  # Here the rest of the configuration and advice chains
configuration.add_extension(MyExtension(possible='config'))
```
