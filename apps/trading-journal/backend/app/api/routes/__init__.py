"""
API routes package.

Authentication:
- Health routes are public (no auth required)
- All other routes should use RequireAuth dependency:

  Option 1: Per-endpoint dependency
  from app.api.dependencies import RequireAuth, DatabaseSession
  @router.get("/endpoint")
  async def endpoint(db: DatabaseSession, auth: RequireAuth):
      ...

  Option 2: Router-level dependency (recommended for protected routes)
  from app.api.dependencies import verify_api_key
  from fastapi import Depends, APIRouter
  router = APIRouter(dependencies=[Depends(verify_api_key)])
  
  Then all endpoints in this router will require authentication.
"""

