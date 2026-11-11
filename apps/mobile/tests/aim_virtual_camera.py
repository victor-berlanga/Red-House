"""Orient a real emulator virtualscene camera; never inject a barcode-reader result.

Requires grpcio in an external test environment. The protobuf fields below come from
Android Emulator 37.2.13 lib/emulator_controller.proto (PhysicalModelValue and
ParameterValue). Authentication is read locally; never print the emulator token.
"""
import argparse
import struct
from pathlib import Path
import grpc

parser=argparse.ArgumentParser()
parser.add_argument("emulator_ini",type=Path)
parser.add_argument("--position",nargs=3,type=float)
parser.add_argument("--rotation",nargs=3,type=float)
args=parser.parse_args()
config=dict(line.split("=",1) for line in args.emulator_ini.read_text().splitlines() if "=" in line)
channel=grpc.insecure_channel("127.0.0.1:"+config["grpc.port"])
metadata=[("authorization","Bearer "+config["grpc.token"])]
base="/android.emulation.control.EmulatorController/"
for target,values in ((0,args.position),(1,args.rotation)):
    if values is not None:
        # target=1; value=3 { data=1 packed float }; interpolation=4 STEP.
        request=bytes([8,target,26,14,10,12])+struct.pack("<3f",*values)+bytes([32,1])
        channel.unary_unary(base+"setPhysicalModel")(request,metadata=metadata,timeout=15)
    result=channel.unary_unary(base+"getPhysicalModel")(bytes([8,target]),metadata=metadata,timeout=15)
    print("position" if target==0 else "rotation",result.hex())
channel.close()
