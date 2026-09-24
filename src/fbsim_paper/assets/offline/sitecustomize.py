"""Fail closed on network access during explicitly offline reproduction/tests."""
import sys

def reject_network(event, args):
    if event in {'socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'socket.gethostbyname', 'socket.sendto', 'socket.bind'}:
        raise RuntimeError('Network access is disabled by the offline reproduction guard')
sys.addaudithook(reject_network)
