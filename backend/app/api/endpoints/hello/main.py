from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def hello_world():
    return {"message": "Hello World"}

@router.get("/{name}")
def hello_name(name: str):
    return {"message": f"こんにちは {name}さん"}