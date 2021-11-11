# Running tasks on remote machines using SSH

The [`bandsaw.advices.ssh.SshAdvice`](../../api/#bandsaw.advices.ssh.SshAdvice)
allows to run tasks on a different machine than where the workflow defining the whole
process is being run. Internally it uses the ssh command line tools to transfer the
task over to another machine, spawns a new python interpreter, runs the task and
returns the result back to the calling machine.

## Configuration

### directory (str)
The directory, where the temporary files like the session or the result will be stored
before transferring them to or from a remote machine. If the directory doesn't exist,
it will be created when first being used. If no directory is given, a temporary
directory is used.

### add_remote()
Defining the remote machine is done by calling
[`add_remote(remote)`](../../api/#bandsaw.advices.ssh.SshAdvice.add_remote)
on the advice and providing an instance of the
[`bandsaw.advices.ssh.Remote`](../../api/#bandsaw.advices.ssh.Remote) class. The
class contains all the information necessary for executing a task remotely and is
initialized using its constructor:

#### host
The hostname of the machine, where the tasks should be run. It could be an ip address,
too, but it must be set.

#### port
The port to which SSH should connect to as `int`. If not set, the default port 22 for
ssh is used.

#### key_file
`key_file` should be the path to file, which contains the key that will be used for
authentication. If this is not configured, ssh will use the default.

!!! warning "Warning"
    Due to its automatic nature, bandsaw doesn't know how to handle passwords.
    Therefore, it doesn't support authentication via password or keyfiles that use a
    passphrase (without using a ssh-agent).

#### user
The username of the user, that is being used on the remote machine. If this is not
configured, bandsaw uses the name of the local user, that runs the python interpreter.

#### interpreter
An instance of [`bandsaw.interpreter.Interpreter`](../../api/#bandsaw.interpreter.Interpreter)
which contains the path on the remote machine to a python interpreter as well as
additions to the PYTHONPATH on the remote machine, e.g. if non-standard libraries are
used.

#### directory
Path to a directory on the remote machine, where temporary files will be stored. If
not specified, '/tmp' is as default.

## Example configuration with a single remote

```python
import bandsaw
from bandsaw.advices.ssh import SshAdvice, Remote

configuration = bandsaw.Configuration().add_advice_chain(
    SshAdvice().add_remote(
        Remote(
            host='my.remote.machine.tld',
            port='22',
            key_file='/path/to/my/key',
            user='my_remote_user',
            interpreter=bandsaw.Interpreter(
                path=[],
                executable='/my/remote/path/to/python3',
            ),
            directory='/my/remote/directory',
        ),
    ),
)
```

## Example configuration with multiple remotes

The advice supports multiple different remote machines that can be  used for executing
tasks. Each definition of a remote machine has to be added by a `add_remote(remote)`
call to the `SshAdvice` class:

```python
import bandsaw
from bandsaw.advices.ssh import SshAdvice, Remote

configuration = bandsaw.Configuration().add_advice_chain(
    SshAdvice().add_remote(
        Remote(
            host='my.remote.machine.tld',
            port='22',
            key_file='/path/to/my/key',
            user='my_remote_user',
            interpreter=bandsaw.Interpreter(
                path=[],
                executable='/my/remote/path/to/python3',
            ),
            directory='/my/remote/directory',
        ),
        name='remote-1',
    ).add_remote(
        Remote(
            host='my.other.machine.tld',
            port='2222',
            key_file='/different/key',
            user='my_other_user',
            interpreter=bandsaw.Interpreter(
                path=[],
                executable='/my/remote/path/to/python3',
            ),
            directory='/tmp/directory',
        ),
        name='remote-2',
    ),
)
```

Besides the `Remote` instance, the `add_remote()` method takes an additional argument
`name` which allows referring to a specific remote configuration. If no name is given
'default' is used.

Which remote configuration should be used can be configured per task. Each task
definition can take additional task arguments in form of keyword arguments:

```python
@bandsaw.task(ssh={'remote': 'remote-2'})
def greet(recipient):
    return f"Hello {recipient}"

```

The `SshAdvice` expects a dictionary for the task keyword argument `ssh`. This dict
contains then the task specific SSH configuration. Currently, the only supported key
is 'remote' whose value must be the name of one of the remotes defined by
`add_remote()`. If no task keyword argument 'ssh' is given, or its value doesn't
contain 'remote', the default name for the remote is 'default'.
