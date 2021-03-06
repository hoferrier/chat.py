import re
import socket
import threading
from blessings import Terminal
from datetime import datetime
import time
import random


def get_self_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        ip = '10.0.0.19'
    return ip


def print_intro():
    y = int(term.height/2-3)
    ip_spacing = round((term.width - len(self_ip))//2)-1

    print(term.clear)
    with term.location(0, y):
        print('chat.py v0.2.0'.center(term.width))
        print(('¸,ø¤º°` ' + start_msgs[random.randint(0, len(start_msgs)-1)] + ' `°º¤ø,¸').center(term.width))
        print('your IP address is:'.center(term.width))
        print(' '*ip_spacing, end='')
        print(term.reverse(self_ip.center(len(self_ip)+2)))


def get_partner_ip():
    print_intro()
    with term.location(0, int(term.height/2-3) + 5):
        ip = input('partner\'s ip: '.rjust(round(term.width / 2)))
    ip_pattern = re.compile('[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}')
    valid_ip = bool(re.match(ip_pattern, ip))
    while not valid_ip:
        print_intro()
        with term.location(0, int(term.height/2-3) + 6):
            print(term.red + 'invalid ip'.center(term.width) + term.normal)
        with term.location(0, int(term.height/2-3) + 5):
            ip = input('partner\'s ip: '.rjust(round(term.width / 2)))
        if re.match(ip_pattern, ip):
            valid_ip = True
    return ip


def get_self_name():
    print_intro()
    with term.location(0, int(term.height/2-3) + 5):
        return input('screen name: '.rjust(round(term.width / 2)))


def local_sender(term, var):
    while True:
        with term.location(0, term.height-1):
            var = input('> ')
            print(term.clear, end='')
        if var == 'quit':
            break


def local_receiver(term, var):
    location = 0
    while True:
        if var == 'quit':
            break
        elif var:
            with term.location(0, term.height-2):
                cur_time = datetime.now().strftime('%H:%M:%S')
                print('[' + cur_time + '] partner: ' + var)
                var = ''
                location += 1
        else:
            with term.location(0, term.height-2):
                cur_time = datetime.now().strftime('%H:%M:%S')
                print('[' + cur_time + '] system: got nothing. ')
                location += 1
            time.sleep(10)


def logger():
    while True:
        with term.location(0, term.height-1):
            message = input('')
            log.append((datetime.now().strftime('%H:%M:%S'), self_name, message))


def receiver():
    global partner_name
    global rcv_status
    last_error = None
    connection = None
    sock_rcv.bind(self_addr)
    while not connection:
        try:
            sock_rcv.listen()
            connection, client_address = sock_rcv.accept()
            rcv_status = True
        except OSError:
            if last_error is not OSError:
                last_error = OSError
                log.append((datetime.now().strftime('%H:%M:%S'), ERR_NAME, 'Failed to receive connection.'))

    while True:
        data = connection.recv(4096)
        if data:
            text = data.decode('utf-8')
            if text[0] == '-':
                text = text[1:].split(' ')
                if text[0] == 'setname':
                    partner_name = text[1]
                    log.append((datetime.now().strftime('%H:%M:%S'), SYS_NAME, 'Connected to {}.'.format(partner_name)))
                if text[0] == 'q':
                    log.append((datetime.now().strftime('%H:%M:%S'), SYS_NAME, '{} has closed the connection. Press any key to exit.'.format(partner_name)))
            else:
                log.append((datetime.now().strftime('%H:%M:%S'), partner_name, text))


def sender():
    global snd_status
    last_error = None

    while not snd_status:
        try:
            sock_snd.connect(partner_addr)
            sock_snd.sendall(bytearray('-setname ' + self_name, 'utf-8'))
            snd_status = True
        except ConnectionRefusedError as e:
            if last_error is not ConnectionRefusedError:
                last_error = e
                log.append((datetime.now().strftime('%H:%M:%S'), ERR_NAME, 'Failed to send connection.'))
            time.sleep(1)
        except BrokenPipeError as e:
            if last_error is not BrokenPipeError:
                last_error = e
                log.append((datetime.now().strftime('%H:%M:%S'), ERR_NAME, 'Failed to send data.'))
            time.sleep(1)
        except OSError:
            if last_error is not OSError:
                last_error = OSError
                log.append((datetime.now().strftime('%H:%M:%S'), ERR_NAME, 'Problem with partner\'s IP address.'))
            time.sleep(1)

    exit = False
    while not exit:
        with term.location(0, term.height-1):
            message = input()
        if message:
            if message.startswith('-'):
                if message.strip('-') == 'q':
                    exit = True
            try:
                sock_snd.sendall(bytearray(message, 'utf-8'))
                log.append((datetime.now().strftime('%H:%M:%S'), self_name, message))
            except BrokenPipeError:
                log.append((datetime.now().strftime('%H:%M:%S'), SYS_NAME, 'Message "{}" not sent.'.format(message)))


def writer():
    old_len = 0
    max_char = 0
    while True:
        if old_len != len(log):
            for item in log:
                if len(item[1]) > max_char:
                    max_char = len(item[1])
            old_len = len(log)
            print(term.clear)
            if len(log) < (term.height - 1):
                with term.location(0, 0):
                    for item in log:
                        print(colorise(item, max_char))
            else:
                with term.location(0, 0):
                    for item in log[-term.height-1:]:
                        print(colorise(item, max_char))
            print(term.move(term.height-1, 0))


def colorise(item, max_char):
    if item[1] == SYS_NAME:
        out_string = term.bright_black('[{}] {}: {}'.format(item[0], item[1].rjust(max_char), item[2]))
    elif item[1] == ERR_NAME:
        out_string = term.red('[{}] {}: {}'.format(item[0], item[1].rjust(max_char), item[2]))
    elif item[2][0] == '>':
        out_string = '[{}] {}: {}'.format(item[0], item[1].rjust(max_char), term.green(item[2]))
    else:
        out_string = '[{}] {}: {}'.format(item[0], item[1].rjust(max_char), item[2])

    if len(out_string) > term.width:
        for i in range(term.width, len(out_string), term.width):
            out_string = out_string[0:i] + '\n'.ljust(max_char+14) + out_string[i:]

    return out_string

if __name__ == '__main__':
    start_msgs = ['now with networking',
                  'with 50% less bees',
                  'S Y N E R G Y',
                  'no girls allowed',
                  'make local networking great again']
    rcv_msgs = {False: '⟳ connecting downstream...', True: '✓ connected downstream'}
    snd_msgs = {False: '⟳ connecting upstream...', True: '✓ connected upstream'}
    SYS_NAME = 'chat.py'
    ERR_NAME = 'error'
    log = []
    term = Terminal()

    sock_rcv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rcv_status = False

    sock_snd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    snd_status = False

    partner_name = ''
    partner_ip = ''
    partner_port = 10008

    self_name = ''
    self_ip = ''
    self_port = 10007

    print(term.enter_fullscreen)

    self_ip = get_self_ip()
    self_addr = (self_ip, self_port)
    threading.Thread(target=receiver).start()

    partner_ip = get_partner_ip()
    partner_addr = (partner_ip, partner_port)
    self_name = get_self_name()

    threading.Thread(target=sender).start()

    while not rcv_status or not snd_status:
        print(term.clear)
        with term.location(0, int((term.height / 2) - 1)):
            print(rcv_msgs[rcv_status].center(term.width))
            print(snd_msgs[snd_status].center(term.width))
        time.sleep(1)

    log.append((datetime.now().strftime('%H:%M:%S'), SYS_NAME, 'connected to ' + partner_name))

    writer()

    print(term.exit_fullscreen)

