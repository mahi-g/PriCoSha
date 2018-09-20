from flask import Flask, render_template, redirect, request, session, url_for, flash
import pymysql.cursors
import hashlib

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='root',
                       db='pricosha2',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login')
def login():
	return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

@app.route('/loginAuth', methods = ['GET', 'POST'])
def loginAuth():
     username = request.form["username"]
     password = request.form["password"]
     h = hashlib.md5(password.encode('utf-8')).hexdigest()
     cursor = conn.cursor() #cursor used to send queries
     query = 'SELECT * FROM person WHERE username = %s and password = %s'
     cursor.execute(query, (username, h))
     data = cursor.fetchone() 
     cursor.close()
     error = None
     if(data):
     	session['username'] = username
     	return redirect(url_for('home'))
     else:
     	error = "Invalid username or password"
     	return redirect('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['username']
	password = request.form['password']
	fname = request.form['fname']
	lname = request.form['lname']
	h = hashlib.md5(password.encode('utf-8')).hexdigest()
	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM person WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	if(data):
		#If the previous query returns data, then user exists
		error = "username already exists"
		return render_template('register.html', error=error)
	else:
		ins = 'INSERT INTO person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, h, fname, lname))
		conn.commit()
		cursor.close()
		return redirect(url_for('login'))
@app.route('/home', methods = ['GET', 'POST'])
def home():
    username = session['username']
    cursor = conn.cursor();
    query = 'SELECT timest, Content.id, username, file_path, content_name FROM Content WHERE username = %s or public = %s or Content.id in (SELECT id FROM Share, Member WHERE Share.group_name = Member.group_name && Member.username = %s) ORDER BY timest DESC'
    cursor.execute(query, (username, True, username))
    data = cursor.fetchall()
    getComments = 'SELECT id, username, timest, comment_text from comment'
    cursor.execute(getComments)
    commentLists = cursor.fetchall()
    tagQuery = 'SELECT id, username_taggee, status from tag'
    cursor.execute(tagQuery)
    tags = cursor.fetchall()
    getTag = 'SELECT * FROM tag where username_taggee = %s and status = 0'
    cursor.execute(getTag, (username))
    pending_tags = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, posts=data, commentlist=commentLists, taglist=tags, pending_tags = pending_tags)
        
@app.route('/create', methods=['GET', 'POST'])
def createFG():
        username = session['username']
        friend = request.form['friend']
        group_name = request.form['group_name']
        description = request.form['description']
        cursor = conn.cursor()
        query = 'SELECT username FROM friendgroup WHERE group_name = %s and username = %s'
        cursor.execute(query, (group_name, username))
        checkGroupName = cursor.fetchone()
        error = None
        if(checkGroupName):
                flash("Group already exists")
                return redirect(url_for('home'))

        checkFriend = 'SELECT username FROM person WHERE username = %s'
        cursor.execute(checkFriend, (friend))
        fUsername = cursor.fetchone()
        if(not fUsername):
                flash("Username does not exist")
                return redirect(url_for('home'))
        if(friend == username):
                flash("You cannot add yourself!")
                return redirect(url_for('home'))
                
        else:               
                ins= 'INSERT INTO friendgroup(username, group_name, description) VALUES(%s, %s, %s)'
                cursor.execute(ins, (username, group_name, description));
                ins_member= 'INSERT INTO member(username, group_name, username_creator) VALUES(%s, %s, %s)'
                cursor.execute(ins_member, (friend, group_name, username));
                conn.commit()
                cursor.close()
                return redirect(url_for('home'))

@app.route('/addFriend', methods=['GET', 'POST'])
def addFriend():
        
	return render_template('add_friend.html')

@app.route('/addFriendAuth', methods=['GET', 'POST'])
def addFriendAuth():
        username = session['username']
        friendGroup = request.form['friendGroup']
        fUsername = request.form['fUsername']
        cursor = conn.cursor();
        query = 'SELECT group_name, username FROM friendgroup WHERE group_name = %s AND username = %s'
        cursor.execute(query,(friendGroup, username))
        data = cursor.fetchone()
        error = None
        if(data):
                check_friend = 'SELECT username FROM person WHERE username = %s'
                cursor.execute(check_friend, fUsername)
                fdata = cursor.fetchone()
                if(fdata):
                         existing_friend = 'SELECT username FROM member WHERE username = %s and group_name = %s and username_creator = %s'
                         cursor.execute(existing_friend, (fUsername, friendGroup, username))
                         existing_friend_data = cursor.fetchone()
                         if(not existing_friend_data):
                                 ins = 'INSERT INTO member VALUES(%s, %s, %s)'
                                 cursor.execute(ins, (fUsername, friendGroup, username))
                                 conn.commit()
                                 cursor.close()
                                 return redirect(url_for('home'))
                         else:
                                 error = "Username already in friend group"
                                 return render_template('add_friend.html', error=error)
                else:
                        error = "Username does not exist"
                        return render_template('add_friend.html', error=error)
       
        else:
                error = "Friend group does not exist"
                return render_template('add_friend.html', error=error)

