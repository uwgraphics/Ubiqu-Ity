# coding=utf-8

import sys
sys.path.append("Ubiqu")

from Ubiqu import app

if __name__ == '__main__':
    port = 5001
    app.run(host='127.0.0.1', port=port, debug=True)
