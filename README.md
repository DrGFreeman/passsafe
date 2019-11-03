# passsafe
A client-server app to safely handle a password in analytical applications

## Installation

```
$ pip install git+https://github.com/DrGFreeman/passsafe.git
```

## Usage

**passsafe** uses a client-server model to store and access the user password (or other secret). The user first launches the server in a terminal, choses the duration for which the password will be available and provides the password to be stored. The server prints out a one time passphrase and token which the user then uses in the client application to retrive the password from the server.

### Server

Launch the server with the `passsafe` command, enter the duration and the password to store ([`correct horse battery staple`](https://xkcd.com/936/) is used as password in the example below):

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

Coming soon...


## Notes on security

Coming soon...

