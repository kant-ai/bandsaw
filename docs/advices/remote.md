# Running tasks on remote machines using SSH (In development)

The `bandsaw.advices.remote.SshAdvice` allows to run tasks on a different machine than
where the workflow defining the whole process is being run.
Internally it uses [`paramiko`](https://www.paramiko.org/) to transfer the task over
to another machine, spawns a new python interpreter, runs the task and returns the
result back to the calling machine.

This feature is currently in development and will be released in November 2021.
