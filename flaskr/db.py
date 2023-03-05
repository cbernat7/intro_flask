import sqlite3

import click
from flask import current_app, g


def get_db():
    # g is a special object unique for each request
    # used to store data that might be accessed by multiple functions
    # during the request. the connection is stored and reused
    # current_app object that points to FLsk app handling the request
    # get_db will be called when the app has been created and is handling a request
    if 'db' not in g:
        # establishes a connected to the file pointed at by DATABASE config key
        g.db = sqlite3.connect(

            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # tells connection to return rows that behave like dicts
        # can access columns by name
        g.db.row_factory = sqlite3.Row

    return g.db


# checks is a connection was created by check if g.db was set
# if connection, closes it
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    # get_db returns a database connection which is used to execute the commands read from the file
    db = get_db()

    # open_resource() opens a file r/t flaskr package
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


# defines a command line command called init-db that calls
# the init_db function and show s a success message to user
@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


# takes an application and registers the applicaiton instance
def init_app(app):
    # tells Flask to call that functions when cleaning up after reutrning the resposne
    app.teardown_appcontext(close_db)

    # adds a new command that can be called w the flask command
    app.cli.add_command(init_db_command)