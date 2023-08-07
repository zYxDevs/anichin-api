from typing import Text

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api import Main

app = FastAPI()
main = Main()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root(req: Request):
    """
    Get home page
    params: page (optional) - int
    return: JSON

    """
    page = req.query_params.get("page")
    try:
        if page and not page.isdigit():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid page"},
            )
        return main.get_home(int(page) if page else 1)
    except Exception as err:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(err)},
        )


@app.get("/search")
def search(req: Request):
    """
    Search donghua by query
    params: q - string (required)
    return: JSON
    """
    if query := req.query_params.get("q"):
        return main.search(query)
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Missing query"},
        )


# slug from url
@app.get("/info/{slug}")
def get_info(slug: Text):
    """
    Show detail of donghua
    params: slug name of donghua - string (required)
    return: JSON

    """
    try:
        slug = slug
        return main.get_info(slug)
    except Exception as err:
        print(err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )


@app.get("/genres")
def list_genres():
    """
    Show list of genres
    return: JSON

    """
    try:
        return main.genres()
    except Exception as err:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )


@app.get("/genre/{slug}")
def get_genres(req: Request, slug: Text):
    """
    Show list of donghua by genre
    params: slug genre - string (required)
    params: page (optional) - int
    return: JSON

    """
    try:
        page = req.query_params.get("page")
        if page and not page.isdigit():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid page"},
            )

        return main.genres(slug, int(page) if page else 1)
    except Exception as err:
        print(err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )


@app.get("/episode/{slug}")
def get_episode(slug: Text):
    """
    Get detail of episode
    params: slug episode - string (required)
    return: JSON

    """
    try:
        if data := main.get_episode(slug):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=data,
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found"},
        )
    except Exception as err:
        print(err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error"},
        )


# get episode from url
@app.get("/video-source/{slug}")
def get_video(slug: Text):
    """
    Show list of video source
    params: slug - string (required)
    return: JSON

    """
    try:
        if data := main.get_video_source(slug):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=data,
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found"},
        )
    except Exception as err:
        print(err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )


@app.get("/anime")
def anime(req: Request):
    """
    Show list of anime
    return: JSON

    """
    try:
        req = req.query_params
        todict = dict(req)
        return main.anime(params=todict)
    except Exception as err:
        print(err)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal Server Error"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
