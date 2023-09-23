import flask
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, PasswordField
from wtforms.validators import DataRequired, URL, email
from flask_ckeditor import CKEditor, CKEditorField
from flask_gravatar import Gravatar
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import smtplib
import secrets
import datetime

#___________________________________Constants / Instantiations____________________________________________#


MY_EMAIL = "keirandevinetest@gmail.com"
EMAIL_PW = "xqtkxyhvmfisjqfi"


#____________________________________Creation of Flask App / DataBase________________________________________#

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
ckeditor = CKEditor(app)
bootstrap = Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None )

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


#_____________________________________Configure DB Tables____________________________________________________#
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class PlaygroundRating(db.Model):
    __tablename__ = "ratings"
    id = db.Column(db.Integer, primary_key=True)
    town = db.Column(db.String(50), unique=True, nullable=False)
    map_url = db.Column(db.String(150), nullable=False)
    opening_hours = db.Column(db.String(50), nullable=False)
    equipment = db.Column(db.String(50), nullable=False)
    state_of_repair = db.Column(db.String(50), nullable=False)
    toilets = db.Column(db.String(50), nullable=False)
    lighting = db.Column(db.String(50), nullable=False)
    bins = db.Column(db.String(50), nullable=False)
    comments = db.Column(db.String(250), nullable=False)

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    comment = db.Column(db.String(250), nullable=False)






#
# with app.app_context():
#     db.create_all()
#______________________________________Create WTF Form______________________________________________________#

class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class CreateRatingForm(FlaskForm):
    town = StringField('Town Name', validators=[DataRequired()])
    map_url = StringField('Map Link', validators=[DataRequired()])
    opening_hours = StringField('Opening and Closing (24h Format 00:00)', validators=[DataRequired()])
    equipment = SelectField('Equipment', coerce=str, choices=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], validators=[DataRequired()])
    state_of_repair = SelectField('State Of Repair', coerce=str, choices=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], validators=[DataRequired()])
    toilets = SelectField('Toilets', coerce=str, choices=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], validators=[DataRequired()])
    lighting = SelectField('Lighting', coerce=str, choices=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], validators=[DataRequired()])
    bins = SelectField('Bins', coerce=str, choices=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"], validators=[DataRequired()])
    comments = CKEditorField("Extra Comments", validators=[DataRequired()])
    submit = SubmitField("Submit Rating")


class CreateCommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")


class CreateUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    confirm_password = StringField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Sign me up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log me in")


#_____________________________________Definition of Functions______________________________________________#


def send_email(name, email, subject, message):
    email_message = f"Subject: New Message\n\nName: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}"
    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=EMAIL_PW)
        connection.sendmail(from_addr=MY_EMAIL, to_addrs=MY_EMAIL, msg=email_message)
        connection.close()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#____________________________________Flask Server Routes___________________________________________________#
@app.route("/")
def home():
    recent_posts = db.session.query(BlogPost).order_by(BlogPost.date.desc()).limit(3).all()
    return render_template("index.html", posts=recent_posts, current_user=current_user)


@app.route("/register", methods=['GET', 'POST'])
def register():
    reg_form = CreateUserForm()
    if reg_form.validate_on_submit():
        if User.query.filter_by(email=reg_form.email.data).first():
            print(User.query.filter_by(email=reg_form.email.data).first())
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            reg_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name=reg_form.name.data,
            email=reg_form.email.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=reg_form, current_user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flask.flash("That email does not exist, please try again")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flask.flash("Password incorrect, please try again")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/ratings")
def ratings():
    all_ratings = db.session.query(PlaygroundRating).all()
    return render_template("ratings.html", ratings=all_ratings, current_user=current_user)

@app.route('/contact', methods=['GET', 'POST'])
def get_contact_info():
    try:
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        send_email(name, email, subject, message)
        return "Message sent successfully"
    except Exception:
        return "An error has occured"

@app.route('/blog')
def get_blog():
    posts = db.session.query(BlogPost).all()
    return render_template('blog.html', all_posts=posts, current_user=current_user)

