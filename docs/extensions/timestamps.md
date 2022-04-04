# Adding timestamps when a task was executed.

Often it is useful to know the timestamps when some tasks were executed. This can be
easily added to the session context and therefore to the tracking information by using
the
[`bandsaw.timestamps.TimestampsExtension`](../../api/#bandsaw.timestamps.TimestampsExtension).

The following timestamps are currently collected:

  - `'timestamps.session_created'`: The time when the session was initially created.
  - `'timestamps.session_finished'`: The time when the session was finished.
  - `'timestamps.before_task'`: The time after applying all `before()` advices and
    before executing the task.
  - `'timestamps.before_task'`: The time before applying all `after()` advices and
    after executing the task.


## Configuration

Nothing to configure.

## Example configuration

```python
import bandsaw

from bandsaw.timestamps import TimestampsExtension

configuration = bandsaw.Configuration()
configuration.add_extension(TimestampsExtension())
```
