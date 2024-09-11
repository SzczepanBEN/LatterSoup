import random
import string
import openai
from textwrap import wrap
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from io import BytesIO
from dotenv import load_dotenv
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pdfkit
from flask import make_response
import os

load_dotenv()

app = Flask(__name__)

# Database configuration
if os.getenv('POSTGRES_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DATABASE')}"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///letter_soup.db')

# Secret key configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Disable SQLAlchemy track modifications (optional, for performance)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

class Grid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    words = db.Column(db.String(1000), nullable=False)
    grid = db.Column(db.String(10000), nullable=False)
    language = db.Column(db.String(50), nullable=False)

def recreate_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database recreated successfully.")

def estimate_word_count(grid_size):
    return max(5, min(25, grid_size * grid_size // 10))

def get_words_from_openai(subject, custom_words, language, num_words=10):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates words related to a given subject in a specified language."},
                {"role": "user", "content": f"Generate {num_words} words related to '{subject}' in {language}. Provide only the words, separated by commas - Like this: wordone,wordtwo,wordthree,wordfour... Never use the word 'placeholder', always use real words. Use the appropriate alphabet for the language. Never use any special characters or numbers other than the alphabet and commas."}
            ]
        )
        
        print("OpenAI API Response:", response)
        
        generated_words = response.choices[0].message['content'].split(',')
        generated_words = [word.strip().lower() for word in generated_words]
        
        all_words = list(set(generated_words + custom_words))
        
        if len(all_words) < num_words:
            return all_words + ["placeholder"] * (num_words - len(all_words))
        return all_words[:num_words]
    
    except Exception as e:
        print(f"Error in getting words from OpenAI: {e}")
        return custom_words + ["placeholder"] * (num_words - len(custom_words))

def create_grid(size, words, language):
    grid = [[' ' for _ in range(size)] for _ in range(size)]
    directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
    placed_words = []

    for word in words:
        word = word.upper()
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            direction = random.choice(directions)
            start_row = random.randint(0, size - 1)
            start_col = random.randint(0, size - 1)
            
            end_row = start_row + direction[0] * (len(word) - 1)
            end_col = start_col + direction[1] * (len(word) - 1)
            
            if 0 <= end_row < size and 0 <= end_col < size:
                if all(grid[start_row + direction[0]*i][start_col + direction[1]*i] in (' ', word[i])
                       for i in range(len(word))):
                    for i, letter in enumerate(word):
                        grid[start_row + direction[0]*i][start_col + direction[1]*i] = letter
                    placed = True
                    placed_words.append(word)
            attempts += 1

    # Fill empty spaces with random letters appropriate for the language
    alphabet = get_alphabet(language)
    for i in range(size):
        for j in range(size):
            if grid[i][j] == ' ':
                grid[i][j] = random.choice(alphabet)

    return grid, placed_words

def get_alphabet(language):
    # Define alphabets for different languages
    alphabets = {
        "English": string.ascii_uppercase,
        "Spanish": string.ascii_uppercase + "ÑÁÉÍÓÚÜ",
        "French": string.ascii_uppercase + "ÀÂÆÇÉÈÊËÎÏÔŒÙÛÜ",
        "German": string.ascii_uppercase + "ÄÖÜß",
        "Polish": string.ascii_uppercase + "ĄĆĘŁŃÓŚŹŻ",
        "Italian": string.ascii_uppercase + "ÀÈÉÌÍÎÒÓÙÚ",
        "Portuguese": string.ascii_uppercase + "ÁÂÃÀÇÉÊÍÓÔÕÚ",
        "Dutch": string.ascii_uppercase + "ÁÉÍÓÚÝ",
        "Swedish": string.ascii_uppercase + "ÅÄÖÉ",
        "Norwegian": string.ascii_uppercase + "ÆØÅ",
        "Danish": string.ascii_uppercase + "ÆØÅ",
        "Finnish": string.ascii_uppercase + "ÄÅÖŠ",
        "Greek": "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
        "Russian": "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
        # Add more languages as needed
    }
    return alphabets.get(language, string.ascii_uppercase)

@app.route('/', methods=['GET', 'POST'])
def generate_grid():
    if request.method == 'POST':
        subject = request.form['subject'].strip()
        size = request.form['size']
        custom_words = request.form.get('custom_words', '').strip().split(',')
        language = request.form['language']
        
        if not subject:
            flash('Subject is required.', 'error')
            return redirect(url_for('generate_grid'))
        
        try:
            size = int(size)
            if size < 5 or size > 25:
                raise ValueError
        except ValueError:
            flash('Grid size must be a number between 5 and 25.', 'error')
            return redirect(url_for('generate_grid'))
        
        custom_words = [word.strip().lower() for word in custom_words if word.strip()]
        
        try:
            num_words = estimate_word_count(size)
            words = get_words_from_openai(subject, custom_words, language, num_words)
            grid, placed_words = create_grid(size, words, language)
            
            new_grid = Grid(subject=subject, size=size, words=','.join(placed_words), grid=str(grid), language=language)
            db.session.add(new_grid)
            db.session.commit()
            
            return render_template('grid.html', grid=grid, words=placed_words, grid_id=new_grid.id, language=language)
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('generate_grid'))
    
    return render_template('generator.html')

font_path = os.path.join(os.path.dirname(__file__), 'NotoSans-Regular.ttf')
bold_font_path = os.path.join(os.path.dirname(__file__), 'NotoSans-Bold.ttf')
pdfmetrics.registerFont(TTFont('NotoSans', font_path))
pdfmetrics.registerFont(TTFont('NotoSans-Bold', bold_font_path))

@app.route('/print/<int:grid_id>')
def print_grid(grid_id):
    grid = Grid.query.get_or_404(grid_id)
    grid_data = eval(grid.grid)
    words = grid.words.split(',')

    # Calculate the cell size (similar to your original calculation)
    max_grid_size = 25
    cell_size = min(800 / max_grid_size, 1000 / max_grid_size)  # Approximate A4 size in pixels

    # Render the HTML template
    html_content = render_template('pdf_template.html', 
                                   grid=grid_data,
                                   words=words,
                                   subject=grid.subject,
                                   language=grid.language,
                                   cell_size=cell_size,
                                   grid_size=grid.size)

    # Configure pdfkit options
    options = {
        'page-size': 'A4',
        'margin-top': '20mm',
        'margin-right': '20mm',
        'margin-bottom': '20mm',
        'margin-left': '20mm',
        'encoding': "UTF-8",
    }

    # Generate PDF
    pdf = pdfkit.from_string(html_content, False, options=options)

    # Create response
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    filename = f"letter_soup_{grid.subject.replace(' ', '_')}_{grid.size}x{grid.size}_{grid.language}.pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return response

@app.route('/grids')
def list_grids():
    grids = Grid.query.all()
    return render_template('grid_list.html', grids=grids)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))