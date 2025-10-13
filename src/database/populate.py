import asyncio

from sqlalchemy import func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import UserGroupEnum, UserGroupModel, get_db_contextmanager

CHUNK_SIZE = 1000


class CSVDatabaseSeeder:
    """
    A class responsible for seeding the database from a CSV file using asynchronous SQLAlchemy.
    """

    def __init__(self, csv_file_path: str, db_session: AsyncSession) -> None:
        """
        Initialize the seeder with the path to the CSV file and an async database session.

        :param csv_file_path: The path to the CSV file containing movie data.
        :param db_session: An instance of AsyncSession for performing database operations.
        """
        self._csv_file_path = csv_file_path
        self._db_session = db_session

    async def is_db_populated(self) -> bool:
        """
        Check if the MovieModel table has at least one record.

        :return: True if there's already at least one movie in the database, otherwise False.
        """
        result = await self._db_session.execute(select(UserGroupModel).limit(1))
        first_movie = result.scalars().first()
        return first_movie is not None

    async def _seed_user_groups(self) -> None:
        """
        Seed the UserGroupModel table with default user groups if none exist.

        This method checks whether any user groups are already present in the database.
        If no records are found, it inserts all groups defined in the UserGroupEnum.
        After insertion, the changes are flushed to the current transaction.
        """
        count_stmt = select(func.count(UserGroupModel.id))
        result = await self._db_session.execute(count_stmt)
        existing_groups = result.scalar()

        if existing_groups == 0:
            groups = [{"name": group.value} for group in UserGroupEnum]
            await self._db_session.execute(insert(UserGroupModel).values(groups))
            await self._db_session.commit()

            print("User groups seeded successfully.")

    async def seed(self) -> None:
        """
        Main method to seed the database with movie data from the CSV.
        It pre-processes the CSV, prepares reference data (countries, genres, actors, languages),
        inserts all movies, then inserts many-to-many relationships (genres, actors, languages).
        """
        try:
            if self._db_session.in_transaction():
                print("Rolling back existing transaction.")
                await self._db_session.rollback()

            await self._seed_user_groups()

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


async def main() -> None:
    """
    The main async entry point for running the database seeder.
    Checks if the database is already populated, and if not, performs the seeding process.
    """
    settings = get_settings()
    async with get_db_contextmanager() as db_session:
        seeder = CSVDatabaseSeeder(settings.PATH_TO_MOVIES_CSV, db_session)

        if not await seeder.is_db_populated():
            try:
                await seeder.seed()
                print("Database seeding completed successfully.")
            except Exception as e:
                print(f"Failed to seed the database: {e}")
        else:
            print("Database is already populated. Skipping seeding.")


if __name__ == "__main__":
    asyncio.run(main())
