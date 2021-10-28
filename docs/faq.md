
# FAQ

## Why do I have to configure bandsaw in a separate module?

Since bandsaw can be integrated in arbitrary python scripts, we need to make sure that as
soon as the `bandsaw.task` decorator is used first time, it is properly configured. By using
a separate module, that bandsaw can import as needed, the library doesn't depend on the user
setting the configuration upfront.