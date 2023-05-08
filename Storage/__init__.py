import logging
import uuid
from typing import Optional

from pymongo import MongoClient, collection, database
from pymongo.errors import PyMongoError

DEFAULT_DATABASE_NAME = "Mafia"
DEFAULT_ENTITY_COLLECTION = "Entities"

logger = logging.getLogger(__name__)

_connection: MongoClient = MongoClient('localhost', 27017, uuidRepresentation="standard")
_database: database = _connection.get_database(DEFAULT_DATABASE_NAME)

_database_name: str = DEFAULT_DATABASE_NAME
_entity_collection_name: str = DEFAULT_ENTITY_COLLECTION


def configure_database(database_: str = _database_name,
                       entity_collection: str = _entity_collection_name):
    global _database, _database_name, _entity_collection_name
    _database_name = database_
    _entity_collection_name = entity_collection
    _database = _connection.get_database(database_)
    logger.info(f"Setup database as {database_} and {entity_collection}")


def save_entity(entity_data: dict):
    if "id" not in entity_data:
        raise KeyError("entity_data must have id field")
    try:
        collection_: collection = _database.get_collection(_entity_collection_name)
        collection_.update_one({"id": entity_data["id"]}, {"$set": entity_data}, upsert=True)
        return True
    except PyMongoError as e:  # pragma: no cover
        logger.critical(f"Database error: {e}")
        logger.error(f"Entity data: {entity_data}")
        # close app


def remove_entity(uuid_: uuid):
    try:
        collection_: collection = _database.get_collection(_entity_collection_name)
        collection_.delete_one({"id": uuid_})
        return True
    except PyMongoError as e:  # pragma: no cover
        logger.critical(f"Database error: {e}")
        logger.error(f"Failed to delete entity with id: {uuid_}")
        # close app


def load_entity(uuid_: uuid) -> Optional[dict]:
    try:
        collection_: collection = _database.get_collection(_entity_collection_name)
        entity_data: dict = collection_.find_one({"id": uuid_})
        if entity_data is None:
            logger.warning(f"Tried to load nonexistent entity with uuid: {uuid_}")
            return None
        return entity_data
    except PyMongoError as e:  # pragma: no cover
        logger.critical(f"Database error: {e}")
        logger.error(f"failed to load entity with id: {uuid_}")
        # close app


def load_all_entities() -> tuple[dict, ...]:
    try:
        entities = []
        collection_: collection = _database.get_collection(_entity_collection_name)
        documents = collection_.find({})
        for doc in documents:
            entities.append(dict(doc))
        return tuple(entities)
    except PyMongoError as e:  # pragma: no cover
        logger.critical(f"Database error: {e}")
        logger.error("Failed to load all entities")
        # close app


# meant for testing to rest database
def clear_entity_collection():
    _database.get_collection(_entity_collection_name).delete_many({})
