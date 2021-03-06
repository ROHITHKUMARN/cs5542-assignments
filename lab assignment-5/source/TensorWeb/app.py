#!/usr/bin/python
import flask
import time
from flask import Flask
import urllib2
import tensorflow as tf

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp/demos_uploads'
ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpe', 'jpeg'])


@app.route('/', methods=['GET', 'POST'])

def classify_index():
    string_buffer = None

    if flask.request.method == 'GET':
        url = flask.request.args.get('url')
        if url:
            string_buffer = urllib2.urlopen(url).read()

        file = flask.request.args.get('file')
        if file:
            string_buffer = open(file, 'rb').read()

        if not string_buffer:
            return flask.render_template('index.html', has_result=False)

    elif flask.request.method == 'POST':
        string_buffer = flask.request.stream.read()

    if not string_buffer:
        resp = flask.make_response()
        resp.status_code = 400
        return resp
    names, probs, time_cost, accuracy = app.clf.classify_image(string_buffer)
    return flask.make_response(u",".join(names), 200, {'ClassificationAccuracy': accuracy})


@app.route('/classify_url', methods=['GET'])
def predict():
    imageurl = flask.request.args.get('imageurl', '')
    image = url_to_img(imageurl)
    a = classify_internet(image)

    return flask.render_template('classify.html', classes=a[0:3], img=imageurl)


def classify_internet(image_data):
    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line
                   in tf.gfile.GFile("models/retrained_labels2.txt")]

    # Unpersists graph from file
    with tf.gfile.FastGFile("models/retrained_graph_bigger.pb", 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')

    li = []

    with tf.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

        predictions = sess.run(softmax_tensor, \
                               {'DecodeJpeg/contents:0': image_data})

        # Sort to show labels of first prediction in order of confidence
        top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[0][node_id]
            #st = human_string +" " + str(score)
            #li.append('%s (score = %.5f)' % (human_string, score))
            li.append(human_string)

    return li


def classify(image_path):
    image_data = tf.gfile.FastGFile(image_path, 'rb').read()

    # Loads label file, strips off carriage return
    label_lines = [line.rstrip() for line
                   in tf.gfile.GFile("models/retrained_labels2.txt")]

    # Unpersists graph from file
    with tf.gfile.FastGFile("models/retrained_graph_bigger.pb", 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')

    with tf.Session() as sess:
        # Feed the image_data as input to the graph and get first prediction
        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

        predictions = sess.run(softmax_tensor, \
                               {'DecodeJpeg/contents:0': image_data})

        # Sort to show labels of first prediction in order of confidence
        top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

        for node_id in top_k:
            human_string = label_lines[node_id]
            score = predictions[0][node_id]
            return ('%s (score = %.5f)' % (human_string, score))


def url_to_img(url):
    response = urllib2.urlopen(url)
    return response.read()


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
