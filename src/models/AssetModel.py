from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums.DataBaseEnum import DataBaseEnum
from typing import List
from sqlalchemy.future import select
from sqlalchemy import func, delete

class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
    
    
    @classmethod
    async def create_instance(cls, db_client):
        isinstance = cls(db_client)
        return isinstance

         
    async def create_asset(self, asset: Asset) -> Asset:
        async with self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)
        
        return asset
    
    
    async def get_all_assets(self, asset_project_id: int, asset_type: str) -> List[Asset]:
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_type == asset_type
                )
                result = await session.execute(query)
                assets = result.scalars().all()
                
        return assets
    
    
    async def count_assets(self, asset_project_id: int, asset_type: str) -> int:
        async with self.db_client() as session:
            async with session.begin():
                query = select(func.count(Asset.asset_id)).where(
                    Asset.asset_project_id == asset_project_id,
                    Asset.asset_type == asset_type
                )
                total_assets = await session.execute(query)
                count = total_assets.scalar_one()
                
        return count
    
    async def get_asset_by_name(self, asset_name: str, asset_project_id: int) -> Asset:
        async with self.db_client() as session:
            async with session.begin():
                query = select(Asset).where(
                    Asset.asset_name == asset_name,
                    Asset.asset_project_id == asset_project_id
                )
                asset = await session.execute(query)
                
        return asset.scalar_one_or_none()
