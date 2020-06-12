from mpi4py import MPI
import numpy as np
from PIL import Image, ImageFilter, ImageFile
import cv2
import urllib.request
import requests
from io import BytesIO
import io
import base64
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google.cloud import firestore, storage
import base64
import string
import random
import time


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/mpi/fire.json"
comm = MPI.COMM_WORLD
r = comm.Get_rank()
globalFullImage = ''
globalImage = ''
globalImageUrl = ''
response = ''

#Genera un string random para el nombre de la imagen
def random_generator(size=15, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

#filtro obenido de https://stackoverflow.com/questions/36434905/processing-an-image-to-sepia-tone-in-python
#despues de muchos intentos no pude realizar mi propio filtro sepia
def makeSepia(img):
    width, height = img.size
    pixels = img.load() 
    for py in range(height):
        for px in range(width):
            r, g, b = img.getpixel((px, py))
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            if tr > 255:
                tr = 255

            if tg > 255:
                tg = 255

            if tb > 255:
                tb = 255
            pixels[px, py] = (tr,tg,tb)
    return img

def upload_blob(imageData):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    randomString = random_generator()
    storage_client = storage.Client()
    bucket = storage_client.bucket('proyecto_final')
    blob = bucket.blob(randomString+'.jpg'+'')
    blob.upload_from_string(imageData)
    return "https://storage.cloud.google.com/proyecto_final/"+randomString+'.jpg'


def filterOne(url):
    file = io.BytesIO(urllib.request.urlopen(url).read())
    image = Image.open(file)
    imageArray = np.asarray(image)
    #Le resta 255 a todo el arreglo, invierte los colores debido a eso
    im_i = 255 - imageArray
    pil_img = Image.fromarray(im_i)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    #transformación a base 64 para poder guardar y enviar la imagen
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    return new_image_string


def filterTwo(url):
    image = Image.open(requests.get(url, stream=True).raw).filter(ImageFilter.EMBOSS)
    imageArray = np.asarray(image)
    pil_img = Image.fromarray(imageArray)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    #transformación a base 64 para poder guardar y enviar la imagen
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    return new_image_string


def filterThree(url):
    # L = single channel image, de rgb pasa a un solo canal por lo que se convierte en blanco y negro
    image = Image.open(requests.get(url, stream=True).raw).convert('L')
    imageArray = np.asarray(image)
    pil_img = Image.fromarray(imageArray)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    #transformación a base 64 para poder guardar y enviar la imagen
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    return new_image_string

def filterFour(url):
    image = Image.open(requests.get(url, stream=True).raw).filter(ImageFilter.CONTOUR)
    imageArray = np.asarray(image)
    pil_img = Image.fromarray(imageArray)
    buff = BytesIO()
    pil_img.save(buff, format="JPEG")
    #transformación a base 64 para poder guardar y enviar la imagen
    new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
    return new_image_string

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route('/upload-picture',methods = ['POST'])
def uploadPicture():
    if request.method == 'POST':
        response = 'empty'
        image = request.form.get('image')
        global globalFullImage
        globalFullImage = image
        global globalImage
        globalImage = image.split("base64,")[1]
        imgdata = base64.b64decode(globalImage)
        blobName = upload_blob(imgdata)
        response = jsonify({'data': blobName})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        return 'Error'

@app.route('/save-picture',methods = ['POST'])
def savePicture():
    if request.method == 'POST':
        response = 'empty'
        image = request.form.get('image')
        db = firestore.Client()
        doc_ref = db.collection(u'datos').document(u'imagen')
        doc_ref.set({
            u'url': image
        })
        response = jsonify({'data': 'Exito'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        return 'Error'

@app.route('/get-picture',methods = ['POST'])
def getPicture():
    if request.method == 'POST':
        response = 'empty'
        image = request.form.get('image')
        db = firestore.Client()
        doc_ref = db.collection(u'datos').document(u'imagen')
        doc = doc_ref.get()
        response = jsonify({'data':doc.to_dict()})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        return 'Error'

@app.route('/get-filter',methods = ['POST'])
def getFilter():
    if request.method == 'POST':
        result = []
        image = request.form.get('image')
        result.append(filterOne("https://storage.googleapis.com/proyecto_final/test.jpg"))
        result.append(filterTwo("https://storage.googleapis.com/proyecto_final/test.jpg"))
        result.append(filterThree("https://storage.googleapis.com/proyecto_final/test.jpg"))
        result.append(filterFour("https://storage.googleapis.com/proyecto_final/test.jpg"))
        response = jsonify({'data': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/get-filter-parallel',methods = ['POST'])
def getFilterParallel():
    if request.method == 'POST':
        result = []
        image = request.form.get('image')
        if r == 0:
            result.append(filterOne("https://storage.googleapis.com/proyecto_final/test.jpg"))
            data = {'Termine'}
            res = comm.bcast(data, root=0)
            comm.barrier()
        elif r == 1:
            result.append(filterTwo("https://storage.googleapis.com/proyecto_final/test.jpg"))
            data = {'Termine'}
            res = comm.bcast(data, root=1)
            comm.barrier()
        elif r == 2:
            data = {'Termine'}
            res = comm.bcast(data, root=2)
            comm.barrier()
            result.append(filterThree("https://storage.googleapis.com/proyecto_final/test.jpg"))
        elif r == 3:
            data = {'Termine'}
            res = comm.bcast(data, root=3)
            comm.barrier()
            result.append(filterFour("https://storage.googleapis.com/proyecto_final/test.jpg"))      
        response = jsonify({'data': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000")
