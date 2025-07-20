import socket
import struct
from types import SimpleNamespace
import pytest
from ft8ctrl import Sequencer

class DummySocket:
    def __init__(self, *args, **kwargs):
        self.options = []
    def setsockopt(self, level, optname, value):
        # Record all setsockopt calls
        self.options.append((level, optname, value))
    def setblocking(self, flag):
        pass
    def bind(self, addr):
        self.bound_addr = addr

@pytest.fixture(autouse=True)
def dummy_socket(monkeypatch):
    # Replace socket.socket with DummySocket for all tests
    monkeypatch.setattr(socket, 'socket', lambda *args, **kwargs: DummySocket())


def make_config(ip):
    # Helper to create a minimal config object
    return SimpleNamespace(
        wsjt_ip=ip,
        wsjt_port=12345,
        my_call='CALL',
        follow_frequency=False,
        tx_power=None,
        tx_retries=5,
        enable_unsolicited=True,
        logger_ip=None,
        logger_port=None
    )


def test_multicast_join():
    raw_ip = '224.0.0.1'
    config = make_config(raw_ip)
    seq = Sequencer(config, queue=None, call_select=None)
    # membership request should be for group raw_ip on 0.0.0.0
    mreq = struct.pack('4s4s', socket.inet_aton(raw_ip), socket.inet_aton('0.0.0.0'))
    assert (socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq) in seq.sock.options


def test_unicast_no_multicast():
    raw_ip = '127.0.0.1'
    config = make_config(raw_ip)
    seq = Sequencer(config, queue=None, call_select=None)
    # ensure no IP_ADD_MEMBERSHIP option added for unicast address
    added = [opt for opt in seq.sock.options if opt[0] == socket.IPPROTO_IP and opt[1] == socket.IP_ADD_MEMBERSHIP]
    assert not added 