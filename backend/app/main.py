from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, organizations, members, departments, invitations, chat, finance, absences, admin, search, boards, notifications, logs

app = FastAPI(title="OCS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(members.router)
app.include_router(departments.router)
app.include_router(invitations.router)
app.include_router(invitations.user_invites_router)
app.include_router(chat.router)
app.include_router(finance.router)
app.include_router(absences.router)
app.include_router(admin.router)
app.include_router(search.router)
app.include_router(boards.router)
app.include_router(notifications.router)
app.include_router(logs.router)
app.include_router(logs.admin_org_logs_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}