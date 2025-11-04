@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('people_list'))
        else:
            return render_template('login.html', error='Wrong username or password')
    return render_template('login.html')