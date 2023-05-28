from starlette.responses import JSONResponse

from model import Model
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/solve/{model_string}")
async def solve(model_string: str):
    model = Model.from_string(model_string.replace('%2F', '/'))

    model.solve()
    print(model.json)
    return JSONResponse(model.json)
