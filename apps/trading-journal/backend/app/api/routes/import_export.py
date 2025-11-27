"""
Import/Export API endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.api.dependencies import verify_api_key, DatabaseSession
from app.services.import_export_service import export_trades_to_csv, import_trades_from_csv

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.get("/export", response_class=StreamingResponse)
async def export_trades(
    db: DatabaseSession,
):
    """
    Export all trades to CSV.
    """
    csv_content = await export_trades_to_csv(db)
    
    response = StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
    )
    response.headers["Content-Disposition"] = "attachment; filename=trades_export.csv"
    return response

@router.post("/import")
async def import_trades(
    db: DatabaseSession,
    file: UploadFile = File(...),
):
    """
    Import trades from CSV file.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
        
    content = await file.read()
    result = await import_trades_from_csv(db, content)
    
    return result

