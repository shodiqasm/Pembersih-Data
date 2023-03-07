import re
import pandas as pd
import sqlite3
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from, LazyString, LazyJSONEncoder

app = Flask(__name__)
api = Api(app)

# Membuat database
conn = sqlite3.connect('docs/database.db')

# Membuat table dalam database.db
conn.execute("""CREATE TABLE IF NOT EXISTS hasil 
                (sebelum varchar(255), 
                setelah varchar(255))""")

app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info = {
        'title': LazyString(lambda: 'Website for Cleansing Text and Censorship for Abusive Words'),
        'version': LazyString(lambda: '0.0.1'),
        'descrption': LazyString(lambda: 'Website for Cleansing Text dan Sensor Kata Kasar')
    },
    host = LazyString(lambda: request.host)
)
Swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui":True,
    "specs_route": "/asod/"
}
swagger = Swagger(app, template=swagger_template,config=Swagger_config)

# Input database
kamus = pd.read_csv('new_kamusalay.csv',
                    encoding='ANSI',
                    header=None)

def cleanse_text(text):
    # Mengubah semua huruf menjadi lowercase
    text = text.lower()
    # Menghapus tanda baca dan karakter spesial
    text = re.sub(r'[^a-zA-Z0-9 .,?]', '', text)
    # Menyensor kata abusive
    abusive = pd.read_csv('abusive.csv')["ABUSIVE"].tolist()
    pattern = re.compile(r'\b(' + '|'.join(abusive) + r')\b', re.IGNORECASE)
    text = pattern.sub('****',text)
    return text

class Endpoint1(Resource):
    @swag_from('docs/endpoint1.yml')
    def post(self):
        # Mendapatkan teks dari input request
        text = request.form.get('text')
        # Membersihkan teks
        cleansed_text = cleanse_text(text)
        # Mengembalikan respons dengan teks yang sudah dicleansing
        json_response = {
            'status_code': 200,
            'description': "text has been cleansed",
            'data': cleansed_text
        }
        response_data = jsonify(json_response)
        return response_data

    # Memasukan hasil cleansing ke database    
    def process_data(text):
        c = conn.cursor()
        cleansed_text = cleanse_text(text)
        c.execute("INSERT INTO hasil VALUES (sebelum,sesudah), (text, cleansed_text)")
        conn.commit()
        conn.close()

class Endpoint2(Resource):
    @swag_from('docs/endpoint2.yml')
    def post(self):
        # Membaca file CSV dari input request
        csv_file = request.files['file']
        # Membaca file CSV menggunakan pandas
        df = pd.read_csv(csv_file, encoding='ANSI')
        # Mencari nama kolom yang bertipe objek
        for col in df.select_dtypes(include='object').columns:
            # Mengubah nama kolom
            df.rename(columns={col:'text'}, inplace=True)
        # Mengganti kata yang terdapat di new_kamusalay.csv
        df['text']=df['text'].replace(kamus.set_index(0)[1])
        # Melakukan cleansing pada setiap nilai pada kolom 'text'
        df['text'] = df['text'].apply(cleanse_text)
        # Mengonversi dataframe menjadi list of dictionaries
        data = df.to_dict('records')
        # Mengembalikan respons dengan data yang sudah dicleansing
        json_response = {
            'status_code': 200,
            'description': "file has been cleansed",
            'data': data
        }
        response_data = jsonify(json_response)
        return response_data

api.add_resource(Endpoint1, '/CleanseText')
api.add_resource(Endpoint2, '/CleanseCSV')

if __name__ == '__main__':
    app.run(debug=True)