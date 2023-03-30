from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.exc import OperationalError, IntegrityError
import requests

API_KEY = "OWN API KEY"
API_MOVIE_URL = 'https://api.themoviedb.org/3/search/movie'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'OWN SECRET KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)

#CREATE A TABLE CALLED MOVIE WITH ID AS PRIMARY KEY AND OTHER ATTRIBUTES
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self): 
        return f'<Book {self.title}, with ID: {self.id}'

#CREATE A FORM FOR ADDING A MOVIE, IN THE *.HTML FILE WE USE QUICK FORM, BUT WE NEED PASS A FORM AS KEYWORD ARG INTO RENDER REMPLATE 
class AddMovieForm(FlaskForm):
    title = StringField(label="Movie name", validators=[DataRequired()])
    submit = SubmitField(label="Add movie")

#CREATE A FORM FOR RATING A MOVIE, IN THE *.HTML FILE WE USE QUICK FORM, BUT WE NEED PASS A FORM AS KEYWORD ARG INTO RENDER REMPLATE 
class RateMovieForm(FlaskForm):
    rating = StringField(label="Your rating out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Done")

#CREATES A DATABASE
with app.app_context():
    db.create_all()

#AFTER WE SELECTED ID OF FILM IN MOVIE DATABASE, WE GET INFO ABOUT FILM VIA API AND THEN ADD THAT DATA INTO OUR DATABASE
def add_data_into_database(movie_id):

    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", params={"api_key": API_KEY})
    data = response.json()

    try:
        with app.app_context():
            #CREATE A NEW RECORD ABOUT BOOK
            new_record = Movie(
                id = movie_id,
                title = data['original_title'],
                year = data['release_date'].split("-")[0], 
                description = data['overview'], 
                img_url = "https://image.tmdb.org/t/p/w500/" + data["poster_path"]
            )
            #COMMITING ALL CHANGES IN DATABASE
            db.session.add(new_record)
            db.session.commit()
    #IN CASE IF WE HAVE TWO SILILAR IDS IN DB       
    except(IntegrityError):
        pass

#RENDER ALL MOVIES IN HOME.HTML URL. IF NOT FILMS, WILL RETURN EMPTY LIST. IF WE HAVE SOME FILMS, WE COUNT A ORDER BY RATING AND DISPLAY THEM 
def get_movies():
    try:
        #WILL CREATE A LIST OF MOVIES ORDERED BY HIGHER -> LOWER
        all_movies = Movie.query.order_by(Movie.rating.desc()).all()
        for index, movie in enumerate(all_movies):
            movie.ranking = index + 1
        db.session.commit()
        return all_movies
    except(OperationalError):
        return []

#WE CHANGE A RATING OF A MOVIE. WHEN WE ADD A NEW MOVIE, OUR RATING DOES NOT EXIST, SO WE ADD THE RATING THERE
def change_rating(movie, form):
    #PASSING FORM WITH DATA FROM WEBSITE
    movie.rating= float(form.rating.data)
    movie.review = form.review.data
    db.session.commit()

#WILL SEARCH MOVIE BY ID IN DATABASE AND DELETE THIS RECORD
def delete_movie(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

#WILL LOOK FOR ALL FILMS WITH MOVIE NAME, THEN WE CAN CHOOSE ONE OF RENDERED FILMS AND ADD THAT FILM INTO OUR DATABASE
def get_movies_from_request(movie_name):
    response = requests.get(API_MOVIE_URL, params={"api_key": API_KEY, "query": movie_name})
    return response.json()["results"]
   
@app.route("/")
def home():
    return render_template("index.html", movies=get_movies())

@app.route("/add", methods=["GET", "POST"])
def add():
    #CREATE A FORM FOR ADDING A MOVIE
    movie_form = AddMovieForm()
    #AFTER PRESSING A SUBMIT BUTTON ON FORM WILL CHECK FOR INPUT 
    if (movie_form.validate_on_submit() == True):
        #RENDER ALL MOVIES WITH TITLE IN FORM
        movies = get_movies_from_request(movie_form.title.data)
        return render_template("select.html", movies=movies)
    
    #IF IS NOT A POST METHOD, BUT A GET(WE RENDER A FORM)
    return render_template("add.html", form=movie_form)

@app.route("/edit<int:id>", methods=["GET", "POST"])
def edit(id):
    #WE WILL GET AN ID OF FILM IN OUR DATABASE TO EDIT A RATING
    movie_to_update = Movie.query.get(id)
    edit_form = RateMovieForm()

    if (edit_form.validate_on_submit() == True):
        change_rating(movie_to_update, edit_form)
        #AFTER SUCCESFULLY UPDATING A RATING WE WILL REDIRECT INTO HOMEPAGE AND DISPLAY ALL FILMS
        return redirect(url_for("home"))

    #IF WE ARE ON GET METHOD ON WEBSITE 
    return render_template("edit.html", form=edit_form, movie=movie_to_update)

@app.route("/delete<int:id>", methods=["GET", "POST"])
def delete(id):
    #GET AN ID OF FILM IN OUR DATABASE AND THE RECORD WITH THIS ID WILL BE REMOVED
    delete_movie(movie_id=id)
    return redirect(url_for("home"))

@app.route("/find<int:id>", methods=["GET", "POST"])
def find_movie(id):
    #GET A FILM ID ON API DATABASE SERVER, WE SEND A REQUEST FOR THAT DATA AND WE STORE THEM INTO DATABASE. ID IN OUR DATABASE IS SAME AS ID ON API 
    add_data_into_database(id)
    #BECAUSE WHEN WE ADD A FILM FROM API, IT DOESNOT HAVE OUR RATING, SO WE WILL IMMEDIATELY FIX THAT
    return redirect(url_for("edit", id=id))

if __name__ == '__main__':
    app.run(debug=True)
