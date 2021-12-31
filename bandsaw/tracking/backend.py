"""Interface for tracking backends"""


class Backend:
    """Base class for backend implementations"""

    def track_run(self, ids, run_info):
        """
        Track a run

        Args:
            ids (bandsaw.session.Ids): Ids where the run was first used.
            run_info (Dict[str,Any]): A dictionary containing tracking information for
                this run.
        """

    def track_distribution_archive(self, distribution_archive):
        """
        Track a distribution archive.

        Args:
            distribution_archive (bandsaw.distribution.DistributionArchive): The
                archive which should be tracked.
        """

    def track_task(self, ids, task_info):
        """
        Track a task.

        Args:
            ids (bandsaw.session.Ids): Ids where task was first used.
            task_info (Dict[str,Any]): A dictionary containing tracking information
                for a task.
        """

    def track_execution(self, ids, execution_info):
        """
        Track an execution.

        Args:
            ids (bandsaw.session.Ids): Ids where task was first used.
            execution_info (Dict[str,Any]): A dictionary containing tracking
                information for the execution.
        """

    def track_session(self, ids, session_info):
        """
        Track a session.

        Args:
            ids (bandsaw.session.Ids): Ids where task was first used.
            session_info (Dict[str,Any]): A dictionary containing tracking
                information for this session.
        """

    def track_result(self, ids, result_info):
        """
        Track the result of a session.

        Args:
            ids (bandsaw.session.Ids): Ids where task was first used.
            result_info (Dict[str,Any]): A dictionary containing tracking
                information for this result.
        """

    def track_attachments(self, ids, attachments):
        """
        Track the attachments of a session.

        Args:
            ids (bandsaw.session.Ids): Ids where task was first used.
            attachments (bandsaw.session.Attachments): An instance of `Attachments`
                which gives access to the files that were attached to a session.
        """
