import asyncio


class Broadcaster:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def broadcast(self, event: dict) -> None:
        for queue in self._subscribers:
            queue.put_nowait(event)


broadcaster = Broadcaster()