import logging
import socket
import threading
import time
from unittest import mock
from wsgiref.simple_server import make_server

import flask

logger = logging.getLogger(__name__)


class HttpServiceMock:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = flask.Flask("target")
        self.server = make_server(self.host, self.port, self.app)
        self.server_thread = threading.Thread(target=self.server.serve_forever)

    def _wait_for_service(self):
        elapsed_time = 0
        start_time = time.time()
        while elapsed_time < 5:
            s = socket.socket()
            s.settimeout(1)
            try:
                s.connect(self.server.server_address)
            except (ConnectionRefusedError, ConnectionAbortedError):
                elapsed_time = time.time() - start_time
                s.close()
            else:
                s.close()
                break
        else:
            raise TimeoutError(f"{self.__class__.__name__} "
                               f"couldn't be set up before test.")

    def __enter__(self):
        logger.debug(f"Starting {self}...")
        self.server_thread.start()
        self._wait_for_service()
        logger.debug(f"{self} has been started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Terminating {self}...")
        self.server.shutdown()
        self.server_thread.join()
        self.server.server_close()
        logger.debug(f"{self} has been terminated.")

    def get_route_mock(self, rule, **options):
        mocked_view = mock.MagicMock(name=rule, spec=lambda: None)
        self.app.add_url_rule(rule,
                              endpoint=rule,
                              view_func=mocked_view,
                              **options)
        logger.debug(f"{self} mock for '{rule}' has been added.")
        return mocked_view

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(host='{self.host}', port={self.port})"
        )