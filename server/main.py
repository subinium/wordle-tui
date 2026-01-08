from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import get_settings
from server.auth.router import router as auth_router
from server.words.router import router as words_router
from server.games.router import router as games_router
from server.leaderboard.router import router as leaderboard_router
from server.streaks.router import router as streaks_router
from server.stats.router import router as stats_router
from server.admin.router import router as admin_router

settings = get_settings()

app = FastAPI(
    title="Wordle TUI API",
    description="Backend API for Wordle TUI game",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(words_router)
app.include_router(games_router)
app.include_router(leaderboard_router)
app.include_router(streaks_router)
app.include_router(stats_router)
app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


def run():
    import uvicorn
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
