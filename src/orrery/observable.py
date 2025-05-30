import weakref
from collections import namedtuple


class ObserverList(object):
    """Class for managing observers and sending notifications for events

    Makes special use of WeakKeyDictionary and WeakMethod so that the
    Observable won't prevent observers from being destroyed, and if an
    observer is destroyed it will automatically be removed from the observers
    """

    CallbackArgs = namedtuple('CallbackArgs', ['callback', 'kwargs'])

    def __init__(self):
        # Create dictionary of observing objects to their callback.
        # The WeakKeyDictionary ensures that if the observer object is
        # destroyed, it is automatically removed from the observer dictionary
        self._observers = weakref.WeakKeyDictionary()

    def add_observer(self, callback, **kwargs):
        """Add an observer to receive notification events

        Args:
            callback: bound method which will receive the callbacks
            kwargs: additional arguments which will be passed to the callback
        """

        # Wrap the callback (which is a bound method) as a WeakMethod,
        # otherwise the bound method would prevent the observer object from
        # being destroyed
        callback_id = callback.__self__
        weak_callback = weakref.WeakMethod(callback)
        self._observers[callback_id] = self.CallbackArgs(
            callback=weak_callback, kwargs=kwargs)
        return callback_id

    def remove_observer(self, callback_id):
        """Remove an observer previously added with add_observer()

        Args:
            callback_id: the callback id returned by the add_observer() call
        """
        if callback_id not in self._observers:
            raise RuntimeError('Unknown callback ID')
        del self._observers[callback_id]

    def notify(self, **event_args):
        """Trigger a callback on all observers which are still in existence"""
        for callback_args in self._observers.values():
            callback_args.callback()(**event_args, **callback_args.kwargs)


class Event(str):
    """Identifies an event that can be raised by an Observable object"""


class Observable:
    """Base class for objects which can send notifications to observers.

    Maintains a dictionary of event types to ObserverList objects
    """

    def __init__(self):
        # Each event has its own unique ObserverList.
        self._observer_lists: dict[Event, ObserverList] = {}

    def add_observer(self, event: Event, callback, **kwargs):
        """Add an observer to receive notifications for the specified event

        Args:
            event: describes a unique event generated by this object
            callback: bound method which will receive the callbacks
            kwargs: additional arguments to be passed to the callbacks - these
                   are added to the arguments passed in through the call to
                   notify()

        Returns:
            An id which can be used to remove the callback if necessary
        """

        return self._get_observer_list(event).add_observer(callback, **kwargs)

    def remove_observer(self, event: Event, callback_id):
        self._get_observer_list(event).remove_observer(callback_id)

    def notify(self, event: Event, **event_args):
        """Trigger a callback on all observers for this event

        Args:
            event: describes a unique event generated by this object
            event_args: named arguments to be passed to pass to callbacks
        """
        self._get_observer_list(event).notify(**event_args)

    def _get_observer_list(self, event: Event) -> ObserverList:
        """Return ObserverList for the specified event, creating if
        necessary"""
        if event not in self._observer_lists:
            self._observer_lists[event] = ObserverList()
        return self._observer_lists[event]
