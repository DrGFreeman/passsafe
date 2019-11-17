from getpass import getpass
from threading import Thread
import time

from flask import Flask
from flask import request
from waitress import serve

from passsafe import Safe
from passsafe import InvalidToken

MAX_MINUTES = 8 * 60
MAX_INVALID_TOKENS = 3

LOGO = r"""
                               (
           )                 ) )\ )    (
 `  )   ( /(  (   (   (   ( /((()/(   ))\
 /(/(   )(_)) )\  )\  )\  )(_))/(_)) /((_)
((_)_\ ((_)_ ((_)((_)((_)((_)_(_) _|(_))
| '_ \)/ _` |(_-<(_-<(_-</ _` ||  _|/ -_)
| .__/ \__,_|/__//__//__/\__,_||_|  \___|
|_|
"""


def ask_user_password():
    password = ''
    while password == '':
        password = getpass("Enter the user password to store: ")
    return password


def ask_user_minutes():
    valid = False
    while not valid:
        default = 60
        minutes = input(
            f"Specify the storage duration in minutes (default={default}): "
        )
        try:
            if minutes == '':
                return default
            minutes = int(minutes)
            if minutes >= 1 and minutes <= MAX_MINUTES:
                valid = True
            else:
                raise ValueError
        except ValueError:
            print(f"Enter a numeric value between 1 and {MAX_MINUTES}")

    return minutes


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def get_password():
    token = request.args.get('token')

    safe = app.config['safe']

    try:
        if app.config['invalid_tokens'] >= MAX_INVALID_TOKENS:
            return 'Maximum number of invalid tokens exceeded\n', 403
        else:
            password = safe.get_password(token)
            return password, 200

    except InvalidToken:
        app.config['invalid_tokens'] += 1
        return 'Invalid or expired token\n', 406


def serve_app(app):

    serve(app, host='localhost', port=8051)


def run():

    minutes = ask_user_minutes()

    safe = Safe()

    passphrase, token = safe.encrypt(ask_user_password(), minutes=minutes)

    print(LOGO)
    print(f"\nYour password is stored in the safe for a period of "
          f"{minutes} minutes.")
    print("Use the passphrase and token below in the client application:\n")
    print(f"Passphrase:\n    {passphrase}")
    print(f"Token:\n    {token[:3]} {token[3:]}\n")

    app.config['safe'] = safe
    app.config['invalid_tokens'] = 0

    t = Thread(target=serve_app, args=[app], daemon=True)
    t.start()

    time.sleep(minutes * 60)

    print(f"\nPassword storage duration has expired. Shutting down the safe.")


if __name__ == '__main__':

    run()
