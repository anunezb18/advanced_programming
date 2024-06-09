"""This file  has theentry point implementtion for RESTapi services."""

from typing import List
from fastapi import Body, FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from film import Film, FilmDB, SearchModel, AddToWatchlistModel
from review import Review
from user import User, UserDB, LoginModel

app = FastAPI()

engine_users = create_engine(
    "postgresql://postgres:123k@host.docker.internal:5432/project-users"
)
engine_films = create_engine(
    "postgresql://postgres:123@host.docker.internal:5432/project-films"
)


@app.get("/hello_ud")
def hello_ud():
    """This is a healthcheck service just to validade is backend is up"""
    return "Welcome to UD!"

@app.post("/users/register")
def register_user(user: User = Body(...)):
    """This method registers a new user"""

    session_maker = sessionmaker(bind=engine_users)
    session = session_maker()

    existing_user = session.query(UserDB).filter_by(username=user.username).first()
    if existing_user is not None:
        return {"message": "Username is already in use. Please choose another one."}

    new_user = UserDB(
        username=user.username,
        password=user.password,
        email=user.email,
    )
    session.add(new_user)
    session.commit()
    session.close()
    return {"message": "User registered successfully"}


@app.post("/users/login")
def login(user: LoginModel):
    """This method logs in a user"""
    dbusername = user.username
    dbpassword = user.password

    session_maker = sessionmaker(bind=engine_users)
    session = session_maker()
    user_db = session.query(UserDB).filter_by(username=dbusername).first()
    session.close()

    if user_db is not None and user_db.password == dbpassword:
        return {"message": "User logged in successfully"}

    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/films/search", response_model=List[Film])
def search_films(search: SearchModel):
    """This method search a film by the title"""

    if not search.title.strip():
        raise HTTPException(
            status_code=400, detail="Title must not be empty or only whitespace"
        )

    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()
    films_db = session.query(FilmDB).filter(FilmDB.title.contains(search.title)).all()
    session.close()

    films = [Film(**film_db.__dict__) for film_db in films_db]

    return films


@app.get("/films/{film_id}", response_model=Film)
def get_film_details(film_id: int):
    """This method returns all the details of a film"""

    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()
    film = session.query(FilmDB).filter(FilmDB.code == str(film_id)).first()
    session.close()

    if film is None:
        raise HTTPException(status_code=404, detail=f"Film with id {film_id} not found")

    film_dict = {c.name: getattr(film, c.name) for c in FilmDB.__table__.columns}

    return film_dict


@app.post("/films/{film_id}/review")
def add_film_review(film_id: int, review: Review = Body(...)):
    """This method adds a review to a film"""
    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()
    film = session.query(FilmDB).filter(FilmDB.code == str(film_id)).first()

    if film is None:
        session.close()
        raise HTTPException(status_code=404, detail=f"Film with id {film_id} not found")

    new_review = f"{review.username}: {review.text}"

    if not film.reviews or film.reviews == "{}":
        film.reviews = [new_review]
    else:
        film.reviews.append(new_review)

    session.commit()
    session.close()

    return {"message": "Review added successfully"}


@app.get("/films/{film_id}/reviews")
def get_film_reviews(film_id: int):
    """This method returns the reviews of a film"""
    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()
    film = session.query(FilmDB).filter(FilmDB.code == str(film_id)).first()

    if film is None:
        session.close()
        raise HTTPException(status_code=404, detail=f"Film with id {film_id} not found")

    reviews = film.reviews
    session.close()
    return {"reviews": reviews}


@app.post("/users/add_to_watchlist")
def add_to_watchlist(item: AddToWatchlistModel):
    """This method adds a movie to a user's watchlist"""
    dbusername = item.username
    film_id = item.film_id
    film_title = item.film_title

    session_maker = sessionmaker(bind=engine_users)
    session = session_maker()
    user_db = session.query(UserDB).filter_by(username=dbusername).first()

    if user_db is None:
        session.close()
        raise HTTPException(status_code=404, detail="User not found")

    film_info = f"Title: {film_title}, Code: {film_id}"
    if not user_db.watchlist or user_db.watchlist == "{}":
        user_db.watchlist = [film_info]
    else:
        user_db.watchlist.append(film_info)
    session.commit()

    session.close()
    return {"message": "Film added to watchlist successfully"}


@app.get("/users/{username}/watchlist")
def get_watchlist(username: str):
    """This method returns a user's watchlist"""
    session_maker = sessionmaker(bind=engine_users)
    session = session_maker()
    user_db = session.query(UserDB).filter_by(username=username).first()

    if user_db is None:
        session.close()
        raise HTTPException(status_code=404, detail="User not found")

    watchlist = user_db.watchlist
    session.close()
    return {"watchlist": watchlist}


@app.post("/admin/films")
def add_film_to_catalog(film: Film = Body(...)):
    """This method adds a film to the catalog"""

    new_film = FilmDB(
        title=film.title,
        code=film.code,
        director=film.director,
        year=film.year,
        synopsis=film.synopsis,
        ratings=None,
        reviews=None,
        lenght=film.lenght,
        crew=film.crew,
    )

    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()

    session.add(new_film)
    session.commit()

    return {"message": "Film added to catalog successfully"}


@app.get("/films")
def get_all_films():
    """This method returns all the films in the catalog"""

    session_maker = sessionmaker(bind=engine_films)
    session = session_maker()
    films_db = session.query(FilmDB).all()
    session.close()

    films = [
        {k: v for k, v in film_db.__dict__.items() if not k.startswith("_")}
        for film_db in films_db
    ]

    return films
