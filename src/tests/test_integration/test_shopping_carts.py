import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import CartItemModel, CartModel, MovieModel, OrderItemModel, OrderModel, OrderStatusEnum, UserModel
from main import app
from security.interfaces import JWTAuthManagerInterface


@pytest.mark.asyncio
class TestGetCarts:
    """Test suite for GET /carts/ endpoint."""

    async def test_get_carts_user(
        self,
        user: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that fetching carts by regular user returns code 403.

        Create user and get all carts
        """
        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.get(
            app.url_path_for("moderator_get_carts"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Admin or moderator role required"

    async def test_get_carts_no_carts_exists(
        self,
        moderator: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that fetching carts when no carts exist returns status 404.

        Create moderator user and get all carts
        """
        access_token = jwt_manager.create_access_token({"user_id": moderator.id})

        response = await client.get(
            app.url_path_for("moderator_get_carts"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_get_carts(
        self,
        user: UserModel,
        moderator: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test if moderator can see users carts by fetching.

        Create moderator, user and get all carts.
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": moderator.id})

        response = await client.get(
            app.url_path_for("moderator_get_carts"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == 1


@pytest.mark.asyncio
class TestGetCart:
    """Test suite for GET /cart/ endpoint."""

    async def test_get_cart_creates_new_cart_if_not_exists(
        self,
        user: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that fetching a cart creates a new empty cart if one doesn't exist.

        Given a user without an existing cart
        When they request their cart
        Then a new empty cart should be created and returned
        """
        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.get(
            app.url_path_for("get_cart"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert data["cart_items"] == []
        assert "id" in data

    async def test_get_cart_returns_existing_cart_with_items(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test that fetching a cart returns existing cart with items.

        Given a user with an existing cart containing items
        When they request their cart
        Then the cart with all items should be returned
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.get(
            app.url_path_for("get_cart"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert len(data["cart_items"]) == 1
        assert data["cart_items"][0]["movie_id"] == movie.id
        assert data["cart_items"][0]["title"] == movie.name

    async def test_get_cart_requires_authentication(self, client: AsyncClient):
        """
        Test that accessing cart without authentication returns 401.

        Given no authentication token
        When requesting the cart
        Then a 403 Unauthorized response should be returned
        """
        response = await client.get(
            app.url_path_for("get_cart"),
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestAddItemToCart:
    """Test suite for POST /cart/items/ endpoint."""

    async def test_add_item_to_cart_success(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test successfully adding an item to the cart.

        Given a valid movie and authenticated user
        When adding the movie to cart
        Then the item should be added successfully
        """
        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.post(
            app.url_path_for("add_item_to_cart", item_id=movie.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Item added to your cart successfully."

        cart_item = await db_session.scalar(
            select(CartItemModel)
            .join(CartModel)
            .where(CartModel.user_id == user.id, CartItemModel.movie_id == movie.id)
        )
        assert cart_item is not None

    async def test_add_item_creates_cart_if_not_exists(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test that adding an item creates a cart if one doesn't exist.

        Given a user without a cart
        When adding an item
        Then a cart should be created and the item added
        """

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.post(
            app.url_path_for("add_item_to_cart", item_id=movie.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 201

        cart = await db_session.scalar(select(CartModel).where(CartModel.user_id == user.id))
        assert cart is not None

    async def test_add_nonexistent_item_returns_404(
        self,
        user: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that adding a nonexistent item returns 404.

        Given an invalid movie ID
        When attempting to add it to cart
        Then a 404 error should be returned
        """
        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.post(
            app.url_path_for("add_item_to_cart", item_id=-2),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Item does not exist"

    async def test_add_duplicate_item_returns_400(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test that adding an item already in cart returns 400.

        Given an item already in the user's cart
        When attempting to add it again
        Then a 400 error should be returned
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.post(
            app.url_path_for("add_item_to_cart", item_id=movie.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Item already in your cart."

    async def test_add_purchased_item_returns_400(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test that adding an already purchased item returns 400.

        Given an item the user has already purchased
        When attempting to add it to cart
        Then a 400 error should be returned
        """
        order = OrderModel(user_id=user.id, status=OrderStatusEnum.PAID, total_amount=1.0)
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        order_item = OrderItemModel(order_id=order.id, movie_id=movie.id, price_at_order=1.0)
        db_session.add(order_item)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.post(
            app.url_path_for("add_item_to_cart", item_id=movie.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "You have already purchased this item."


@pytest.mark.asyncio
class TestRemoveItemFromCart:
    """Test suite for DELETE /cart/items/{item_id}/ endpoint."""

    async def test_remove_item_from_cart_success(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test successfully removing an item from the cart.

        Given an item in the user's cart
        When removing the item
        Then it should be deleted successfully
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.delete(
            app.url_path_for("remove_item_from_cart", item_id=cart_item.id),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Item removed from your cart successfully."

    async def test_remove_nonexistent_item_returns_404(
        self,
        user: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that removing a nonexistent item returns 404.

        Given a user with a cart
        When attempting to remove a nonexistent item
        Then a 404 error should be returned
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.delete(
            app.url_path_for("remove_item_from_cart", item_id=-1),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Item does not exist."


@pytest.mark.asyncio
class TestClearCart:
    """Test suite for DELETE /cart/clear/ endpoint."""

    async def test_clear_cart_success(
        self,
        user: UserModel,
        movie: MovieModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
        seed_database: AsyncSession,
    ):
        """
        Test successfully clearing all items from cart.

        Given a cart with multiple items
        When clearing the cart
        Then all items should be removed
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)

        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.delete(
            app.url_path_for("clear_cart"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204

        remaining_items = await db_session.scalars(select(CartItemModel).where(CartItemModel.cart_id == cart.id))
        assert len(list(remaining_items)) == 0

    async def test_clear_empty_cart_success(
        self,
        user: UserModel,
        client: AsyncClient,
        db_session: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        seed_user_groups: AsyncSession,
    ):
        """
        Test that clearing an already empty cart succeeds.

        Given a user with an empty cart
        When clearing the cart
        Then the operation should succeed without errors
        """
        cart = CartModel(user_id=user.id)
        db_session.add(cart)
        await db_session.commit()

        access_token = jwt_manager.create_access_token({"user_id": user.id})

        response = await client.delete(
            app.url_path_for("clear_cart"),
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 204
