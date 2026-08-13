# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates

# app = FastAPI(title="Synthetic Member Servicing Console")
# templates = Jinja2Templates(directory="demo_app/templates")

# MEMBERS = {
#     "12345": {"name": "Jane Smith", "savings": "$4,821.52", "checking": "$1,220.15"},
#     "67890": {"name": "Alex Johnson", "savings": "$8,104.73", "checking": "$925.40"},
# }

# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="home.html",
#         context={}
#     )

# @app.get("/member/{member_id}", response_class=HTMLResponse)
# def member(request: Request, member_id: str):
#     if member_id == "50000":
#         return templates.TemplateResponse("member.html", {
#             "request": request,
#             "error": "Application Error",
#             "message": "Temporary core service failure."
#         }, status_code=200)

#     member_data = MEMBERS.get(member_id)
#     if not member_data:
#         return templates.TemplateResponse("member.html", {
#             "request": request,
#             "not_found": True,
#             "member_id": member_id
#         })

#     return templates.TemplateResponse("member.html", {
#         "request": request,
#         "member": member_data,
#         "member_id": member_id
#     })

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Synthetic Member Servicing Console")
templates = Jinja2Templates(directory="demo_app/templates")

MEMBERS = {
    "12345": {
        "name": "Jane Smith",
        "savings": "$4,821.52",
        "checking": "$1,220.15",
    },
    "67890": {
        "name": "Alex Johnson",
        "savings": "$8,104.73",
        "checking": "$925.40",
    },
}


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )


@app.get("/member/{member_id}", response_class=HTMLResponse)
def member(request: Request, member_id: str):
    # Synthetic application failure used to demonstrate
    # checkpoint failure / escalation behavior.
    if member_id == "50000":
        return templates.TemplateResponse(
            request=request,
            name="member.html",
            context={
                "error": "Application Error",
                "message": "Temporary core service failure.",
            },
            status_code=200,
        )

    member_data = MEMBERS.get(member_id)

    # Expected business outcome: member does not exist.
    if not member_data:
        return templates.TemplateResponse(
            request=request,
            name="member.html",
            context={
                "not_found": True,
                "member_id": member_id,
            },
        )

    # Successful member lookup.
    return templates.TemplateResponse(
        request=request,
        name="member.html",
        context={
            "member": member_data,
            "member_id": member_id,
        },
    )