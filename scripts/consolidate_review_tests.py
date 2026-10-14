"""Consolida el resultado más reciente de cada caso sin ocultar fallos pendientes.

Conserva informes originales y procedencia individual. No suma casos repetidos.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('reports',type=Path,nargs='+')
    args=parser.parse_args()
    cases={};provenance={}
    for report in args.reports:
        for case in ET.parse(report).findall('.//testcase'):
            key=(case.get('classname',''),case.get('name',''))
            cases[key]=case;provenance['::'.join(key)]=report.name
    pending=[key for key,case in cases.items() if any(case.find(tag) is not None for tag in ('failure','error','skipped'))]
    if not cases or pending:
        raise RuntimeError(f'Quedan casos sin aprobar: {pending}')
    duration=sum(float(c.get('time','0')) for c in cases.values())
    root=ET.Element('testsuites')
    suite=ET.SubElement(root,'testsuite',name='Casos únicos; último resultado por caso',tests=str(len(cases)),failures='0',errors='0',skipped='0',time=f'{duration:.3f}')
    for key in sorted(cases):suite.append(cases[key])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(args.output,encoding='utf-8',xml_declaration=True)
    manifest={'method':'Último resultado por classname/name; fuentes originales conservadas','unique_tests':len(cases),
              'case_duration_seconds':round(duration,3),'reports':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.reports},'case_sources':provenance}
    args.output.with_suffix('.provenance.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'result':'PASS','unique_tests':len(cases)}))


if __name__=='__main__':main()
