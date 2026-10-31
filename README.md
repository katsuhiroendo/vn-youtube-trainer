# YouTubeベトナム語トレーナー

YouTubeの「英語↔ベトナム語」動画を教材にして、聞き取りと発話を練習するWebアプリです。

- 公開URL（設定後）: https://katsuhiroendo.github.io/vn-youtube-trainer/
- PC・スマホのブラウザ（Chrome推奨）でそのまま使えます。インストールは不要です。

## フォルダ構成

```
index.html                    アプリ本体（基本的に触らない）
content/                      教材フォルダ（ここに JSON を追加するだけ）
  01-daily-phrases.json       01 日常会話102フレーズ
  02-vietnamese-food.json     02 ベトナム料理の名前と例文
  index.json                  教材一覧（GitHub Pages では自動検出されるので更新は任意）
start_windows.bat / start_mac.command   手元PCで動かす場合の起動スクリプト（任意）
```

## 教材の追加方法

1. YouTube の「文字起こし」をコピーし、URL と一緒に Claude に渡して「教材JSONを作って」と依頼する
2. 受け取った `.json` を **content フォルダにアップロード**する
   https://github.com/katsuhiroendo/vn-youtube-trainer/upload/main/content
   （ファイルをドラッグ＆ドロップ →「Commit changes」）
3. 1〜3分後にアプリを再読み込みすると、教材を選ぶメニューに追加される

ファイル名の先頭に番号（`03-…json`）を付けると、その順に並びます。

## 教材JSONの形式

```json
{
  "vid": "YouTube動画ID(11文字)",
  "title": "03 教材名",
  "url": "https://www.youtube.com/watch?v=...",
  "note": "補足",
  "items": [
    {"id": 1, "t0": 4.0, "t1": 6.7, "e1": 12.2, "t2": 18.0, "t3": 24.4,
     "word": {"vi": "Phở bò", "ja": "牛肉のフォー"},
     "vi": "Chị ơi cho em một tô phở bò ít hành.",
     "ja": "すみません、牛肉のフォーを1杯、ネギ少なめでください。",
     "en": "Excuse me, can I have a bowl of beef phở with less green onion, please?",
     "w": [["ít", "少ない"], ["hành", "ネギ"]],
     "note": "cho em … で「〜ください」"}
  ]
}
```

| 項目 | 意味 |
|---|---|
| t0 | その項目の開始（秒） |
| t1 | ベトナム語の1回目の開始 |
| e1 | 1回目の終わり（省略すると t2 まで） |
| t2 | ベトナム語の2回目の開始（無ければ null） |
| t3 | 項目の終わり |
| word | 単語（任意）。料理名など |

## 学習の進め方

- 1フレーズを **聞き取り** と **発話** の2枚のカードとして別々に管理する（SM-2系の間隔反復）
- 新しいフレーズ：動画を確認 → シャドーイング×3 → 1問後に聞き取り → 3問後に発話
- 覚えるほど出題が難しくなる
  - 聞き取り：意味4択 → 単語並べ替え → 書き取り
  - 発話：音読 → 頭文字ヒント → 日本語のみ
- 書き取り・発話は音節ごとに採点し、声調だけの違いは別色で表示する
- 進捗はブラウザに保存される（端末ごと）。「進捗・設定」から書き出し・読み込みができる
