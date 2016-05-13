# coding=utf-8

import sys
sys.path.append("Ubiqu")

from Ubiqu import app as ubiquApp

if __name__ == '__main__':
    port = 5001
    ubiquApp.app.run(host='127.0.0.1', port=port, debug=True)
