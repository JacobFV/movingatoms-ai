"""Build pinned public wall-property graph probe; raw outputs remain local."""
import argparse,json,subprocess,tempfile
from pathlib import Path
from schema_probe import REV


def build(source,target,directory):
 source=source.resolve();target=target.resolve()
 if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader revision mismatch')
 subprocess.run(['git','-C',str(source),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
 with tempfile.TemporaryDirectory(dir=directory) as temp:
  p=Path(temp);(p/'src').mkdir();(p/'src/main.rs').write_bytes(Path(__file__).with_suffix('.rs').read_bytes())
  (p/'Cargo.toml').write_text('[package]\nname="rvt-element-properties-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
  subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(p/'Cargo.toml'),'--target-dir',str(target)],check=True)
 return target/'release/rvt-element-properties-probe'

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('files',type=Path,nargs='+');a=p.parse_args()
 binary=build(a.reader_source,a.target,a.files[0].parent)
 for path in a.files:
  data=subprocess.check_output([str(binary),str(path)])
  output=path.parent/('element-properties-'+path.stem+'.json');output.write_bytes(data)
  print(json.dumps({'file':path.name,'raw_evidence':str(output),'bytes':len(data)}))
