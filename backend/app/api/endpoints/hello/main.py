from fastapi import APIRouter

router = APIRouter()

@router.get("/", response_model=dict)
def get_hello_world():
    return {"message": "Hello World"}

@router.get("/{name}", response_model=dict)
def get_hello_name(name: str):
    return {"message": f"こんにちは {name}さん"}