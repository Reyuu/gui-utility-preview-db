import sqlite3
import random
import uuid
import time
import datetime
from tqdm import tqdm

## utilities
def random_date():
    d = random.randint(1, int(time.time()))
    return datetime.datetime.fromtimestamp(d).strftime('%Y-%m-%d')

def _generate_words(length):
    generated_words = []
    with open("words-no-swears.txt", "r") as f:
        words = f.read().split("\n")
        for i in range(length):
            generated_words += [random.choice(words)]
    return generated_words

def create_sentence(length):
    sentence = _generate_words(length)
    sentence = " ".join(sentence)
    sentence = f"{sentence}.".capitalize()
    return sentence
        
def create_passage(length):
    passage = []
    for i in range(length):
        passage += [create_sentence(random.randint(5, 10))]
    return " ".join(passage)

def create_name():
    name = _generate_words(2)
    return " ".join(name).upper()

## test utilities
#print(_generate_words(2), create_sentence(5), create_passage(5), create_name())

## connection

conn = sqlite3.connect("dummy.db")
cur = conn.cursor()

## create table
cur.execute("drop table comments")
cur.execute("""CREATE TABLE comments
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
                comment_created_at text)""")

## add dummy data
for i in tqdm(range(5000)):
    id = str(uuid.uuid4())
    subject = create_sentence(random.randint(5, 10))
    description = create_passage(5)
    submitter = create_name()
    submitter_email = f"{submitter}@testing-company.com"
    assignee = create_name()
    assignee_email = f"{assignee}@testing-company.com"
    collaborators = ""
    group = create_name()
    for j in range(random.randint(5, 10)):
        comment_author_id = str(uuid.uuid4())
        comment_html_body = create_passage(random.randint(10, 20))
        comment_public = random.randint(0, 1)
        comment_created_at = str(random_date())

        values = (id, subject, description, submitter, submitter_email, assignee,
                  assignee_email, collaborators, group, comment_author_id,
                  comment_html_body, comment_public, comment_created_at)
        cur.execute("insert into comments values (?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    conn.commit()
conn.close()

