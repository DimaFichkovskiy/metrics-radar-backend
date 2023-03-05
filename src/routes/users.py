from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, paginate

from src import schemas
from src.crud import UserCRUD
from src.routes.dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not Found"}}
)


@router.get("/", response_model=Page[schemas.User])
async def read_users(
        skip: int = 0,
        limit: int = 100,
        user_crud: UserCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
):
    users = await user_crud.get_users(skip=skip, limit=limit)
    return paginate(users)


@router.get("/{user_id}", response_model=schemas.User)
async def read_user(
        user_id: int,
        user_crud: UserCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
):
    user = await user_crud.get_user(user_id=user_id)
    return user


@router.patch("/update_user_info", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def update_user_info(
        update_data: schemas.UserInfoUpdate,
        user_crud: UserCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.User:
    if (update_data.first_name and update_data.last_name) is None:
        raise HTTPException(status_code=400, detail="There is not enough data to update")

    return await user_crud.update_user_info(user_id=current_user.id, update_data=update_data)


@router.patch(
    "/update_user_password", response_model=schemas.UpdatePasswordResponse, status_code=status.HTTP_201_CREATED
)
async def update_user_password(
        update_data: schemas.UserPasswordUpdate,
        user_crud: UserCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.UpdatePasswordResponse:
    if update_data.password is None:
        raise HTTPException(status_code=400, detail="The password field must not be empty")

    user = await user_crud.update_user_password(user_id=current_user.id, update_data=update_data)
    if not user:
        raise HTTPException(status_code=400, detail="The new password matches the old one")

    return schemas.UpdatePasswordResponse(
        status_code=status.HTTP_201_CREATED,
        body="Password successfully updated"
    )


@router.delete("/delete_me", response_model=schemas.DeleteUserResponse, status_code=200)
async def delete_user(
        user_crud: UserCRUD = Depends(),
        current_user: schemas.User = Depends(get_current_user)
) -> schemas.DeleteUserResponse:
    await user_crud.delete_user(user_id=current_user.id)

    return schemas.DeleteUserResponse(
        status_code=status.HTTP_200_OK,
        body="Success delete user"
    )
