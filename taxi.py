import sys
import os
import re
import pickle
import imaplib
import getpass
import email
import email.message
import base64


def fetch_db(email_address):
    print('> get emails')
    imap_srv = 'imap.yandex.ru'
    imap = imaplib.IMAP4_SSL(imap_srv)
    my_email = email_address
    r, _ = imap.login(my_email, getpass.getpass())
    if r != 'OK':
        print('Cannot login with {} to {}'.format(my_email, imap_srv),
              file=sys.stderr)
        sys.exit(2)
    print('Login OK.')

    imap.select()
    # search messages
    taxi_email = 'no-reply@taxi.yandex.ru'
    r, email_ids = imap.search(None, '(FROM "{}")'.format(taxi_email))
    if r != 'OK':
        print('Cant find messages from {}'.format(taxi_email))
        sys.exit(2)
    # get all messages
    print('> fetch email by id:')
    msgs = []
    for msg_id in email_ids[0].split():
        r, msg = imap.fetch(msg_id, '(RFC822)')
        if r != 'OK':
            print('Cant fetch message {}'.format(msg_id))
            continue
        print('fetch email: {}'.format(msg_id.decode('utf8')))
        msgs.append(msg)
    print('get OK')
    imap.logout()

    str_msgs = []
    msg_cls = email.message.EmailMessage
    for raw_msg in msgs:
        msg = email.message_from_bytes(raw_msg[0][1], _class=msg_cls)
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                mstr = base64.b64decode(part.get_payload()).decode('utf8')
                str_msgs.append(mstr)
    return str_msgs


def load_db(email_address):
    msgs = []
    dump_filename = 'taxidump.bin'
    if not os.path.exists(dump_filename):
        msgs = fetch_db(email_address)
        with open(dump_filename, 'wb') as f:
            pickle.dump(msgs, f)

    with open(dump_filename, 'rb') as f:
        msgs = pickle.load(f)
    
    return msgs

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: taxi1.py <email_address>', file=sys.stderr)
        sys.exit(2)
    email_address = sys.argv[1]
    msgs = load_db(email_address)
    summ = 0
    pay = re.compile(r'Стоимость поездки\s+(\d+)\s+руб')
    for msg in msgs:
        res = pay.findall(msg)
        if len(res) == 0:
            continue
        summ += int(res[0])
    print('ПОТРАЧЕНО: {}'.format(summ))

