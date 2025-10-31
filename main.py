from tkinter.font import names

from dotenv import load_dotenv
import os

from flask import render_template, request, redirect, url_for, Flask
import json
import random

load_dotenv()

CATEGORIES_KEY = "CATEGORIES"
TITLE_KEY = "TITLE"
MERCH_FOLDER_KEY = "MERCH_FOLDER"
IMAGE_FOLDER_KEY = "IMAGE_FOLDER"
DEFAULT_CATEGORIES = "Cards, T-shirt, trousers"
DEFAULT_TITLE = "CardSharp 100% official merch store"
DEFAULT_MERCH_FOLDER = "merch"
DEFAULT_IMAGE_FOLDER = "static/images"


IMAGE_FOLDER = os.environ.get(IMAGE_FOLDER_KEY, DEFAULT_IMAGE_FOLDER)
MERCH_FOLDER = os.getenv(MERCH_FOLDER_KEY, DEFAULT_MERCH_FOLDER)
CATEGORIES = os.getenv(CATEGORIES_KEY, DEFAULT_CATEGORIES).split(",")
CATEGORIES = [cat.strip() for cat in CATEGORIES]
TITLE = os.getenv(TITLE_KEY, DEFAULT_TITLE)
DEBUG = os.getenv("DEBUG", "false").lower() in ["1", "true", "y", "yes"]

app = Flask(__name__)

app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

for cat in CATEGORIES:
    os.makedirs(os.path.join(MERCH_FOLDER, cat), exist_ok=True)
os.makedirs(os.path.join(IMAGE_FOLDER), exist_ok=True)

# Joke dataclass
class Merch:
    def __init__(self, category:str, name:str, description:str, price:int, image:str, rating:list[int]=[], id=None):
        self.category = category
        self.name = name
        self.description = description
        self.rating = rating
        self.price = price
        self.image = image
        self.id = id  # Track the joke ID

    @property
    def votes(self):
        rate_sum:int=0
        if len(self.rating)>0:
            for rate in self.rating:
                rate_sum += rate
            return int(rate_sum/len(self.rating))
        elif len(self.rating)==0:
            return 0

    def save(self):
        folder = os.path.join(MERCH_FOLDER, self.category)
        if self.id is None:
            # New merch: assign a new ID
            existing = os.listdir(folder)
            self.id = len(existing) + 1
        filepath = os.path.join(folder, f"{self.id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f)

    @staticmethod
    def load(category, merch_id):
        path = os.path.join(MERCH_FOLDER, category, f"{merch_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Merch(**data)

    @staticmethod
    def load_all():
        merchandise = []
        for cat in CATEGORIES:
            folder = os.path.join(MERCH_FOLDER, cat)
            for filename in os.listdir(folder):
                path = os.path.join(folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    merchandise.append(Merch(**data))
        return merchandise

    @staticmethod
    def load_category(category):
        merchandise = []
        folder = os.path.join(MERCH_FOLDER, category)
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                merchandise.append(Merch(**data))
        return merchandise








@app.route("/", methods=["GET"])
def index():
    category = request.args.get("filter")
    if category and category in CATEGORIES:
        merchandise = Merch.load_category(category)
    else:
        merchandise = Merch.load_all()
    amount = len(merchandise)
    return render_template("index.html", title=TITLE, categories=CATEGORIES, merchandise=merchandise, amount=amount)



@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        category = request.form["category"]
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        image = request.files["image"]
        image_name = image.filename
        while os.path.exists(IMAGE_FOLDER + "/" + image_name):
            image_name = str(random.randint(1,999))+image_name
        image.save(os.path.join(app.config['IMAGE_FOLDER'], image_name))
        merch = Merch(category, name, description, price, image_name)
        merch.save()
        return redirect(url_for("index"))
    return render_template("add.html",categories=CATEGORIES)

@app.route("/product/<string:category>/<int:id>")
def product(category:str, id:int):
    if category in CATEGORIES:
        item:Merch = Merch.load(category, id)
        return render_template("product.html", merch=item)
    else:
        return redirect(url_for("index"))

@app.route("/vote/<string:category>/<int:id>", methods=["POST"])
def vote(category:str, id:int):
    if category in CATEGORIES and request.method == "POST":
        item:Merch = Merch.load(category, id)
        item.rating.append(int(request.form["rating"]))
        item.save()
        return redirect(url_for("product", category=category, id=item.id))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("index"))

@app.errorhandler(Exception)
def error(e):
    return f"Fuck, {e}"


if __name__ == "__main__":
    app.run(debug=DEBUG,host="0.0.0.0")