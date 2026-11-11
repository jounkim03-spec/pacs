"""Generate synthetic CT/localizer and DX, then send with C-STORE."""
import argparse,json
from pathlib import Path
import numpy as np
from pydicom.dataset import FileDataset,FileMetaDataset
from pydicom.uid import generate_uid,ExplicitVRLittleEndian,CTImageStorage,DigitalXRayImageStorageForPresentation
from pynetdicom import AE
p=argparse.ArgumentParser()
p.add_argument('--host',default='localhost');p.add_argument('--port',type=int,default=4242)
p.add_argument('--aet',default='ORTHANC');p.add_argument('--directory',default='samples')
a=p.parse_args();root=Path(a.directory);root.mkdir(exist_ok=True)
if not list(root.glob('*.dcm')):
 manifest=[]
 for modality in ['CT','DX']:
  study,frame=generate_uid(),generate_uid()
  groups=[('AXIAL',32),('LOCALIZER',1)] if modality=='CT' else [('XRAY',1)]
  for kind,count in groups:
   series=generate_uid()
   for i in range(count):
    sop=CTImageStorage if modality=='CT' else DigitalXRayImageStorageForPresentation
    meta=FileMetaDataset();meta.MediaStorageSOPClassUID=sop;meta.MediaStorageSOPInstanceUID=generate_uid();meta.TransferSyntaxUID=ExplicitVRLittleEndian
    d=FileDataset('',{},file_meta=meta,preamble=b'\0'*128)
    d.SOPClassUID=sop;d.SOPInstanceUID=meta.MediaStorageSOPInstanceUID
    d.PatientName='SYNTHETIC^DEMO';d.PatientID='DEMO001'
    d.StudyInstanceUID=study;d.SeriesInstanceUID=series;d.FrameOfReferenceUID=frame
    d.StudyDate='20260101';d.StudyTime='120000';d.StudyID=modality;d.AccessionNumber=modality
    d.Modality=modality;d.StudyDescription='Synthetic '+modality;d.SeriesDescription=kind
    d.SeriesNumber=1 if kind=='AXIAL' else 2;d.InstanceNumber=i+1
    d.ImageType=['ORIGINAL','PRIMARY',kind];d.PatientPosition='HFS'
    d.Rows=d.Columns=256;d.PixelSpacing=[1,1];d.SliceThickness=3
    d.ImageOrientationPatient=[1,0,0,0,0,1] if kind=='LOCALIZER' else [1,0,0,0,1,0]
    d.ImagePositionPatient=[-128,0,-20] if kind=='LOCALIZER' else [-128,-128,i*3]
    d.SamplesPerPixel=1;d.PhotometricInterpretation='MONOCHROME2'
    d.BitsAllocated=d.BitsStored=16;d.HighBit=15;d.PixelRepresentation=1
    d.RescaleIntercept=0;d.RescaleSlope=1;d.WindowCenter=40;d.WindowWidth=400
    y,x=np.mgrid[-128:128,-128:128];image=np.full((256,256),-1000,dtype=np.int16)
    image[(x/90)**2+(y/65)**2<1]=40
    image[x*x+y*y<100]=700
    d.PixelData=image.tobytes();d.save_as(root/(d.SOPInstanceUID+'.dcm'),enforce_file_format=True)
  manifest.append({'modality':modality,'StudyInstanceUID':study,'instances':sum(n for _,n in groups)})
 (root/'manifest.json').write_text(json.dumps(manifest,indent=2))
import pydicom
ae=AE(ae_title='DEMO_SCU')
for sop in [CTImageStorage,DigitalXRayImageStorageForPresentation]: ae.add_requested_context(sop,ExplicitVRLittleEndian)
assoc=ae.associate(a.host,a.port,ae_title=a.aet)
if not assoc.is_established: raise SystemExit('Association failed')
failed=0
try:
 for file in root.glob('*.dcm'):
  status=assoc.send_c_store(pydicom.dcmread(file))
  ok=status is not None and status.Status==0
  print(file.name,'OK' if ok else 'FAILED');failed+=not ok
finally: assoc.release()
raise SystemExit(1 if failed else 0)
