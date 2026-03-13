from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="website/static"), name="static")

templates = Jinja2Templates(directory="website/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/new-question", response_class=HTMLResponse)
async def new_question(request: Request):
    return templates.TemplateResponse("new_question.html", {"request": request})

@app.post("/new-question")
async def submit_question(request: Request, question: str = Form(...), email: str = Form(None), name: str = Form(None), tags: str = Form(None)):
    # Load existing questions
    file_path = "website/questions.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            questions = json.load(f)
    else:
        questions = []
    
    # Create new question entry
    new_question = {"question": question}
    if email:
        new_question["email"] = email
    if name:
        new_question["name"] = name
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if tag_list:
            new_question["tags"] = tag_list
    
    # Append and save
    questions.append(new_question)
    with open(file_path, "w") as f:
        json.dump(questions, f, indent=4)
    
    return templates.TemplateResponse("new_question.html", {"request": request, "message": "Question submitted successfully!"})

@app.get("/arqiv", response_class=HTMLResponse)
async def arqiv(request: Request):
    file_path = "website/questions.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            questions = json.load(f)
    else:
        questions = []
    
    # Load myths
    myths_path = "website/myths.json"
    if os.path.exists(myths_path):
        with open(myths_path, "r") as f:
            myths = json.load(f)
        # Mark myths
        for myth in myths:
            myth["is_myth"] = True
        questions.extend(myths)
    
    # Collect unique tags
    tags = set()
    for q in questions:
        if "tags" in q:
            tags.update(q["tags"])
    tags = sorted(list(tags))
    
    selected_tag = request.query_params.get('tag')
    if selected_tag:
        questions = [q for q in questions if selected_tag in q.get('tags', [])]
    
    return templates.TemplateResponse("arqiv.html", {"request": request, "questions": questions, "tags": tags, "selected_tag": selected_tag})

@app.get("/myths", response_class=HTMLResponse)
async def myths(request: Request):
    file_path = "website/myths.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            myths = json.load(f)
    else:
        myths = []
    return templates.TemplateResponse("myths.html", {"request": request, "myths": myths})

@app.get("/schedule", response_class=HTMLResponse)
async def schedule(request: Request):
    file_path = "website/events.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            events = json.load(f)
    else:
        events = []
    
    # Current date
    today = datetime.date.today()
    
    upcoming_events = []
    previous_events = []
    
    for event in events:
        start_date = datetime.datetime.strptime(event["start_date"], "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(event.get("end_date", event["start_date"]), "%Y-%m-%d").date()
        if start_date >= today:
            upcoming_events.append(event)
        elif end_date < today:
            previous_events.append(event)
        # Ongoing events (start_date < today <= end_date) are not included in upcoming or previous
    
    # Sort upcoming by start_date ascending, previous by end_date descending
    upcoming_events.sort(key=lambda x: x["start_date"])
    previous_events.sort(key=lambda x: x.get("end_date", x["start_date"]), reverse=True)
    
    return templates.TemplateResponse("schedule.html", {"request": request, "upcoming_events": upcoming_events, "previous_events": previous_events})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})

@app.post("/account")
async def login(request: Request, password: str = Form(...)):
    if password == "admin":
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return templates.TemplateResponse("account.html", {"request": request, "error": "Invalid password"})

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    file_path = "website/questions.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            questions = json.load(f)
    else:
        questions = []
    return templates.TemplateResponse("admin.html", {"request": request, "questions": questions})

@app.post("/admin/add-answer")
async def admin_add_answer(request: Request, question_index: int = Form(...), answer: str = Form(...)):
    file_path = "website/questions.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            questions = json.load(f)
    else:
        questions = []
    
    if 0 <= question_index < len(questions):
        questions[question_index]["answer"] = answer
        with open(file_path, "w") as f:
            json.dump(questions, f, indent=4)
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/delete-all")
async def admin_delete_all(request: Request):
    file_path = "website/questions.json"
    with open(file_path, "w") as f:
        json.dump([], f, indent=4)
    return RedirectResponse(url="/admin", status_code=303)