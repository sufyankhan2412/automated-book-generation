import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

def handler(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            notes = data.get('notes', '')

            # Here, you would integrate with your book generation workflow
            # For now, return a placeholder response
            response = {
                'status': 'success',
                'message': f'Book generation started for "{title}" with notes: {notes}',
                'book_id': 'placeholder_id'
            }
            return {
                'statusCode': 200,
                'body': json.dumps(response)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }