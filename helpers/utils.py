import socket
import contextlib 

def is_port_open(port, host='127.0.0.1'):
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return False
        else:
            return True


def get_port():
    while True:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        if is_port_open(port):
            return port
            
