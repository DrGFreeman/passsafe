import base64
import getpass
from pathlib import Path
import random

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pyotp import TOTP
from pyotp import random_base32
import requests

from .version import __version__  # noqa F401

PASSPHRASE_N_WORDS = 6

# Use random.SystemRandom instead of random
sys_random = random.SystemRandom()


def _generate_key(passphrase):
    """Generates a encryption/decryption key from a passphrase using a
    password based key derivation function (PBKDF).

    Parameters
    ----------
    passphrase : str
        The passprhrase from which to derive the key.

    Returns
    -------
    key : bytes
        The derived key."""

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256,
        length=32,
        salt=base64.urlsafe_b64encode(getpass.getuser().encode('utf-8')),
        iterations=100000,
        backend=default_backend()
    )

    return base64.urlsafe_b64encode(
        kdf.derive(passphrase.encode('utf-8'))
    )


class Passphrase():
    """Class used to generate cryptographically secure passphrases.
    The class uses the english word list from Securedrop
    (https://github.com/freedomofpress/securedrop#wordlists)."""

    def __init__(self):

        self.words = list(self._load_words())

    def _load_words(self):

        path = Path(__file__).parent.joinpath('wordlists', 'securedrop_en.txt')
        with open(path, 'r') as word_file:
            lines = word_file.readlines()
            words = map(lambda x: x.replace('\n', ''), lines)

        return words

    def generate(self, n, separator=' '):
        """Generates a random passphrase using words from a list.

        Parameters
        ----------
        n : int
            The number of words in the passphrase.

        separator : str, optional, default=' '
            The character(s) separating the words of the passphrase.

        Returns
        -------
        passphrase : str
            The generated passphrase.
        """

        return separator.join(sys_random.sample(self.words, n))


class Safe():
    """Stores the encrypted password for a determined period.

    This class stores the enctypted password, provides a passphrase and token
    and returns the encrypted password when provided the valid token"""

    def __init__(self):
        pass

    def encrypt(self, password, minutes):
        """Encrypts the user password.

        Parameters
        ----------
        password : str
            The password to encrypt

        minutes : int
            The validity period, in minutes, of the TOTP token used to
            retreive the encrypted password.

        Returns
        -------
        passphrase : str
            The passhprase used to derive the encryption key.

        token : str
            The TOTP token required to retreive the encrypted password.
        """

        self._window = 60 * int(minutes)

        # Generate TOTP source
        self._totp = TOTP(random_base32(), interval=1)

        # Generate TOTP token
        token = self._totp.now()

        # Generate passphrase and derive key from passphrase
        passphrase = Passphrase().generate(PASSPHRASE_N_WORDS)
        key = _generate_key(passphrase)

        # Encrypt password using key
        f = Fernet(key)
        self._password = f.encrypt(password.encode('utf-8'))

        return passphrase, token

    def get_password(self, token):
        """Returns the encrypted password, provided a valid TOTP token.

        Parameters
        ----------
        token : str
            The TOTP token required to retreive the encrypted password.

        Returns
        -------
        password : str
            The encrypted password.

        Raises
        ------
        InvalidToken
            If the provided TOTP token is invalid or expired.
        """

        token = token.replace(' ', '')

        if self._totp.verify(token, valid_window=self._window):
            return self._password
        else:
            raise InvalidToken('Invalid TOTP token.')


class Client():
    """Retreives the password from the server and decrypts it.

    Parameters
    ----------
    passphrase : str
        The passphrase use to derive the password decryption key.

    token : str
        The TOTP token required to retreive the encrypted password from the
        server.

    host : str, optional, default=http://localhost:8051
        The server host URL including the port number.
    """

    def __init__(self, passphrase, token, host='http://localhost:8051'):
        self._passphrase = passphrase.strip()
        self._token = token
        self._host = host

    def password(self):
        """Retreives the encrypted password from the server, decrypts is and
        returns it in plain text.

        Returns
        -------
        password : str
            The decrypted password in plain text.

        Raises
        ------
        InvalidToken
            If the TOTP token is invalid or expired (http status code 406).

        MaxInvalidTokens
            If the maximum number of invalid tokens has been exceeded (http
            status code 403).
        """

        response = requests.post(f"{self._host}/?token={self._token}")

        if response.status_code == 200:
            return self._decrypt(response.content)
        elif response.status_code == 406:
            raise InvalidToken('Invalid or expired token.')
        elif response.status_code == 403:
            raise MaxInvalidTokens(
                'Maximum number of invalid tokens exceeded.')

    def _decrypt(self, password):

        key = _generate_key(self._passphrase)
        f = Fernet(key)

        return f.decrypt(password).decode('utf-8')


class InvalidToken(Exception):
    """A custom exeption raised when the TOTP token is either invalid or
    expired (http status code 406)."""
    pass


class MaxInvalidTokens(Exception):
    """A custom exception raised when the maximum number of invalid tokens
    has been recieved (http status code 403)."""
