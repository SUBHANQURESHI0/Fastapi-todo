from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
from dailydo_todos_app import settings
from typing import Annotated
from contextlib import asynccontextmanager


# Create Model


class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(index=True, min_length=3, max_length=54)
    is_completed: bool = Field(default=False)


connecetion_string: str = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg")
# engine is one for whole application
engine = create_engine(connecetion_string, connect_args={
                       "sslmode": "require"}, pool_recycle=300, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)


# todo1 : Todo = Todo(content = "first task")
# todo2 : Todo = Todo(content = "second task")

# #session: seperate session for each transaction
# session = Session(engine)

# #create todos in database
# print(f'Before commit {todo1}')
# session.add(todo1)
# session.add(todo2)
# session.commit()
# session.refresh(todo1)
# print(f'After commit {todo1}')
# session.close()


def get_session():
    with Session(engine) as session:
      yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"creating tables")
    create_tables()
    print("Tables Create")
    yield

app = FastAPI(lifespan=lifespan, title="DailyDo Todos App", version="1.0.0")


@app.get('/')
async def root():
    return {"message": "Welcome to the dailyDo todo app"}


@app.post('/todos/', response_model=Todo)
async def create_todos(todo: Todo, session: Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get("/todos/", response_model=list[Todo])
async def get_all(session: Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    return todos


@app.get("/todos/{id}", response_model=Todo)
async def get_single_todo(id: int, session: Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id == id)).first()
    return todo


@app.put("/todos/{id}")
async def edit_todo(id: int, todo: Todo, session: Annotated[Session, Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException (status_code=404, detail="No task found")
        


@app.delete("/todos/{id}")
async def delete_todo(id:int,session: Annotated[Session, Depends(get_session)]):
    todo = session.exec(select(Todo).where(Todo.id == id)).first()
    if todo: 
        session.delete(todo)
        session.commit()
        # session.refresh(todo)
        return {"message": "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="Task Not found")
    
