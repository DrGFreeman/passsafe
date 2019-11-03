from getpass import getpass

from flask import Flask
from flask import request
from waitress import serve

from passsafe import Safe
from passsafe import InvalidToken

MAX_MINUTES = 8 * 60


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
        password = safe.get_password(token)
        return password, 200
    except InvalidToken:
        return '', 406


def run():

    minutes = ask_user_minutes()

    safe = Safe()

    passphrase, token = safe.encrypt(ask_user_password(), minutes=minutes)

    print(f"\nYour password is stored in the safe for a period of "
          f"{minutes} minutes.")
    print("Use the passphrase and token below in the client application:\n")
    print(f"Passphrase: {passphrase}")
    print(f"Token:      {token[:3]} {token[3:]}\n")

    app.config['safe'] = safe

    serve(app, host='localhost', port=8051)


if __name__ == '__main__':

    run()
