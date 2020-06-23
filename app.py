# -*- encoding=UTF-8 -*-
from flask import render_template, redirect, Flask

from astgram import app

if __name__ == '__main__':
    app.run(debug=True)
