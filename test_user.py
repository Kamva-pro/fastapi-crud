import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from user import User, app, get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_user(client: TestClient):
    response = client.post("/users", json= {
        "name": "User 1",
        "email": "user@example.com"
    })
    data = response.json()
    assert response.status_code == 200
    assert data['name'] == "User 1"
    assert data["email"] == "user@example.com"


def test_get_users(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    user_2 = User(name= "Ben Dover", email= "dendover@example.com")
    user_3 = User(name= "Tester", email= "tester@example.com")

    session.add(user_1)
    session.add(user_2)
    session.add(user_3)
    session.commit()

    response = client.get("/users")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 3


def test_get_user(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    session.add(user_1)
    session.commit()

    response = client.get(f"/users/{user_1.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == user_1.name


def test_update_name(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    session.add(user_1)
    session.commit()

    response = client.put(f"/users/{user_1.id}", json={"name": "New Name"})
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "New Name"
    assert data["email"] == "johndoe@example.com"

def test_update_email(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    session.add(user_1)
    session.commit()

    response = client.put(f"/users/{user_1.id}", json={"email": "newmail@example.com"})
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "John Doe"
    assert data["email"] == "newmail@example.com"

def test_update_id(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    session.add(user_1)
    session.commit()

    response = client.put(f"/users/{user_1.id}", json={"id": 5})
    assert response.status_code == 500

def test_delete_user(session: Session, client: TestClient):
    user_1 = User(name= "John Doe", email= "johndoe@example.com")
    session.add(user_1)
    session.commit()

    response = client.delete(f"/users/{user_1.id}")

    db_user = session.get(User, user_1.id)

    assert response.status_code == 200

    assert db_user is None