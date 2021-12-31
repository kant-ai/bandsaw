# Tracking the runs of the workflow

Since most of the time workflows are run multiple times, it can be useful to have a
history of past runs and their results. For this bandsaw comes with a
[`bandsaw.tracking.tracker.TrackerExtension`](../../api/#bandsaw.tracking.tracker.TrackerExtension).

This extension tracks information about the different parts of a workflow, be it the
run itself or the executed tasks with their result. This information is then send to
a backend where the data is stored and can be accessed and integrated into ones own
process and monitoring solution. Currently, the only available backend is the
[`bandsaw.tracking.filesystem.FileSystemBackend`](../../api/#bandsaw.tracking.filesystem.FileSystemBackend)
which stores the data in json format in a local directory.

## Configuration

### backend (bandsaw.tracking.backend.Backend)

`backend` is a required positional argument. It contains the pre-configured backend
instance that will be used for storing the tracking information. The object has to
inherit from type
[`bandsaw.tracking.backend.Backend`](../../api/#bandsaw.tracking.backend.Backend).

## Example configuration

```python
import bandsaw

from bandsaw.tracking.tracker import TrackerExtension
from bandsaw.tracking.filesystem import FileSystemBackend

tracking_directory = '/path/to/my/tracking/directory'

configuration = bandsaw.Configuration()
configuration.add_extension(TrackerExtension(FileSystemBackend(tracking_directory)))

```

## Backends

All backends need to inherit from the base class
[`bandsaw.tracking.backend.Backend`](../../api/#bandsaw.tracking.backend.Backend)
which defines the interface that is being expected from the tracker extension.
It defines a set of methods which take the information about the workflow:

```python

def track_run(self, ids, run_info):
    pass

def track_task(self, ids, task_info):
    pass

def track_execution(self, ids, execution_info):
    pass

def track_session(self, ids, session_info):
    pass

def track_result(self, ids, result_info):
    pass

def track_attachments(self, ids, attachments):
    pass

def track_distribution_archive(self, distribution_archive):
    pass
```

All `*_infos` that are passed over are dictionaries which contain the information.

### FileSystemBackend
The first available backend is the
[`bandsaw.tracking.filesystem.FileSystemBackend`](../../api/#bandsaw.tracking.filesystem.FileSystemBackend)
which writes the info objects to the file system. For this it takes a path to a directory
as configuration, where the individual `*-info.json` files are stored.
The directory layout follows a specific schema:

```bash
.tracking/
├── runs
│   ├── 025c8e7e-6992-11ec-8e2d-48f17f64520d
│   │   ├── 0d268ac06a82654e_76560cb43662cc8f_025c8e7e-6992-11ec-8e2d-48f17f64520d
│   │   └── run-info.json
│   └── 6aa525e8-698f-11ec-8e2d-48f17f64520d
│       ├── 0d268ac06a82654e_76560cb43662cc8f_6aa525e8-698f-11ec-8e2d-48f17f64520d
│       └── run-info.json
└── tasks
    └── 0d268ac06a82654e
        ├── 76560cb43662cc8f
        │   ├── 025c8e7e-6992-11ec-8e2d-48f17f64520d
        │   │   ├── attachments
        │   │   │   ├── metrics.json
        │   │   │   └── session.log
        │   │   ├── result-info.json
        │   │   └── session-info.json
        │   ├── 6aa525e8-698f-11ec-8e2d-48f17f64520d
        │   │   ├── attachments
        │   │   │   ├── metrics.json
        │   │   │   └── session.log
        │   │   ├── result-info.json
        │   │   └── session-info.json
        │   └── execution-info.json
        └── task-info.json
```

`tasks` contains on its level a single directory for each individual task whose name
is the `task_id` of the containing task. The task directory contains a single
`task-info.json` file, which contains a json object with some information about this
specific tasks. Every execution of this task is stored in a separate subdirectory named
with the `execution_id` of the corresponding execution. These directories contain a
`execution-info.json` file with meta information about the arguments used in this
execution and subdirectories named by the `run_id` for every specific run, where the
task was executed with these specific arguments.
This directory contains then an `session-info.json` with information about the session
of this execution and the `result-info.json` which describes the computed result.
If attachments where created by the advice chain while executing the task, those are
stored in the `attachments` directory.
Additionally, in the root of the tracking directory a directory `runs` stores
information about the executed sessions for each individual run. Every run has their
own specific directory named by its `run_id` This directory contains a `run-info.json`
and empty files named with the session_ids of every session that was computed during
this run.

#### Example JSON info file format

All `*-info.json` files have the same format and share some of their content. An example
can be found below. Most files contain only a subset of this example data.

```json
{
  "task": {
    "id": "0d268ac06a82654e",
    "definition": "demo.greet",
    "advice_parameters": {}
  },
  "execution": {
    "id": "76560cb43662cc8f",
    "arguments": [
      {
        "type": "str",
        "value": "Christoph",
        "size": "9",
        "name": "recipient"
      }
    ]
  },
  "run": {
    "id": "6aa525e8-698f-11ec-8e2d-48f17f64520d"
  },
  "configuration": "bandsaw_config",
  "distribution_archive": {
    "modules": [
      "__main__",
      "bandsaw",
      "bandsaw_config",
      "multimeter"
    ],
    "id": null
  },
  "session": {
    "id": "0d268ac06a82654e_76560cb43662cc8f_6aa525e8-698f-11ec-8e2d-48f17f64520d"
  },
  "result": {
    "value": {
      "type": "int",
      "value": "16421"
    }
  }
}
```
