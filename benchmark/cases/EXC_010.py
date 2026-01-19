from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/api/v1", tags=["export"])

@router.get(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    tags=["export"]
)
async def export_data_csv() -> StreamingResponse:
    '''
    Exporta dados em formato CSV via stream.
    '''
    stream = io.StringIO()
    stream.write("id,name,value\n")
    stream.write("1,Test,100\n")
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )