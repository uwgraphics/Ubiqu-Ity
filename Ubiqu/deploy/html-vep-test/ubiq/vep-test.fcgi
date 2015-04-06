#!/p/graphics/public/vep-test/vep-python/bin/python
# coding=utf-8
path_to_module = "/p/graphics/public/vep-test/Ubiqu+Ity/Ubiqu/"
# Trailing slash required.
path_to_web = "/ubiq/"

import sys
sys.path.append(path_to_module + "..")
sys.path.append(path_to_module)

from flup.server.fcgi import WSGIServer
from Ubiqu.app import app


class ScriptNameStripper(object):
    def __init__(self, app):
        self.app = app
        # REQUIRED for correct routes with flask_util_js
        self.app.config.update(
            WEB_ROOT=path_to_web
        )

    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = path_to_web
        return self.app(environ, start_response)

app = ScriptNameStripper(app)

if __name__ == '__main__':
    WSGIServer(app).run()

