from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
from flask_mysqldb import MySQL
import pandas as pd
import io
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter