import asyncio

class EventManager:
    def __init__(self):
        self.subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    def broadcast(self, event: dict):
        for queue in self.subscribers:
            queue.put_nowait(event)


broadcaster = EventManager()