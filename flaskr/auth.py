import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

# creates a Blueprint named 'auth'
# url prefix prepended to all urls assoc. w blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')


# bp.route associates the URL /register with register view function
# when Flask receives a request to /auth/register, ti will cal the register view
# and use the return value as the response
@bp.route('/register', methods=('GET', 'POST'))
def register():
    # if user submits form, request.method will be 'POST'
    if request.method == 'POST':
        # request.form type of dict mapping submitted form keys and values
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        # validate that un/pw are not empty
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        # if validation successes, insert new data into database
        if error is None:
            try:
                # takes SQL query w ? placeholders, database library escapes the values
                # so not vulnerable to SQL injection attack
                db.execute(
                    "INSERT INTO user(username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),  # pw has to secure pw.
                )
                db.commit()  # call after hashing the password
            except db.IntegrityError:  # will occur if UN already exists
                error = f'User {username} is already registered.'
            else:
                # redirect back to login page
                return redirect(url_for('auth.login'))

        # flash stores messages than can be retrieved when rendering the template
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # fetchone() returns one row from the query.
        # if query returned no results, it returns None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # session is a dict that stores data across requests
            # userid is stored in a new session, dta stored in a cookie, sent to browser
            # flask securely signs the data so can't be tampered with

            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)

    return render_template('auth/login.html')


# before_app_request registers a function that runs before the view function
# no matter what url is requested
# checks if a user id is stored in the session nand gets that user's data
# from the database, storing it on g.user - lasts for length of the request
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# returns a new view function that wraps the orig view its applited to.
# new function checks if a user is loaded and redirects to login page otherwise
# is a user is loaded, te orig view is called and loads normally
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)
    return wrapped_view()