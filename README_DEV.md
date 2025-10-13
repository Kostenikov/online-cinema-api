# online-cinema-api


## Example of using role based dependencies
``` python
from config import require_admin, require_moderator, require_user


@router.get("/some_path/")
async def some_action(
    current_user: Annotated[UserModel, Depends(require_admin)],
):
    # Here is the logic of endpoint
    pass
    
@router.get("/some_path/")
async def some_action(
    current_user: Annotated[UserModel, Depends(require_moderator)],
):
    # Here is the logic of endpoint
    pass
    
@router.get("/some_path/")
async def some_action(
    current_user: Annotated[UserModel, Depends(require_user)],
):
    # Here is the logic of endpoint
    pass
    
```