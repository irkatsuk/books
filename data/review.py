import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Review(SqlAlchemyBase):
    __tablename__ = 'review'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("users.id"))
    book_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("books.id"))
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user = orm.relation('User')
    books = orm.relation('Books')
