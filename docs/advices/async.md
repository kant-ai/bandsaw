# Running tasks asynchronously (Planned)

This feature is currently not available but planned for the next future. The main
use-case for this are processes that take a long time to compute. In this case, driving
the process from the local machine and running the individual tasks synchronously would
require the developer machine to stay online the whole time to communicate the results
between the individual tasks and start the individual tasks as needed. In the
asynchronous case, all tasks are scheduled before and an executor on the individual
computation platforms takes care of running them as appropriate.

The drawback of this is, that we don't have access to the actual results within the
workflow that defines the process, but we only have futures that are passed between the
individual tasks.

This feature is planned to be available in Q1 of the year 2022.