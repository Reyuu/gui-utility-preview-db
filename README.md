# Preview specific database in GUI

## Prerequisites

`python3.7+`

### Install prerequisites
`pip3 install requirements.txt`

### or install one by one
```
Jinja2
tqdm
wxPython
```

## Database format

Format is as follows (based on SQLite query)
```sql
CREATE TABLE comments
                (id text,
                subject text,
                description text,
                submitter text,
                submitter_email text,
                assignee text,
                assignee_email text,
                collaborators text,
                group_ text,
                comment_author_id text,
                comment_html_body text,
                comment_public integer,
                comment_created_at text)
```

Yes, I know this is wasetful.

## Usage
Use **create_dummy_database.py** to create a dummy database, which would be helpful for testing.

Use **gui_app.py** to launch the actual GUI app to preview database. Use searchbar to filter the results. By default, nothing is displayed, only after searching you'll have list of rows.