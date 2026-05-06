from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / '.env')

app = FastAPI()


@app.get('/')
def root():
    return {'status': 'Book Generation API is running'}


class GeneratePayload(BaseModel):
    title: str = ''
    notes: str = ''


@app.post('/api/generate')
def generate(payload: GeneratePayload):
    return {
        'status': 'success',
        'message': f'Book generation started for "{payload.title}" with notes: {payload.notes}',
        'book_id': 'placeholder_id'
    }
