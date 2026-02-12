import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, ClassVar, Generic, Self, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


TModel = TypeVar("TModel", bound=BaseModel)


class DBError(Exception):
    pass

class NotFoundError(DBError):
    pass

class BaseMongoDBManager(Generic[TModel]):

    model: ClassVar[type[TModel]]
    collection_name: ClassVar[str | None] = None


    indexes: ClassVar[list[dict[str, Any]]] = []

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._db = db
        self._collection: AsyncIOMotorCollection | None = None

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            name = self.collection_name or f"{self.model.__name__.lower()}s"
            self._collection = self._db.get_collection(name)
        return self._collection

    async def ensure_indexes(self) -> None:
        for spec in self.indexes:
            keys: list[tuple[str, int]] = spec["keys"]
            kwargs: dict[str, Any] = spec.get("kwargs", {})
            await self.collection.create_index(keys, **kwargs)

    def _to_doc(self, obj: TModel) -> dict[str, Any]:
        return obj.model_dump()

    def _from_doc(self, doc: dict[str, Any]) -> TModel:
        return self.model.model_validate(doc)

    async def create(self, data: TModel | dict[str, Any]) -> TModel:
        obj = data if isinstance(data, BaseModel) else self.model.model_validate(data)

        now = utcnow()
        payload = self._to_doc(obj)
        payload.setdefault("created", now)
        payload["updated"] = now

        try:
            await self.collection.insert_one(payload)
        except DuplicateKeyError as e:
            raise ValueError("Duplicate key while creating document") from e

        return self._from_doc(payload)

    async def get(self, *, id_: str | None = None, raise_not_found: bool = False, **filter_by) -> TModel | None:

        filter_by: dict = dict(filter_by)
        if id_:
            filter_by["id"] = id_

        doc = await self.collection.find_one(filter_by)

        if doc is None and raise_not_found:
            raise NotFoundError(f"{self.model.__name__} with id {id_} not found")
        return self._from_doc(doc) if doc else None

    async def exists(self, *, id_: str) -> bool:
        doc = await self.collection.find_one({"id": id_}, projection={"id": 1})
        return doc is not None

    async def list_(
        self,
        *,
        filter_by: dict[str, Any] | None = None,
        sort: Sequence[tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int = 100,
        projection: dict[str, int] | None = None,
    ) -> list[TModel]:
        query = filter_by or {}
        cursor = self.collection.find(query, projection=projection)

        if sort:
            cursor = cursor.sort(list(sort))
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        docs = await cursor.to_list(length=limit if limit else 0)
        return [self._from_doc(d) for d in docs]

    async def update(
        self,
        *,
        id_: str | None = None,
        search_by: dict[str, Any] | None = None,
        patch: dict[str, Any],
        upsert: bool = False,
        return_new: bool = True,
    ) -> TModel | None:
        patch_doc = dict(patch)
        patch_doc["updated"] = utcnow()

        patch_doc.pop("id", None)
        patch_doc.pop("created", None)

        search_by = search_by or {}

        if id_:
            search_by["id"] = id_

        if return_new:
            doc = await self.collection.find_one_and_update(
                search_by,
                {"$set": patch_doc},
                upsert=upsert,
                return_document=True,
            )
            return self._from_doc(doc) if doc else None

        res = await self.collection.update_one({"id": id_}, {"$set": patch_doc}, upsert=upsert)
        if res.matched_count == 0 and not upsert:
            raise NotFoundError(f"{self.model.__name__} with id {id_} not found")
        return await self.get(id_=id_)

    async def replace(self, *, id_: str, data: TModel | dict[str, Any], upsert: bool = False) -> TModel | None:
        existing = await self.get(id_=id_)
        now = utcnow()

        payload = self._to_doc(data) if isinstance(data, BaseModel) else dict(data)
        payload["id"] = id
        payload["updated"] = now
        payload["created"] = existing.created if existing else payload.get("created", now)

        payload = self._to_doc(self.model.model_validate(payload))

        res = await self.collection.replace_one({"id": id}, payload, upsert=upsert)
        if res.matched_count == 0 and not upsert:
            raise NotFoundError(f"{self.model.__name__} with id {id_} not found")
        return self._from_doc(payload)

    async def delete(self, *, id_: str) -> bool:
        res = await self.collection.delete_one({"id": id_})
        return res.deleted_count == 1

    async def delete_many(self, *, filter_by: dict[str, Any]) -> int:
        res = await self.collection.delete_many(filter_by)
        return int(res.deleted_count)

    async def count(self, *, filter_by: dict[str, Any] | None = None) -> int:
        return int(await self.collection.count_documents(filter_by or {}))


    async def get_by(self, **fields: Any) -> TModel | None:
        doc = await self.collection.find_one(fields)
        return self._from_doc(doc) if doc else None

    async def list_by(
        self,
        *,
        filter_by: dict[str, Any],
        sort: Sequence[tuple[str, int]] | None = None,
        limit: int = 100,
        skip: int = 0,
        projection: dict[str, int] | None = None,
    ) -> list[TModel]:
        return await self.list_(
            filter_by=filter_by,
            sort=sort,
            limit=limit,
            skip=skip,
            projection=projection,
        )

    async def get_or_create(self, *, id_: str, defaults: dict[str, Any] | None = None) -> tuple[TModel, bool]:
        existing = await self.get(id=id_)
        if existing:
            return existing, False

        payload: dict[str, Any] = {"id": id_, **(defaults or {})}
        created = await self.create(payload)
        return created, True

    def with_collection(self, collection_name: str) -> Self:
        self._collection = self._db.get_collection(collection_name)
        return self

    async def create_or_update(
            self,
            *,
            search_by: dict[str, Any],
            update: dict[str, Any],
    ) -> tuple[TModel, bool]:
        now = utcnow()
        update_doc = dict(update)
        update_doc.pop("created", None)
        update_doc.pop("id", None)

        set_doc: dict[str, Any] = {**update_doc, "updated": now}

        set_on_insert: dict[str, Any] = {"created": now, "id": str(uuid.uuid4()), **search_by}

        doc = await self.collection.find_one_and_update(
            search_by,
            {"$set": set_doc, "$setOnInsert": set_on_insert},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        if not doc:
            fetched = await self.collection.find_one(search_by)
            if not fetched:
                raise RuntimeError("create_or_update failed to upsert document")
            doc = fetched

        created_flag = bool(doc.get("created") == doc.get("updated") == now)

        return self._from_doc(doc), created_flag