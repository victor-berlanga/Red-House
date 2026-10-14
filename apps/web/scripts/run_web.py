"""Entrada independiente del portal integrado; configuración de cliente sin claves de MS."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src import create_app
from waitress import serve


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--port',type=int,default=5050)
    args=parser.parse_args()
    app=create_app({'BACKEND_MODE':'microservices','MICROSERVICES_CONFIG':args.config})
    serve(app,host='127.0.0.1',port=args.port,threads=8,max_request_body_size=65536)


if __name__=='__main__':
    main()
