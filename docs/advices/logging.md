# Keep logs of task executions

The python module `bandsaw.advices.log` contains the
[`LoggingAdvice`](../../api/#bandsaw.advices.log.LoggingAdvice) class, which
allows to keep the log output of task executions as attachment in a session.

The advice adds an own `Handler` to the `logging.root` logger and stores log
messages emitted during task execution in its own log file. The handler can use
its own formatter and supports using a different logging level. The log messages
are written into an attachment in the session with the name `session.log`.

## Configuration

### level (int)
The level of the log messages, that should be kept. If not set or set to `None`, which
messages are kept depends only on the configured level of the used loggers.

### formatter (logging.Formatter)
The formatter to use for writing our the individual log messages. This defaults to an
own [`bandsaw.advices.log.JsonFormatter`](../../api/#bandsaw.advices.log.JsonFormatter)
that writes log messages as individual json objects (one per line), but custom
formatter can be used as well.

## Example configuration

```python
import logging

import bandsaw.advices.log


configuration = bandsaw.Configuration().add_advice_chain(
    bandsaw.advices.log.LoggingAdvice(
        level=logging.INFO,
    )
)
```

## JsonFormatter

The `JsonFormatter` writes log messages as line-wise json that makes its easier to
process the logs later-on without having to parse user-defined text formats.

### Description of the individual fields
| Field       |  Type  | Optional | Description                                                                     |
|-------------|:------:|---------:|---------------------------------------------------------------------------------|
| timestamp   | string |       no | Times are ISO-Format and always in UTC.                                         |
| logger      | string |       no | The name of the logger that created the message.                                |
| level       | string |       no | The level of the message (usually INFO, DEBUG, WARN, ERROR, but can be custom). |
| message     | string |       no | The text content of the log message.                                            |
| threadId    |  int   |       no | The ID of the thread where the message was emitted.                             |
| threadName  | string |       no | The name of the thread where the message was emitted.                           |
| processId   |  int   |       no | The process ID of the process which emitted the message.                        |
| processName | string |       no | The name of the process which emitted the message.                              |
| module      | string |       no | The name of the module based on the filename.                                   |
| function    | string |       no | Name of the function which emitted the log message.                             |
| path        | string |       no | Path to the python file where the message originated.                           |
| line_no     |  int   |       no | Number of the line where the log message was created.                           |
| traceback   | string |      yes | Stacktrace of the exception. (missing if no exception is logged)                |
| exception   | string |      yes | String representation of the exception. (missing if no exception is logged)     |
| sessionId   | string |      yes | (bandsaw specific) ID of the session in which the log message was created.      |
| runId       | string |      yes | (bandsaw specific) ID of the run in which the log message was created.          |
| taskId      | string |      yes | (bandsaw specific) ID of the task which was executed.                           |
| executionId | string |      yes | (bandsaw specific) ID of the execution of the task.                             |



### Example of normal log message

```json
{
  "timestamp": "2021-12-22T14:13:30.840811+00:00",
  "logger": "bandsaw.advices.metrics",
  "level": "INFO",
  "message": "Measurement id ea1a9e07d0c48896 with tags {'run_id': '55e85c2e-6331-11ec-8e2d-48f17f64520d', 'task_id': 'd24d5c98e4f63e66', 'execution_id': 'dd999d9ace267e13', 'session_id': 'ea1a9e07d0c48896'}",
  "threadId": 140239061456704,
  "threadName": "MainThread",
  "processId": 16365,
  "processName": "MainProcess",
  "module": "metrics",
  "function": "before",
  "path": "/home/bandsaw/dd999d9ace267e13/distribution-zy0tybls.pyz/bandsaw/advices/metrics.py",
  "line_no": 50,
  "sessionId": "ea1a9e07d0c48896",
  "runId": "55e85c2e-6331-11ec-8e2d-48f17f64520d",
  "taskId": "d24d5c98e4f63e66",
  "executionId": "dd999d9ace267e13"
}
```


### Example of log message with exception

```json
{
  "timestamp": "2021-12-22T14:18:31.821401+00:00",
  "logger": "my.logger",
  "level": "ERROR",
  "message": "Error greeting",
  "threadId": 140626754463552,
  "threadName": "MainThread",
  "processId": 16632,
  "processName": "MainProcess",
  "module": "demo",
  "function": "greet",
  "path": "/home/bandsaw/76560cb43662cc8f/distribution-f_say9mc.pyz/demo.py",
  "line_no": 20,
  "traceback": "File \"/home/bandsaw/76560cb43662cc8f/distribution-f_say9mc.pyz/demo.py\", line 18, in greet\n    raise ValueError(os.getpid())",
  "exception": "ValueError: 16632",
  "sessionId": "2573b136fd2b4f8e",
  "runId": "0939cef2-6332-11ec-8e2d-48f17f64520d",
  "taskId": "0d268ac06a82654e",
  "executionId": "76560cb43662cc8f"
}
```