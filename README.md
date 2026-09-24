# Resume Match Analyzer

Resume Match Analyzer is a web application that compares a candidate's resume with a job description and generates an overall compatibility score along with category-wise analysis.

## Features

- User registration and login
- Resume upload in PDF and DOCX formats
- Job description input
- Resume and job description semantic matching
- Overall resume match score
- Technical Skills analysis
- Soft Skills analysis
- Tools & Technologies analysis
- Analysis history
- Clean and responsive web interface
- SQLite-based user and analysis history management

## How It Works

The application follows these steps:

1. The user creates an account and signs in.
2. The user enters a job description.
3. The user uploads a resume in PDF or DOCX format.
4. Text is extracted from the uploaded resume.
5. The application processes the job description and resume text.
6. Sentence embeddings are generated using a pre-trained Sentence Transformer model.
7. Cosine similarity is used to calculate semantic similarity.
8. Keyword overlap is incorporated into the overall matching calculation.
9. The application calculates category-wise alignment for:
   - Technical Skills
   - Soft Skills
   - Tools & Technologies
10. The overall score and category results are displayed.
11. The analysis is stored in the user's history.

## Matching Approach

The overall score combines semantic similarity and keyword overlap.

### Semantic Similarity

The application uses:

`paraphrase-MiniLM-L6-v2`

from the Sentence Transformers library to generate embeddings for the job description and resume.

Cosine similarity is then calculated between the two embeddings.

### Keyword Processing

The application uses spaCy to process text and extract relevant terms after removing stop words and punctuation.

Keyword overlap is incorporated along with semantic similarity to produce the final match score.

### Category Analysis

The result page separately analyzes three areas:

- **Technical Skills** — programming languages, frameworks, databases and technical concepts.
- **Soft Skills** — communication, teamwork, leadership, collaboration and related professional skills.
- **Tools & Technologies** — development tools, cloud platforms, productivity tools and related technologies.

## Technologies Used

### Backend

- Python
- Flask
- Flask-WTF
- SQLite

### Natural Language Processing

- Sentence Transformers
- spaCy
- PyMuPDF
- python-docx

### Frontend

- HTML
- CSS
- Jinja2

### Model

- `paraphrase-MiniLM-L6-v2`

## Project Structure

```text
Resume-Match-Analyzer/
│
├── main.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── logo.png
│
├── templates/
│   ├── Login_Page.html
│   ├── SignUp_Page.html
│   ├── index.html
│   ├── result.html
│   └── history.html
│
└── uploads/