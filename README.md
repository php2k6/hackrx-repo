# hackrx-fastapi-app/hackrx-fastapi-app/README.md

# HackRx FastAPI App

This project is a FastAPI application designed for processing insurance documents. It utilizes various services to extract text from PDFs, convert it to Markdown, and query the content using the BM25 algorithm.

## Project Structure

```
hackrx-fastapi-app
├── app
│   ├── __init__.py
│   ├── main.py                # Entry point for the FastAPI application
│   ├── api                    # Contains API routes
│   │   ├── __init__.py
│   │   └── routes
│   │       ├── __init__.py
│   │       └── document.py    # FastAPI routes for document processing
│   ├── core                   # Core configuration and settings
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models                 # Pydantic models for request/response validation
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── services               # Contains business logic for document processing
│       ├── __init__.py
│       ├── bm25_service.py
│       ├── chunking_service.py
│       ├── extract_service.py
│       ├── llm_service.py
│       └── markdown_service.py
├── docs                       # Documentation files
│   ├── document.md
│   ├── layout_clean.json
│   └── output.md
├── sample                     # Sample PDF documents for testing
│   ├── BAJHLIP23020V012223.pdf
│   ├── CHOTGDP23004V012223.pdf
│   ├── demo.py
│   ├── EDLHLGA23009V012223.pdf
│   ├── HDFHLIP23024V072223.pdf
│   └── ICIHLIP22012V012223.pdf
├── tests                      # Unit tests for the application
│   ├── __init__.py
│   └── test_api.py
├── .gitignore                 # Git ignore file
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd hackrx-fastapi-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the FastAPI application, execute the following command:

```
uvicorn app.main:app --reload
```

You can access the API documentation at `http://127.0.0.1:8000/docs`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.