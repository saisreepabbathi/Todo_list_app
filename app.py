from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['todo']
users_collection = db['users']
tasks_collection = db['tasks']

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    pending_tasks = list(tasks_collection.find({'user_id': user_id, 'status': 'pending'}))
    completed_tasks = list(tasks_collection.find({'user_id': user_id, 'status': 'completed'}))
    return render_template('index.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks, username=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not email or not password or not confirm_password:
            flash('Please fill out all fields.')
            return render_template('register.html')
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')
        if users_collection.find_one({'email': email}):
            flash('Email already registered.')
            return render_template('register.html')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users_collection.insert_one({'email': email, 'password': hashed})
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Please fill out all fields.')
            return render_template('login.html')
        user = users_collection.find_one({'email': email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user['email']
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form.get('title')
    if not title:
        flash('Task cannot be empty.')
        return redirect(url_for('index'))
    tasks_collection.insert_one({
        'user_id': session['user_id'],
        'title': title,
        'status': 'pending'
    })
    return redirect(url_for('index'))

@app.route('/complete/<task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tasks_collection.update_one({'_id': ObjectId(task_id), 'user_id': session['user_id']}, {'$set': {'status': 'completed'}})
    return redirect(url_for('index'))

@app.route('/pending/<task_id>')
def pending_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tasks_collection.update_one({'_id': ObjectId(task_id), 'user_id': session['user_id']}, {'$set': {'status': 'pending'}})
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tasks_collection.delete_one({'_id': ObjectId(task_id), 'user_id': session['user_id']})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)