@app.route('/blog-post/<int:index>', methods=['GET', 'POST'])
def get_blog_post(index):
    comment_form = CreateCommentForm()
    requested_post = BlogPost.query.get(index)
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login to comment")
            return redirect(url_for('login'))

        new_comment = Comment(
            comment=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()

    return render_template('blog-post.html', post=requested_post, form=comment_form, current_user=current_user)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post_to_edit = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        author=post_to_edit.author,
        img_url=post_to_edit.img_url,
        body=post_to_edit.body
    )
    if request.method =='POST':
        title = edit_form.title.data
        subtitle = edit_form.subtitle.data
        body = edit_form.body.data
        author = edit_form.author.data
        img_url = edit_form.img_url.data
        post_to_edit.title = title
        post_to_edit.subtitle = subtitle
        post_to_edit.body = body
        post_to_edit.author = author
        post_to_edit.img_url = img_url
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('make-post.html', id=post_id, form=edit_form, current_user=current_user)


@app.route("/new-post", methods=['GET', 'POST'])
def create_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login to create a new post")
            return redirect(url_for('login'))
        new_blog =BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            date=datetime.datetime.today().strftime('%B-%d-%Y'),
            author=current_user,
            img_url=form.img_url.data,
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('get_blog'))
    return render_template('make-post.html', form=form, current_user=current_user)

@app.route('/delete-post')
def delete_blog_post():
    post_id = request.args.get('index')
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_blog'))

@app.route('/new-rating', methods=['GET','POST'])
def create_new_rating():
    form = CreateRatingForm()
    if request.method == 'POST':
        town = form.town.data
        map_url = form.map_url.data
        opening_hours = form.opening_hours.data
        equipment = form.equipment.data
        state_of_repair = form.state_of_repair.data
        toilets = form.toilets.data
        lighting = form.lighting.data
        bins = form.bins.data
        comments = form.comments.data
        new_rating = PlaygroundRating(
            town=town,
            map_url=map_url,
            opening_hours=opening_hours,
            equipment=equipment,
            state_of_repair=state_of_repair,
            toilets=toilets,
            lighting=lighting,
            bins=bins,
            comments=comments
        )
        db.session.add(new_rating)
        db.session.commit()
        return redirect(url_for('ratings'))

    return render_template('make-rating.html', form=form, current_user=current_user)


@app.route('/edit-rating/<int:rating_id>', methods=['GET', 'POST'])
def edit_rating(rating_id):
    rating_to_edit = PlaygroundRating.query.get(rating_id)
    edit_form = CreateRatingForm(
        town=rating_to_edit.town,
        map_url=rating_to_edit.map_url,
        opening_hours=rating_to_edit.opening_hours,
        equipment=rating_to_edit.equipment,
        state_of_repair=rating_to_edit.state_of_repair,
        toilets=rating_to_edit.toilets,
        lighting=rating_to_edit.lighting,
        bins=rating_to_edit.bins,
        comments=rating_to_edit.comments
    )
    if request.method =='POST':
        town = edit_form.town.data
        map_url = edit_form.map_url.data
        opening_hours = edit_form.opening_hours.data
        equipment = edit_form.equipment.data
        state_of_repair = edit_form.state_of_repair.data
        toilets = edit_form.toilets.data
        lighting = edit_form.lighting.data
        bins = edit_form.bins.data
        comments = edit_form.comments.data

        rating_to_edit.town = town
        rating_to_edit.map_url = map_url
        rating_to_edit.opening_hours = opening_hours
        rating_to_edit.equipment = equipment
        rating_to_edit.state_of_repair = state_of_repair
        rating_to_edit.toilets = toilets
        rating_to_edit.lighting = lighting
        rating_to_edit.bins = bins
        rating_to_edit.comments = comments
        db.session.commit()
        return redirect(url_for('ratings'))

    return render_template('make-rating.html', id=rating_id, form=edit_form, current_user=current_user)

@app.route('/delete-rating')
def delete_rating():
    rating_id = request.args.get('rating_id')
    rating_to_delete = PlaygroundRating.query.get(rating_id)
    db.session.delete(rating_to_delete)
    db.session.commit()
    return redirect(url_for('ratings'))



if __name__ == '__main__':
   app.run(debug=True)
