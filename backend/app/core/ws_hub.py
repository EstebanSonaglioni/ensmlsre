from collections import defaultdict

from fastapi import WebSocket


class Hub:
    def __init__(self) -> None:
        self._sockets: dict[int, set[WebSocket]] = defaultdict(set)
        self._watch: dict[int, set[int]] = defaultdict(set)
        self._socket_watch: dict[WebSocket, set[int]] = defaultdict(set)
        self._product_watch: dict[int, set[int]] = defaultdict(set)
        self._socket_products: dict[WebSocket, set[int]] = defaultdict(set)

    def connect(self, user_id: int, ws: WebSocket) -> None:
        self._sockets[user_id].add(ws)

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        self._sockets[user_id].discard(ws)
        watched = list(self._socket_watch.get(ws, ()))
        self._socket_watch.pop(ws, None)
        for sell_id in watched:
            still = any(
                sell_id in self._socket_watch.get(sock, set())
                for sock in self._sockets.get(user_id, ())
            )
            if not still:
                self._watch[sell_id].discard(user_id)
        products = list(self._socket_products.get(ws, ()))
        self._socket_products.pop(ws, None)
        for product_id in products:
            still = any(
                product_id in self._socket_products.get(sock, set())
                for sock in self._sockets.get(user_id, ())
            )
            if not still:
                self._product_watch[product_id].discard(user_id)

    def watch(self, user_id: int, sell_id: int, ws: WebSocket) -> None:
        self._watch[sell_id].add(user_id)
        self._socket_watch[ws].add(sell_id)

    def unwatch(self, user_id: int, sell_id: int, ws: WebSocket) -> None:
        self._socket_watch[ws].discard(sell_id)
        still = any(
            sell_id in self._socket_watch.get(sock, set())
            for sock in self._sockets.get(user_id, ())
        )
        if not still:
            self._watch[sell_id].discard(user_id)

    def is_watching(self, user_id: int, sell_id: int) -> bool:
        return user_id in self._watch.get(sell_id, set())

    def watch_product(self, user_id: int, product_id: int, ws: WebSocket) -> None:
        self._product_watch[product_id].add(user_id)
        self._socket_products[ws].add(product_id)

    def unwatch_product(self, user_id: int, product_id: int, ws: WebSocket) -> None:
        self._socket_products[ws].discard(product_id)
        still = any(
            product_id in self._socket_products.get(sock, set())
            for sock in self._sockets.get(user_id, ())
        )
        if not still:
            self._product_watch[product_id].discard(user_id)

    def is_watching_product(self, user_id: int, product_id: int) -> bool:
        return user_id in self._product_watch.get(product_id, set())

    def product_watchers(self, product_id: int) -> set[int]:
        return set(self._product_watch.get(product_id, ()))

    async def send_user(self, user_id: int, payload: dict) -> None:
        for ws in list(self._sockets.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(user_id, ws)


hub = Hub()
