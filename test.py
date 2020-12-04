from flask import Flask , render_template , flash , redirect , url_for, session, logging, request
from flask_mysqldb import MySQL 
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#Kayıt Formu

class RegisterForm(Form):
	name = StringField("İsim",validators=[validators.Length(min = 4,max = 25)])
	surname = StringField("Soyisim" , validators=[validators.Length(min=2 , max=20)])
	username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
	email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
	password = PasswordField("Parola:",validators=[
		validators.DataRequired(message = "Lütfen bir parola belirleyin"),
		validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
    ])
	confirm = PasswordField("Parola Doğrula")


#login formu
class LoginForm(Form):
	username = StringField("Kullanıcı adı")
	password = PasswordField("Parola")

app = Flask(__name__)
app.secret_key = "bk_blog"


#decorator
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if "log_in" in session:
			return f(*args, **kwargs)
		else:
			flash("Bu sayfayı görüntülemek için GİRİŞ YAP","danger")
			return redirect(url_for("login"))
	return decorated_function


app.config["MYSQL_HOST"]= "localhost"
app.config["MYSQL_USER"]= "root"
app.config["MYSQL_PASSWORD"]= ""
app.config["MYSQL_DB"]= "bk_blog"
app.config["MYSQL_CURSORCLASS"]= "DictCursor"



mysql =MySQL(app)




@app.route('/')
def index():
	return render_template("index.html" )


@app.route('/about')
def about():
   return render_template("about.html")

@app.route('/articles')
def articles():
	cursor = mysql.connection.cursor()
	query = "select * from articles"

	result =cursor.execute(query)
	if result > 0:
		articles = cursor.fetchall()
		return render_template("articles.html" , articles=articles)
	else:
		return render_template("articles.html")
	return render_template("articles.html")



@app.route('/dashboard')
@login_required
def dashboard():
	cursor = mysql.connection.cursor()
	query = "select * from articles where author = %s"

	result =cursor.execute(query,(session["username"],))
	
	if result > 0:
		articles = cursor.fetchall()
		return render_template("dashboard.html" , articles=articles)
	else:
		return render_template("dashboard.html")


	return render_template("dashboard.html")


@app.route('/addarticles' , methods = ["GET","POST"])
def addarticles():
	form = ArticlesForm(request.form)
	if request.method =="POST" and form.validate():
		title = form.title.data
		content = form.content.data

		cursor = mysql.connection.cursor()

		query = "insert into articles(title,author,content) VALUES (%s,%s,%s)"

		cursor.execute(query,(title,session["username"],content))
		mysql.connection.commit()
		
		cursor.close()

		flash("makale başarı ile eklendi" , "success")
		return redirect(url_for("dashboard"))

	return render_template("addarticles.html" , form = form)

#makale form
class ArticlesForm(Form):
	title =StringField("Makale Başlığı", validators = [validators.Length(min = 5 , max =50)])
	content = TextAreaField("Makale İçeriği" , validators = [validators.Length(min = 10)])


#article detail
@app.route('/article/<string:id>')
def detail(id):
	cursor = mysql.connection.cursor()
	query = "select * from articles where id = %s"
	result = cursor.execute(query,(id,))
	mysql.connection.commit()

	if result >0:
		article = cursor.fetchone()
		return render_template("article.html",article=article)
	else:
		return render_template("article.html")


#article delete
@app.route('/delete/<string:id>')
@login_required
def delete(id):
	cursor = mysql.connection.cursor()
	query = "select * from articles where author = %s and id = %s "
	result = cursor.execute(query,(session["username"],id))
	if result >0 :
		query2 = "delete from articles where  id = %s"
		cursor.execute(query2,(id))
		mysql.connection.commit()
		return redirect(url_for("dashboard"))
	else:
		flash("Böyle bir makale yok ya da bu işleme yetkiniz yok", "danger")
		return redirect(url_for("index"))



#register
@app.route('/register',methods=["GET","POST"])
def register():
	form= RegisterForm(request.form)

	if request.method =="POST" and form.validate():
		firstname = form.name.data
		surname = form.surname.data
		username = form.username.data
		email=form.email.data
		userPassword = sha256_crypt.encrypt(form.password.data)

		cursor = mysql.connection.cursor()

		query = "insert into users(firstname,surname,email,username,userPassword) VALUES (%s,%s,%s,%s,%s)"
		val = (firstname,surname,email,username,userPassword)
		cursor.execute(query,val)
		mysql.connection.commit()

		cursor.close()

		flash(message="Kayıt Başarılı.." , category="success")
		return redirect(url_for("login"))

	else :
  	 	return render_template("register.html" , form=form)

@app.route('/login' ,methods=["GET","POST"])
def login():
	form = LoginForm(request.form)


	if request.method == "POST":
		username = form.username.data
		password_enter = form.password.data

		cursor = mysql.connection.cursor()

		query = "Select * from users where username = %s"

		result = cursor.execute(query,(username,))

		if result > 0:
			data = cursor.fetchone()
			real_password = data["userPassword"]
			if sha256_crypt.verify(password_enter,real_password):
				flash("Giriş Yapıldı","success")

				session["log_in"] = True
				session["username"] = username
				return redirect(url_for("index"))
			else:
				flash("Parola Yanlış" ,"danger")
				return redirect(url_for("login"))
		else:
			flash("Kullanıcı Bulunamadı","danger")
			return redirect(url_for("login"))


	return render_template("login.html" , form=form)


#logout
@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for("index"))

if __name__ == "__main__":
	app.run(debug=True)