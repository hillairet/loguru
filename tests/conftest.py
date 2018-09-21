import loguru
import logging
import itertools
import pytest
import py
import os
import subprocess

default_levels = loguru._logger.Logger._levels.copy()

@pytest.fixture(autouse=True)
def reset_logger():
    def reset():
        loguru.logger.stop()
        loguru.logger.__init__({}, None, False, False, False, 0)
        loguru._logger.Logger._levels = default_levels.copy()
        loguru._logger.Logger._min_level = float('inf')
        loguru._logger.Logger._extra_class = {}
        loguru._logger.Logger._handlers = {}
        loguru._logger.Logger._handlers_count = itertools.count()
        loguru._logger.Logger._enabled = {}
        loguru._logger.Logger._activation_list = []
        logging.Logger.manager.loggerDict.clear()
        logging.root = logging.RootLogger(logging.WARNING)

    reset()
    yield
    reset()

@pytest.fixture
def writer():

    def w(message):
        w.written.append(message)

    w.written = []
    w.read = lambda: ''.join(w.written)
    w.clear = lambda: w.written.clear()

    return w

@pytest.fixture
def pyexec(tmpdir):
    file = tmpdir.join("test.py")
    loguru_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    loguru_config = ('import sys;'
                     'sys.path.append(r"' + loguru_path + '");'
                     'from loguru import logger;'
                     'logger.stop();\n')

    def pyexec(code, import_loguru=False, *, pyfile=None):
        if import_loguru:
            code = loguru_config + code
        else:
            code = "# padding\n" + code

        if pyfile is None:
            pyfile = file
        pyfile.write(code)
        process = subprocess.Popen('python %s' % pyfile.realpath(),
                                    shell=True, universal_newlines=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        return out, err

    return pyexec

@pytest.fixture
def monkeypatch_now(monkeypatch):

    def monkeypatch_now(func):
        monkeypatch.setattr(loguru._logger, 'fast_now', func)
        monkeypatch.setattr(loguru._file_sink, 'fast_now', func)

    return monkeypatch_now

@pytest.fixture
def make_logging_logger():

    def make_logging_logger(name, handler, fmt="%(message)s", level="DEBUG"):
        logging_logger = logging.getLogger(name)
        logging_logger.setLevel(level)
        formatter = logging.Formatter(fmt)

        handler.setLevel(level)
        handler.setFormatter(formatter)
        logging_logger.addHandler(handler)

        return logging_logger

    yield make_logging_logger
