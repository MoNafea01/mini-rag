from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums.DataBaseEnum import DataBaseEnum

class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        await isinstance.init_collection()
        return isinstance
    
    async def init_collection(self):
        collection_name = DataBaseEnum.COLLECTION_ASSET_NAME.value
        all_collections = await self.db_client.list_collection_names()
        self.collection = self.db_client[collection_name]
        
        if collection_name not in all_collections:
            print(f"⏳ Initializing collection: '{collection_name}'")
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(**index)
            
    async def create_asset(self, asset: Asset) -> Asset:
        result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_unset=True))
        asset.id = result.inserted_id
        return asset
    
    async def get_all_assets(self, asset_project_id: str):
        return await self.collection.find({
            "asset_project_id": asset_project_id
            }).to_list(length=None)
