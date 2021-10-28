# Caching task results in the file system

The python module `bandsaw.advices.cache` contains the `CachingAdvice` class, which
allows to store results of already calculated tasks in the file system so that they
can be reused in later executions.

## Configuration

### directory (str)
The directory, where the results will be stored. If the directory doesn't exist,
it will be created the first time, a result is being stored.

## Example configuration

```python
import bandsaw.advices.cache

configuration = bandsaw.Configuration().add_advice_chain(
    bandsaw.advices.cache.CachingAdvice(
        directory='/my/cache/directory',
    )
)
```
