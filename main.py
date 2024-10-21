from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "sqlite:///./files.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FileModel(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)


Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow your React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = f"files/{file.filename}"
    with open(file_location, "wb") as file_object:
        file_object.write(await file.read())
    db = SessionLocal()
    db_file = FileModel(filename=file.filename)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    db.close()
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}


@app.get("/files/")
async def read_files():
    db = SessionLocal()
    files = db.query(FileModel).all()
    db.close()
    return files


@app.delete("/files/{file_id}")
async def delete_file(file_id: int):
    db = SessionLocal()
    file_to_delete = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file_to_delete:
        db.close()
        raise HTTPException(status_code=404, detail="File not found")
    db.delete(file_to_delete)
    db.commit()
    db.close()
    os.remove(f"files/{file_to_delete.filename}")
    return {"detail": "File deleted"}


app.mount("/files", StaticFiles(directory="files"), name="files")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <body>
            <h1>File Upload</h1>
            <form action="/upload/" enctype="multipart/form-data" method="post">
                <input name="file" type="file"/>
                <input type="submit"/>
            </form>
        </body>
    </html>
    """


@app.get('/health')
async def health_check():
    return {'status': 'ok'}
