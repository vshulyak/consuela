import abc
import asyncio

from datetime import datetime, time, timedelta

from itertools import chain


class SchedulerTask(abc.ABC):
    """
    A base class for all the tasks
    """
    is_recurring = False

    due_task_execution_timeout = -30  # Seconds

    def __init__(self, publisher):
        self.publisher = publisher
        self.last_run = None

    @abc.abstractmethod
    def run(self):
        raise NotImplemented

    @asyncio.coroutine
    def execute(self):
        """
        Executes the task
        """
        # TODO: main concern: should task know how to execute itself or should it be abstracted?
        # TODO: and also last_run logic... should it be moved outside?
        # TODO: one of the ways is to make a very simple class with only run() to override and all
        #  other logic is in other classes
        gen = self.run()
        # silently ignore None and non-coroutines
        if gen and asyncio.iscoroutine(gen):
            yield from gen
            self.last_run = datetime.now()


class RunEveryTask(SchedulerTask):
    """
    Runs at a particular time every day:

    `run_every` should be a timedelta. Example:

        timedelta(seconds=7)

    """
    is_recurring = True

    def __init__(self, publisher, run_every):
        super(RunEveryTask, self).__init__(publisher)
        self.run_every = run_every

    def next_time_due(self):

        assert isinstance(self.run_every, timedelta)

        if not self.last_run:
            self.last_run = datetime.now()

        next_run = (self.last_run + self.run_every).timestamp() - datetime.now().timestamp()
        return next_run


class RunAtTimeTask(SchedulerTask):
    """
    Runs at a particular time every day:

    `run_at` should be datetime. Example:

        datetime.now() + timedelta(seconds=7)

    """
    run_at = None  #
    is_recurring = True

    def __init__(self, run_at, publisher):
        super(RunAtTimeTask, self).__init__(publisher)
        self.run_at = run_at

    def next_time_due(self):

        assert isinstance(self.run_at, time)

        next_run = self.run_at.timestamp() - datetime.now().timestamp()

        if next_run < self.due_task_execution_timeout or \
                (self.last_run is not None and self.last_run.date() == datetime.now().date()):
            return None
        return next_run


class RunAtDateTimeTask(SchedulerTask):
    """
    Runs at a particular datetime once.

    `run_at` should be a datetime object. Example:

        (datetime.now() + timedelta(seconds=10))

    """
    is_recurring = False

    def __init__(self, run_at, publisher):
        super(RunAtDateTimeTask, self).__init__(publisher)

        assert isinstance(run_at, datetime)

        self.run_at = run_at

    def next_time_due(self):

        next_run = self.run_at.timestamp() - datetime.now().timestamp()

        is_too_old_to_execute = next_run < self.due_task_execution_timeout
        has_run_today_already = self.last_run is not None \
                                and self.last_run.date() == datetime.now().date()

        if is_too_old_to_execute or has_run_today_already:

            # deregister task
            return None

        return next_run


class Scheduler(object):
    """
    Schedules tasks to be executed via aio look
    """
    tick_max_sleep_seconds = 60 * 60

    def __init__(self):
        self.task_pool = []
        self.next_cycle_future = asyncio.Future()

    @asyncio.coroutine
    def run(self):
        """
        Schedules execution of all the tasks which are due, waiting
        for new tasks otherwise

        :return:
        """
        while True:

            next_action_times = []

            # we need a copy since we delete tasks in the loop
            # more readable than moving removal outside imo
            for task in self.task_pool[:]:

                next_due_time = task.next_time_due()

                print("next due time for {task} is {time}".format(task=task, time=next_due_time))

                # signals to delete the task
                if next_due_time is None:
                    self.task_pool.remove(task)
                    continue

                if next_due_time <= 0:

                    # try except execute. If it fails, do not unregister
                    asyncio.async(task.execute())

                else:
                    next_action_times.append(next_due_time)

            sleep_till_next_time_seconds = min(chain(next_action_times, [self.tick_max_sleep_seconds]))

            if self.next_cycle_future.done():
                self.next_cycle_future = asyncio.Future()

            try:
                print("Sleeping {seconds}".format(seconds=sleep_till_next_time_seconds))
                yield from asyncio.wait_for(self.next_cycle_future, timeout=sleep_till_next_time_seconds)
            except asyncio.TimeoutError:
                pass

    def register_task(self, task):
        """
        Registers a new task and wakes up the loop

        :param task: task to execute
        :return:
        """
        assert isinstance(task, SchedulerTask)

        self.task_pool.append(task)
        self.next_cycle_future.set_result(None)

    def has_tasks(self):
        return bool(self.task_pool)