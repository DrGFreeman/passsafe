# passsafe
A client-server app to safely handle a password in analytical applications

## Installation

```
$ pip install git+https://github.com/DrGFreeman/passsafe.git
```

## Usage

**passsafe** uses a client-server model to store and access the user password (or other secret). The user first launches the server in a terminal, choses the duration for which the password will be available and provides the password to be stored. The server prints out a one time passphrase and token which the user then uses in the client application to retrive the encrypted password from the server and decrypt it.

### Server

Launch the server with the `passsafe` command, enter the duration and the password to store (The [`correct horse battery staple`](https://xkcd.com/936/) password is used in the example below):

```
$ passsafe
Specify the storage duration in minutes (default=60): 30
Enter the user password to store: 
                               
                               (           
           )                 ) )\ )    (   
 `  )   ( /(  (   (   (   ( /((()/(   ))\  
 /(/(   )(_)) )\  )\  )\  )(_))/(_)) /((_) 
((_)_\ ((_)_ ((_)((_)((_)((_)_(_) _|(_))   
| '_ \)/ _` |(_-<(_-<(_-</ _` ||  _|/ -_)  
| .__/ \__,_|/__//__//__/\__,_||_|  \___|  
|_|                                        


Your password is stored in the safe for a period of 30 minutes.
Use the passphrase and token below in the client application:

Passphrase:
    crudely explode kilogram detached overdrive
Token:
    936 265

Serving on http://localhost:8051

```

### Client application

In the client application, import the `passsafe.Client` class and create an instance, using the passphrase and token provided by the server:

```python
In [1]: from passsafe import Client

In [2]: client = Client('crudely explode kilogram detached overdrive', 936265)
```

The clear text password can be accessed with the `password()` method of the `Client` instance:

```python
In [3]: client.password()                                                           
Out[3]: 'correct horse battery staple'
```

A more practical use case would use the `password()` method to pass the password directly into the connection string of a database connection ([`pyodbc`](https://mkleehammer.github.io/pyodbc/) driver is used in this example):

```python
In [4]: import pyodbc

In [5]: conn_str = "DRIVER={{SQL Server}};SERVER=server_name;DATABASE=db_name;UID=username;PWD={}"

In [6]: with pyodbc.connect(conn_str.format(client.password())) as conn:
   ...:     results = conn.cursor.execute("SELECT ...")
```

## How it works

When it starts, the server generates a one time passphrase composed of six words randomly selected from a [list of words](https://github.com/freedomofpress/securedrop#wordlists). This passphrase is used to derive an encryption key using a password based key derivation function (PBKDF). This key is used to encrypt the password provided by the user. The encrypted password is stored in memory by the server (the plaintext password is not stored on the server). The sever also generates and stores in memory a secret key used to generate and verify time-based one time passwords (TOTP). The server prints the one time passphrase along with a TOTP token that is valid only for the duration specified by the user.

The user uses the one time passphrase and TOTP token printed out by the server to instantiate the client. Each time the `password()` method of the client instance is called, the client contacts the server, providing the TOTP token. If the TOTP token is valid and not expired, the server returns the encrypted password to the client. The client generates a decryption key using the passphrase and the same password based key derivation function and decrypts the password using this key.

The username, as returned by the `getpass.getuser()` function is used by both the sever and client as a salt in the password based key derivation function.


## Notes on security

The security of this application is based on the following principles:
1. The encrypted password cannot [practically](https://www.rempe.us/diceware/#diceware) be decrypted without knowledge of the one time passphrase.
1. The server makes the encrypted password available only for a limited time.
1. The TOTP token is required to retrieve the encrypted password from the server.
1. The client does not store the encrypted password but gets it from the server each time it is needed.

Protecting the one time passphrase and token is the main way to ensure the password cannot be obtained and decrypted. The difference with protecting the password itself is that, in the eventuality where the passphrase is leaked (committed under version control, saved in a Jupyter notebook or in a file on disk), it is only of value if the token is also available and still valid and the server is still running. For this reason, the password storage duration of the server should be set to the shortest value practical for the use case.

### Additional security features
1. The sever will stop returning the encrypted password after three invalid TOTP tokens have been provided. This prevents an attacker from brute-forcing the server to find the TOTP token and get access to the encrypted password.
2. The username, as returned by the `getpass.getuser()` function is used by both the sever and client as a salt in the password based key derivation function. This means only the user who launched the server can decrypt the password using the client application code. Although a serious attacker with access to the application source code could easily get around this feature, it prevents a "casual" user who got access to the passphrase and token to easily decrypt the encrypted password using the unmodified client application code.

While this application does not provide absolute security against a serious attacker, it offers a practical means of providing a password to an application while making it relatively difficult to access the password. Compared to manipulating a password directly in code or storing it on disk or in an interactive notebook, the time bound nature of the application significantly reduces the risks associated with an inadvertent leakage of the password.
