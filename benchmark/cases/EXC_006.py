from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import Dict

router = APIRouter(prefix="/api/v1", tags=["files"])

@router.post(
    "/upload",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    tags=["files"]
)
async def upload_file(
    file: UploadFile = File(..., description="Arquivo de imagem (max 5MB)")
) -> Dict[str, str]:
    '''
    Faz upload de um arquivo de imagem.
    
    Args:
        file: Arquivo enviado pelo cliente
        
    Returns:
        Metadados do arquivo salvo
        
    Raises:
        HTTPException: Se arquivo não for imagem ou muito grande
    '''
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas imagens são permitidas"
        )
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo muito grande (max 5MB)"
        )
        
    return {"filename": file.filename, "content_type": file.content_type}