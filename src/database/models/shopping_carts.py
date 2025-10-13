from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base, MovieModel, UserModel


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="shopping_cart",
    )

    cart_items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="cart",
    )

    def __repr__(self):
        return f"<CartModel(id={self.id}, user_id={self.user_id}, items={len(self.cart_items)})>"


class CartItemModel(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "movie_id",
            name="unique_movie_in_cart",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id"),
        nullable=False,
    )
    cart: Mapped[CartModel] = relationship(
        "CartModel",
        back_populates="cart_items",
    )

    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False,
    )
    movie: Mapped[MovieModel] = relationship(
        "MovieModel",
        back_populates="cart_items",
    )

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return (
            f"<CartItemModel(id={self.id}, cart_id={self.cart_id}, "
            f"movie_id={self.movie_id}, added_at={self.added_at})>"
        )
