#!/usr/bin/env python
from app import app
import argparse

if __name__ == '__main__':
    ## parse arguments for debug mode
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--debug", action="store_true", help="debug flask")
    args = vars(ap.parse_args())

    if args["debug"]:
        app.run(debug=True, port=8000)
    else:
       app.run(host='0.0.0.0', threaded=True ,port=8000)