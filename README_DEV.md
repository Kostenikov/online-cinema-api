# online-cinema-api


## Users for testing application

### Admin
```
Email: admin@example.com  
Password: Admin123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VyX2dyb3VwIjoiYWRtaW4iLCJleHAiOjE3NjMwNzI4NjN9.oBevqAXUJMatdzwa3s2CiUCyzj89CLCjjoEup0JWg-E  
```

### Moderator
```
Email: moderator@example.com  
Password: Moderator123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VyX2dyb3VwIjoibW9kZXJhdG9yIiwiZXhwIjoxNzYzMDczMDQwfQ.-z6G9StUqLwXdE298ukOdf9oYgTeBsxG09apDDPAl1A  
```

### Simple User
```
Email: user@example.com  
Password: User123!  
Access Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX2dyb3VwIjoidXNlciIsImV4cCI6MTc2MzA3MzE0N30.tWyQJ-XI_VCIU4WcWxPJeo23dcazVpBHvxyy51dNUp8  
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