@app.route('/post', methods=['GET', 'POST'])
def post():
        username = session['username']
        cursor = conn.cursor();
        Content = request.form['Content']
        file_path = request.form['file_path']
        public = request.form['public']
        group = request.form['group_name']
        error = None
        if (public == 'public'):
                #public = True
                queryToPost = 'INSERT INTO Content (content_name, username, file_path, public) VALUES(%s, %s, %s, %s)'
                cursor.execute(queryToPost, (Content, username, file_path,1))
        elif(public == 'private'):
                q = 'SELECT group_name FROM FriendGroup WHERE group_name = %s'
                cursor.execute(q,(group))
                selectFriendGroup = cursor.fetchone()
                if (selectFriendGroup):
                #for group in selectFriendGroup:
                        queryToFindfgOwner = 'SELECT username_creator FROM member WHERE group_name = %s and username_creator = %s'
                        cursor.execute(queryToFindfgOwner, (group, username))
                        owner = cursor.fetchone()
                        if(owner):
                                owner = owner.get('username_creator')
                        if(not owner):
                                  #error = "Friend group does not exist"
                                  #return render_template('home.html', username=username, perror=error)
                                  flash("Friend group does not exist")
                                  return redirect(url_for('home'))
                        queryToPost = 'INSERT INTO Content(content_name, username, file_path, public) VALUES(%s, %s, %s, %s)'
                        cursor.execute(queryToPost, (Content, username, file_path,0))
                        content_id = cursor.lastrowid #returns the value generated for an AUTO_INCREMENT column by the previous INSERT
                        queryToShare = 'INSERT INTO Share (id, group_name, username) VALUES (%s, %s, %s)'
                        cursor.execute(queryToShare, (content_id, group, username))

        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/comment', methods=['GET', 'POST'])
def comment():
            username = session['username']
            cursor = conn.cursor();
            comment = request.form['comment']
            cID = request.form['cID']
            query = 'INSERT into Comment (id, username, comment_text) VALUES (%s, %s, %s)'
            cursor.execute(query, (cID, username, comment))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))

@app.route('/tag', methods=['GET', 'POST'])
def tag():
            username = session['username']
            cursor = conn.cursor();
            cID = request.form['cID']
            taggee = request.form['taggee']
            status = False
            tag_error = None
            
            #checking if same tag already exists
            queryToCheckTag = 'SELECT * FROM Tag WHERE id = %s AND username_taggee = %s'
            cursor.execute(queryToCheckTag,(cID, taggee))
            tagExists = cursor.fetchone()

            if (tagExists):

                              flash("Tag already exists")
                              return redirect(url_for('home'))
                        
            validUser = 'SELECT username FROM person WHERE username = %s'
            cursor.execute(validUser,(taggee))
            userExists = cursor.fetchone()
            if(not userExists):
                    flash("Cannot add tag: User does not exist!")
                    return redirect(url_for('home'))

            if (username == taggee):
                            status = True
                            queryToPostTag = 'INSERT INTO Tag(id, username_tagger, username_taggee, status) VALUES (%s, %s, %s, %s)'
                            cursor.execute(queryToPostTag,(cID, username, username, status))
             

            else:
                            queryToPostTag = 'INSERT INTO Tag(id, username_tagger, username_taggee, status) VALUES (%s, %s, %s, %s)'
                            cursor.execute(queryToPostTag,(cID, username, taggee, status))

            conn.commit()
            cursor.close()
            return redirect(url_for('home'))

@app.route('/manage', methods=['GET', 'POST'])
def managetags():
        username = session['username']
        answer = request.form['answer'] ##the problem is here
        cID = request.form['id']
        username_tagger = request.form['username_tagger']
        #username_tagger = request.form['username_tagger']
        cursor = conn.cursor()
        if(answer == 'yes'):
                query = 'UPDATE tag SET status = 1 WHERE username_taggee = %s and username_tagger = %s and id = %s'
                cursor.execute(query, (username, username_tagger, cID))
        else:
                query = 'DELETE FROM tag where username_tagger = %s and username_taggee = %s and id = %s '
                cursor.execute(query, (username_tagger, username, cID))
        conn.commit()

        cursor.close()
        return redirect(url_for('home')) ## always runs but nothingn changes in mysql



@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/login')

app.secret_key = 'some key'


if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
