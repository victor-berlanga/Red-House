"""Punto de entrada para empaquetadores y ejecución local."""
import argparse

from redhouse_desktop.app import main, smoke_report

parser = argparse.ArgumentParser()
parser.add_argument('--smoke-report', metavar='RUTA')
args = parser.parse_args()
if args.smoke_report:
    smoke_report(args.smoke_report)
else:
    main()
