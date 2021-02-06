from flask import Flask, request, render_template, render_template_string, make_response, redirect, url_for, session, g
import sqlite3
import hashlib
import os
import time, random
from selenium import webdriver

app = Flask(__name__) 
app.secret_key = os.urandom(32)
DATABASE = "database.db"


userLevel = {
    0 : 'guest',
    1 : 'admin'
}


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/') 
def index(): 
    return render_template('index.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        userid = request.form.get("userid")
        password = request.form.get("password")
        if userid !='admin':
            password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        cur = conn.cursor()
        user = cur.execute('SELECT * FROM user WHERE id = ? and pw = ?', (userid, password )).fetchone()
        
        if user:
            session['idx'] = user['idx']
            session['userid'] = user['id']
            session['level'] = userLevel[user['level']]
            return redirect(url_for('index'))

        return "<script>alert('Wrong id/pw');history.back(-1);</script>";


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        userid = request.form.get("userid")
        password = request.form.get("password")
        name = request.form.get("name")

        conn = get_db()
        cur = conn.cursor()
        user = cur.execute('SELECT * FROM user WHERE id = ?', (userid,)).fetchone()
        if user:
            return "<script>alert('Already Exists userid.');history.back(-1);</script>";


        sql = "INSERT INTO user(id, pw, name, level) VALUES (?, ?, ?, ?)"
        cur.execute(sql, (userid, hashlib.sha256(password.encode()).hexdigest(), name, 0))
        conn.commit()
        return "<script>alert('Register Success');location.href='/login';</script>"

@app.route('/notice')
def board():
    if session:
        by=request.args.get("by",default='idx')
        conn = get_db()
        cur = conn.cursor()
        lists = cur.execute('SELECT * FROM board order by '+by).fetchall() 
        return render_template('notice.html',lists=lists)
    return "<script>alert('login first');location.href='/';</script>"


@app.route('/<path:file>')
def test(file):
    if session:
        if 'admin' in session['userid']:
            def filter(s):
                s = s.replace('(', '').replace(')', '')
                blacklist = ['config', 'self']
                return ''.join(['{{% set {}=None%}}'.format(c) for c in blacklist])+s
            return render_template_string(filter(file))
        return "you need join with admin"
    return "you are not logged in"

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port='2322', debug=True)