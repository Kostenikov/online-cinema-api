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

from database import Base


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(    Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user: Mapped[UserModel] = relationship("UserModel", back_populates="shopping_cart")

    cart_items: Mapped[list["CartItemModel"]] = relationship("CartItemModel", back_populates="cart")


class CartItemModel(Base):
    __tablename__ = "cart_items"
    __table_args__ = [
        UniqueConstraint("cart_id", "movie_id", name="unique_movie_in_cart"),
    ]

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)
    cart: Mapped[CartModel] = relationship("CartModel", back_populates="cart_items")

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    movie: Mapped[MovieModel] = relationship("MovieModel", back_populates="cart_items")

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
