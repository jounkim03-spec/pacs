"""Send existing DICOM files without generating or modifying their contents."""
import argparse
from pathlib import Path
import sys
import pydicom
from pydicom.errors import InvalidDicomError
from pynetdicom import AE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="DICOM file or folder (recursive)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4242)
    parser.add_argument("--aet", default="ORTHANC")
    args = parser.parse_args()
    if not args.path.exists():
        parser.error("Path does not exist")
    files = sorted(args.path.rglob("*")) if args.path.is_dir() else [args.path]
    sent = warnings = failed = skipped = 0
    for path in files:
        if not path.is_file():
            continue
        try:
            ds = pydicom.dcmread(path)
        except InvalidDicomError:
            # Do not force-read arbitrary files or silently reinterpret them.
            skipped += 1
            print(f"SKIP (not a Part 10 DICOM): {path}")
            continue
        except Exception as exc:
            failed += 1
            print(f"READ FAILED: {path}: {exc}", file=sys.stderr)
            continue
        if not all(getattr(ds, key, None) for key in ("SOPClassUID", "SOPInstanceUID", "StudyInstanceUID")) or not getattr(ds.file_meta, "TransferSyntaxUID", None):
            failed += 1
            print(f"FAILED (missing required UID/transfer syntax): {path}", file=sys.stderr)
            continue
        # Negotiate the original syntax so compressed data is not transcoded.
        ae = AE(ae_title="PACS_IMPORT")
        ae.add_requested_context(ds.SOPClassUID, ds.file_meta.TransferSyntaxUID)
        ae.acse_timeout = ae.dimse_timeout = ae.network_timeout = 30
        assoc = None
        try:
            assoc = ae.associate(args.host, args.port, ae_title=args.aet)
            if not assoc.is_established:
                raise RuntimeError("DICOM association rejected or unavailable")
            status = assoc.send_c_store(ds)
            code = getattr(status, "Status", None)
            if code == 0:
                sent += 1
                print(f"OK: {path} StudyInstanceUID={ds.StudyInstanceUID}")
            elif code in (0xB000, 0xB006, 0xB007):
                warnings += 1
                print(f"WARNING 0x{code:04X}: {path}", file=sys.stderr)
            else:
                raise RuntimeError(f"C-STORE status={code}")
        except Exception as exc:
            failed += 1
            print(f"SEND FAILED: {path}: {exc}", file=sys.stderr)
        finally:
            if assoc is not None and assoc.is_established:
                assoc.release()
    print(f"Sent={sent}, warnings={warnings}, failed={failed}, skipped={skipped}")
    return 0 if sent and not failed and not warnings else 1


if __name__ == "__main__":
    raise SystemExit(main())
