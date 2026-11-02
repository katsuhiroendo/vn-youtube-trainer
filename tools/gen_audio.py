"""教材JSON（content/*.json）のベトナム語から高品質な音声(MP3)を生成する。

- 音声: Microsoft ニューラル音声（edge-tts）
    f = vi-VN-HoaiMyNeural（女性） / m = vi-VN-NamMinhNeural（男性）
- 速度: n = 通常 / s = ゆっくり
- 出力: audio/{voice}{speed}/{key}.mp3   key = sha1(正規化テキストの小文字)[:12]
- 一覧: audio/index.json  {key: テキスト}
- 日本語訳: audio/ja/{key}.mp3（ja-JP-NanamiNeural）、一覧 audio/ja.json（流し聞き用）
既に存在するファイルは作り直さないので、教材を追加したときは新しい分だけ生成される。
"""
import asyncio, glob, hashlib, json, os, re, sys, unicodedata

import edge_tts

VOICES = {'f': 'vi-VN-HoaiMyNeural', 'm': 'vi-VN-NamMinhNeural'}
SPEEDS = {'n': '-5%', 's': '-35%'}
JA_VOICE = 'ja-JP-NanamiNeural'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')


def norm(t):
    t = unicodedata.normalize('NFC', t).strip()
    return re.sub(r'\s+', ' ', t)


def key(t):
    return hashlib.sha1(norm(t).lower().encode('utf-8')).hexdigest()[:12]


def speakable(t):
    """読み上げ用に整形（記号・省略記号を除去）"""
    t = norm(t).replace('…', ' ').replace('...', ' ')
    t = re.sub(r'[（(][^）)]*[）)]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip(' /')


def speakable_ja(t):
    t = norm(t).replace('（', '、').replace('）', '').replace('(', '、').replace(')', '')
    t = t.replace('／', '、').replace('/', '、').replace('〜', '')
    t = re.sub(r'、+', '、', t).replace('。、', '。')
    return t.strip('、 ')


def collect_ja():
    texts = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'content', '*.json'))):
        if f.endswith('index.json'):
            continue
        for it in json.load(open(f, encoding='utf-8')).get('items', []):
            ja = it.get('ja', '')
            if ja and speakable_ja(ja):
                texts[key(ja)] = norm(ja)
    return texts


def collect():
    texts = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'content', '*.json'))):
        if f.endswith('index.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        for it in d.get('items', []):
            cand = [it.get('vi', '')]
            if it.get('word'):
                cand.append(it['word'].get('vi', ''))
            cand += [w[0] for w in it.get('w', []) if w]
            for c in cand:
                if c and speakable(c):
                    texts[key(c)] = norm(c)
    return texts


async def synth(text, voice, rate, path, sem, ja=False):
    async with sem:
        for attempt in range(4):
            try:
                tmp = path + '.tmp'
                if ja:
                    await edge_tts.Communicate(speakable_ja(text), JA_VOICE, rate=rate).save(tmp)
                else:
                    await edge_tts.Communicate(speakable(text), VOICES[voice], rate=rate).save(tmp)
                if os.path.getsize(tmp) < 500:
                    raise RuntimeError('empty audio')
                os.replace(tmp, path)
                return True
            except Exception as e:  # noqa: BLE001
                print(f'retry {attempt+1}: {text!r} {voice} {rate}: {e}', file=sys.stderr)
                await asyncio.sleep(2 * (attempt + 1))
        return False


async def main():
    texts = collect()
    sem = asyncio.Semaphore(4)
    jobs = []
    for k, t in texts.items():
        for v in VOICES:
            for s, rate in SPEEDS.items():
                d = os.path.join(AUDIO, v + s)
                os.makedirs(d, exist_ok=True)
                p = os.path.join(d, k + '.mp3')
                if not os.path.exists(p):
                    jobs.append(synth(t, v, rate, p, sem))
    jat = collect_ja()
    jd = os.path.join(AUDIO, 'ja'); os.makedirs(jd, exist_ok=True)
    for k, t in jat.items():
        p = os.path.join(jd, k + '.mp3')
        if not os.path.exists(p):
            jobs.append(synth(t, 'ja', '+0%', p, sem, ja=True))
    print(f'texts={len(texts)} ja={len(jat)} new files={len(jobs)}')
    res = await asyncio.gather(*jobs)
    ok = {k: t for k, t in texts.items()
          if all(os.path.exists(os.path.join(AUDIO, v + s, k + '.mp3')) for v in VOICES for s in SPEEDS)}
    json.dump(ok, open(os.path.join(AUDIO, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    jok = {k: t for k, t in jat.items() if os.path.exists(os.path.join(jd, k + '.mp3'))}
    json.dump(jok, open(os.path.join(AUDIO, 'ja.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    print(f'generated={sum(res)} failed={len(res)-sum(res)} available={len(ok)}')


if __name__ == '__main__':
    asyncio.run(main())
