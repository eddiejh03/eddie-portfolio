from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/education")
def education():
    return render_template("education.html")

@app.route("/experience")
def experience():
    return render_template("experience.html")

@app.route("/resume")
def resume():
    return render_template("resume.html")

@app.route("/download-resume")
def download_resume():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'resume.pdf', as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)