# online-cinema-api


## Users for testing application

### Admin
```
Email: admin@example.com  
Password: Admin123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NjMwNDc3NTd9.9Y6Dat7be5mP1wcVPEpOqtpDcV9rd-LKwu1mM9-sWsc  
```

### Moderator
```
Email: moderator@example.com  
Password: Moderator123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJleHAiOjE3NjMwNDc4NTZ9.KnoHbEHCcGAEtogs4LMBg9ntp-mt4CwJLE7wRZ13Bwk  
```

### Simple User
```
Email: user@example.com  
Password: User123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJleHAiOjE3NjMwNDgwMTR9.HU7zcU3CeflnlDRFdKAn1DumvgXjqMNWXahozhlOV5s  
```


## Example of using role based dependencies
``` python
from security.permissions import require_admin, require_moderator, require_user


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