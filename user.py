from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select

class User(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    name: str 
    email: str

app = FastAPI()

database_url = "sqlite:///./users.db"
engine = create_engine(database_url, connect_args= {
    "check_same_thread": False
})

SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/users", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    for check_user in users:
        if check_user.email == user.email:
            raise HTTPException(
                status_code = 409,
                detail = "User already exists"
            )
    try:
        session.add(user)
        session.commit()
        session.refresh(user)    
    except:
        raise HTTPException(
            status_code = 500,
            detail = "An unexpected error occured"
        )
    return user

@app.get("/users", response_model=list[User])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    if not users:
        raise HTTPException(
            status_code = 200,
            detail = "There are currently no users"
        )
    return users

@app.get("/users/{id}", response_model=User)
def get_user(id: int, session: Session = Depends(get_session)):
    user = session.get(User, id)
    if not user:
        raise HTTPException(status_code = 404, detail="User not found")
    return user

@app.put("/users/{id}", response_model=User)
def update_user(id: int, updated_user: User, session: Session = Depends(get_session)):
    user = get_user(id, session)
    try:
        for field, value in updated_user.model_dump().items():
            setattr(user, field, value)
        if user.id != id:
            raise HTTPException()
        session.commit()
        session.refresh(user)
    except:
        raise HTTPException(
            status_code = 500,
            detail = "An unexpected error occured"
        )
    return user

@app.delete("/users/{id}", response_model=list[User])
def delete_user(id: int, session: Session = Depends(get_session)):
    user = get_user(id, session)
    session.delete(user)
    session.commit()
    users = session.exec(select(User)).all()
    return users


