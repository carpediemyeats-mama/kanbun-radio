import json,requests,time,io,re
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine
ROOT=Path(__file__).parent; SITE=ROOT/'site'; SITE.mkdir(exist_ok=True)
e=json.loads((ROOT/'episode.json').read_text()); API='http://127.0.0.1:50021'
def voice(text,role):
 speaker=13 if role=='classic' else 30
 q=requests.post(API+'/audio_query',params={'text':text,'speaker':speaker},timeout=60);q.raise_for_status();data=q.json();data['speedScale']=0.84 if role=='classic' else 0.96;data['pitchScale']=-0.08 if role=='classic' else -0.025;data['intonationScale']=1.08 if role=='classic' else 1.20
 r=requests.post(API+'/synthesis',params={'speaker':speaker},json=data,timeout=180);r.raise_for_status()
 if not r.content.startswith(b'RIFF'):raise RuntimeError('No WAV')
 return AudioSegment.from_file(io.BytesIO(r.content),format='wav').set_frame_rate(44100).set_channels(2)
def speak_naturally(text,role):
 result=AudioSegment.silent(duration=0,frame_rate=44100).set_channels(2)
 for sentence in re.findall(r'[^。！？!?]+[。！？!?]?',text):
  sentence=sentence.strip()
  if not sentence:continue
  parts=re.split(r'(?<=、)',sentence) if len(sentence)>65 else [sentence]
  for part in parts:
   part=part.strip()
   if not part:continue
   result+=voice(part,role)
   pause=530 if part.endswith(('？','?')) else 400 if part.endswith(('。','！','!')) else 190
   result+=AudioSegment.silent(duration=pause,frame_rate=44100).set_channels(2)
 return result
def jingle():
 a=AudioSegment.silent(duration=1400,frame_rate=44100).set_channels(2)
 for n,pos in [(392,0),(494,300),(587,600),(392,950)]:a=a.overlay(Sine(n).to_audio_segment(duration=330).apply_gain(-27).set_channels(2),position=pos)
 return a.fade_out(300)
whole=jingle();chapters=[]
for ch in e['chapters']:
 chapters.append({'title':ch['title'],'start_seconds':round(len(whole)/1000,1)})
 for line in ch['lines']:
  whole+=speak_naturally(line['text'],line['role'])+AudioSegment.silent(duration=170)
 whole+=AudioSegment.silent(duration=450)
whole+=jingle();out=SITE/'episode.mp3';whole.export(out,format='mp3',bitrate='128k')
check=AudioSegment.from_mp3(out)
if len(check)<90000 or out.stat().st_size<100000:raise RuntimeError('Audio too short')
seconds=round(len(check)/1000);(SITE/'episode.json').write_text(json.dumps({'edition':e['edition'],'title':e['title'],'seconds':seconds,'chapters':chapters},ensure_ascii=False),encoding='utf-8')
print('DONE',seconds,out.stat().st_size)
