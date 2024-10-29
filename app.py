import os
from datetime import datetime
from os.path import dirname, join

import requests
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")
API_KEY = os.environ.get("API_KEY")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)


# endpoint homepage
@app.route("/")
def main():
    # mengambil data didalam database
    word_documents = db.words.find({}, {"_id": False})

    # menyimpan hasil iterasi
    word_list = []

    # proses iterasi
    for word_doc in word_documents:
        # mengambil baris awal shortdef di field definitions
        definition = word_doc["definitions"][0]["shortdef"]

        """
        - definition akan dirender jika tipe datanya adalah string 
        - jika tipe datanya array, maka render baris awal dari definition
        """
        definition = definition if type(definition) is str else definition[0]

        # menambahkan objek word dan definition ke dalam words
        word_list.append({"word": word_doc["word"], "definition": definition})

    msg = request.args.get("msg")

    # meminta suggestions dalam format list
    suggestions = request.args.getlist("suggestions")

    # merender words untuk ditampilkan di template
    return render_template(
        "index.html", words=word_list, msg=msg, suggestions=suggestions
    )


# endpoint detail page yang menerima parameter
@app.route("/detail/<keyword>")
def detail(keyword):
    api_url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={API_KEY}"

    response = requests.get(api_url)
    definition_data = response.json()

    """
    - jika definition_data kosong
    - diarahkan ke main ('/') dengan membawa msg
    """
    if not definition_data:
        return redirect(url_for("main", msg=f'The word "{keyword}" could not be found'))

    """
    - jika elemen pertama definitions adalah string
    - diarahkan ke main dengan membawa suggestions
    - suggestions berisikan kata alternatif dari definitions
    """
    if type(definition_data[0]) is str:
        return redirect(
            url_for(
                "main",
                msg=f'The word "{keyword}" could not be found',
                suggestions=definition_data,
            )
        )

    # default key status_give adalah new
    status = request.args.get("status_give", "new")

    """
    - variabel word digunakan dalam html untuk merender keyword
    - variabel definitions berisi data definisi keyword
    - variabel status untuk menampilkan button berdasarkan kondisi
    """
    return render_template(
        "detail.html", word=keyword, definitions=definition_data, status=status
    )


# endpoint untuk menyimpan data ke database
@app.route("/api/save_word", methods=["POST"])
def save_word():
    # mengambil data yang dikirim dalam format JSON
    json_data = request.get_json()
    word = json_data.get("word_give")
    definitions = json_data.get("definitions_give")

    date_saved = datetime.now().strftime("%Y-%m-%d")

    word_document = {"word": word, "definitions": definitions, "date": date_saved}

    # menyimpan data word_document ke database
    db.words.insert_one(word_document)

    return jsonify(
        {"result": "success", "msg": f"The word '{word}' was saved successfully!"}
    )


# endpoint untuk menghapus data pada database
@app.route("/api/delete_word", methods=["POST"])
def delete_word():
    word = request.form.get("word_give")
    db.words.delete_one({"word": word})
    db.examples.delete_many({"word": word})

    return jsonify(
        {"result": "success", "msg": f"The word '{word}' was deleted successfully!"}
    )


# endpoint untuk menampilkan data sentence pada database
@app.route("/api/get_exs", methods=["GET"])
def get_exs():
    word = request.args.get("word_give")
    # diganti
    example_documents = db.examples.find({"word": word})

    examples = []
    for example_doc in example_documents:
        examples.append(
            {"example": example_doc.get("example"), "id": str(example_doc.get("_id"))}
        )
    return jsonify({"result": "success", "examples": examples})


# endpoint untuk menyimpan sentence ke database
@app.route("/api/save_ex", methods=["POST"])
def save_ex():
    word = request.form.get("word_give")
    example_sentence = request.form.get("example_give")

    example_document = {
        "word": word,
        "example": example_sentence,
    }
    db.examples.insert_one(example_document)

    return jsonify(
        {
            "result": "success",
            "msg": f"Your example sentence for word '{word}', was saved!",
        }
    )


# endpoint untuk menghapus sentence dari database
@app.route("/api/delete_ex", methods=["POST"])
def delete_ex():
    example_id = request.form.get("id_give")
    word = request.form.get("word_give")

    db.examples.delete_one({"_id": ObjectId(example_id)})

    return jsonify(
        {
            "result": "success",
            "msg": f"Your example sentence for word '{word}', was deleted!",
        }
    )


# jalankan web
if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
