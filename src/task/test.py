import os
import flask
import flask_cors

flask_app = flask.Flask("dsjakld")


flask_cors.CORS(flask_app)
flask_app.config['CORS_HEADERS'] = 'Content-Type'


@flask_app.after_request
def cors(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Private-Network', "true")


    response.headers.add('Access-Control-Allow-Methods', "POST, GET, OPTIONS, DELETE")
    return response

@flask_app.route('/task/<path:path>')
def static_file1(path):
    p = "./" + path
    return flask.send_file(p)


# ssl_context='adhoc'
flask_app.run("0.0.0.0", 12980, False)




