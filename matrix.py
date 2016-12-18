from flask import Flask, render_template, request, session, flash
import flask_login
import os
from user import User
import threading
import leds

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')

app = Flask(__name__)
app.secret_key = 'a really secret key'
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
users = {'simon@koala.ie': {'pw': 'give me a break'}}


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return
    user = User()
    user.id = email
    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['pw'] == users[email]['pw']
    return user


def startYourEngines(message):
    print 'here is the message ' + message
    leds.displayImage(message)
    return


@app.route("/")
def index():
    if 'logged_in' in session:
        return render_template('main.html')
    else:
        return render_template('welcome.html')


@app.route("/start")
@flask_login.login_required
def start():
    global t
    global message
    s = os.path.join(APP_STATIC, message) + '.png'
    print 's=' + s
    t = threading.Thread(target=startYourEngines, args=(s,))
    t.start()
    flash('Lights started')
    return render_template('main.html')


@app.route("/stop")
@flask_login.login_required
def stop():
    leds.stopDisplay()
    flash('Lights stopped')
    return render_template('main.html')


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'GET':
        flash('Please login')
        return render_template('welcome.html')
    email = request.form['email']
    try:
        if request.form['pw'] == users[email]['pw']:
            user = User()
            user.id = email
            flask_login.login_user(user)
            session['logged_in'] = True
            return render_template('main.html')
    except KeyError as e:
        flash('Invalid email')
        return render_template('welcome.html')

    flash('Invalid password')
    return render_template('welcome.html')


@app.route("/logout", methods=['GET'])
def logout():
    flask_login.logout_user()
    session.pop('logged_in', None)
    return render_template('welcome.html')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


@app.route("/message", methods=['POST'])
@flask_login.login_required
def message():
    global message
    message = request.form['chosen']
    flash('Message set to ' + message)
    return render_template('main.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9090, debug=True)
