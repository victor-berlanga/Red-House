"""Orient a real emulator virtualscene camera; never inject a barcode-reader result.

Requires grpcio in an external test environment. The protobuf fields below come from
Android Emulator 37.2.13 lib/emulator_controller.proto (PhysicalModelValue and
ParameterValue). Authentication is read locally; never print the emulator token.
"""
import argparse
import struct
import sys
from pathlib import Path

import grpc


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("emulator_ini",type=Path)
    parser.add_argument("--position",nargs=3,type=float)
    parser.add_argument("--rotation",nargs=3,type=float)
    args=parser.parse_args()
    config=dict(line.split("=",1) for line in args.emulator_ini.read_text().splitlines() if "=" in line)
    metadata=[("authorization","Bearer "+config["grpc.token"])]
    channel=grpc.insecure_channel("127.0.0.1:"+config["grpc.port"])
    base="/android.emulation.control.EmulatorController/"
    try:
        for target,values in ((0,args.position),(1,args.rotation)):
            if values is not None:
                # target=1; value=3 { data=1 packed float }; interpolation=4 STEP.
                request=bytes([8,target,26,14,10,12])+struct.pack("<3f",*values)+bytes([32,1])
                channel.unary_unary(base+"setPhysicalModel")(request,metadata=metadata,timeout=15)
            result=channel.unary_unary(base+"getPhysicalModel")(bytes([8,target]),metadata=metadata,timeout=15)
            print("position" if target==0 else "rotation",result.hex())
    finally:
        channel.close()


if __name__=="__main__":
    try:
        main()
    except grpc.RpcError as error:
        # Server details/debug strings may echo credentials. Never print the exception.
        print("camera_rpc_failed: "+error.code().name,file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:  # noqa: BLE001 - CLI boundary must not expose credentials in diagnostics.
        print("camera_setup_failed",file=sys.stderr)
        raise SystemExit(1) from None
