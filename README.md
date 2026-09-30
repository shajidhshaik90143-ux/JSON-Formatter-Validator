# JSON Formatter & Validator

A strong, beginner-friendly JSON utility built with Python and Streamlit.

## Features

- Beautify / pretty-print JSON
- Minify JSON
- JSON validation with line and column errors
- JSON statistics: objects, arrays, strings, numbers, booleans, nulls, depth
- JSON tree explorer
- Flatten nested JSON into path/value rows
- JSONPath-style queries:
  - `$.user.name`
  - `$.users[0].name`
  - `$['user-name']`
  - `$`
- JSON document comparison / diff
- CSV export
- Pretty JSON download
- JSON file upload
- Configurable indentation
- Optional key sorting
- Unicode handling
- Responsive Streamlit interface

## Requirements

- Python 3.10+
- Streamlit
- Pandas

## Windows setup

Open Command Prompt in this folder:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If `python` is not recognized, try:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py -m streamlit run app.py
```

## Project structure

```text
JSON_Formatter_Validator/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── sample.json
└── src/
    ├── __init__.py
    └── json_tools.py
```

## Example JSON

```json
{
  "users": [
    {
      "id": 1,
      "name": "Alex",
      "active": true
    },
    {
      "id": 2,
      "name": "Sam",
      "active": false
    }
  ]
}
```

Query examples:

```text
$.users[0].name
$.users[1].active
```

## Troubleshooting

### Streamlit command not found

Use:

```bat
python -m streamlit run app.py
```

### ModuleNotFoundError

Activate the virtual environment and reinstall:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Port already in use

Run:

```bat
python -m streamlit run app.py --server.port 8502
```
