# Letter Soup AI Generator

Letter Soup AI Generator is a Flask-based web application that creates customizable word search puzzles using OpenAI's GPT model. It generates puzzles based on user-defined subjects, grid sizes, and languages, making it a versatile tool for educators, puzzle enthusiasts, or anyone looking for a fun word-finding challenge.

## Features

- Generate word search puzzles on any subject
- Customize grid size (5x5 to 25x25)
- Support for multiple languages
- AI-powered word generation using OpenAI's GPT model
- Option to add custom words
- PDF export for easy printing
- Save and manage multiple puzzles

## Technologies Used

- Python
- Flask
- SQLAlchemy
- OpenAI API
- ReportLab (for PDF generation)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/SzczepanBEN/letter-soup-ai-generator.git
   cd letter-soup-ai-generator
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add the following:
   ```
   FLASK_SECRET_KEY=your_secret_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Initialize the database:
   ```
   python
   >>> from index import app, db
   >>> with app.app_context():
   ...     db.create_all()
   ```

6. Run the application:
   ```
   python index.py
   ```

7. Open a web browser and navigate to `http://localhost:5000` to use the application.

## Usage

1. Enter a subject for your word search puzzle.
2. Choose the grid size (5x5 to 25x25).
3. Optionally, add custom words separated by commas.
4. Select the language for the puzzle.
5. Click "Generate Puzzle" to create your word search.
6. You can download the puzzle as a PDF or save it for later.

## Contributing

Contributions to the Letter Soup AI Generator are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
