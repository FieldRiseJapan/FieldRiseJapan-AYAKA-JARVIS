# AYAKA JARVIS — v0.1「彩花の耳」

Python の Windows WASAPI 録音から whisper.cpp の日本語音声認識へ接続し、認識結果から「彩花」などのウェイクワードを検出する最小構成です。SDL2 の `whisper-stream` 録音経路は使用しません。

## v0.1 の構成

```text
Jabra Speak2 40 MS
        │ Windows WASAPI
        ▼
Python sounddevice / recorder.py
        │ 5秒 WAV
        ▼
whisper.cpp whisper-cli.exe + ggml-small.bin
        │ 日本語テキスト
        ▼
WakeWordDetector（「彩花」）
        │
        └── 任意: PowerShell System.Speech「はい、社長。」
```

コードは後続の Speaker ID、LLM、TTS、UI を追加しやすいように、設定・録音・STT・ウェイクワード検出を分離しています。

## Windows セットアップ

1. Python 3.13 64bit と whisper.cpp x64 ビルドを用意します。
2. リポジトリ直下で仮想環境を作り、依存関係をインストールします。

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

3. `config.json` の `whisper.executable` と `whisper.model` を実際の配置に合わせます。大容量モデルはGitHubへコミットせず、ローカルの `models/` に置いてください。
4. 既定では `Jabra Speak2 40 MS` と `Windows WASAPI` を名前で自動検出します。検出できない場合だけ `audio.device_index` に確認済みの番号を設定します。デバイス番号はPC環境により変わるため、恒久的な識別子として扱わないでください。

## 起動

簡単に起動する場合:

```text
run_ayaka.bat
```

または:

```powershell
.venv\Scripts\python.exe -m ayaka.main --config config.json --tts
```

5秒ごとに録音して文字起こしし、コンソールへ次のように表示します。

```text
認識結果: 彩花、おはよう
ウェイクワード検出: 彩花
```

`--tts` を付けると、ウェイクワード検出時に Windows の `System.Speech` で「はい、社長。」と発話します。音声設定そのものは変更しません。

## 既存WAVでの確認

実機で作成済みの `ayaka_test.wav` を、マイクを使わずに確認できます。

```powershell
.venv\Scripts\python.exe -m ayaka.main --config config.json --wav ayaka_test.wav
```

この経路では、音声入力が正常に保存されているかと、whisper.cpp の日本語STTおよび「彩花」検出を分離して検証できます。

## テスト

外部音声デバイスを必要としないユニットテストを実行します。

```powershell
python -m unittest discover -s tests -v
```

テスト対象は、名前・WASAPI・入力チャンネルによるデバイス選択、全角・空白・句読点を含むウェイクワード検出、既定設定です。録音とwhisper.cppは実機依存のため、`--wav` の手動確認を別途行います。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `ayaka/config.py` | 音声・whisper・アプリ設定の型付き定義 |
| `ayaka/devices.py` | WASAPIホストAPIと入力デバイスの自動検出 |
| `ayaka/recorder.py` | sounddeviceによるWAV録音 |
| `ayaka/stt.py` | whisper.cpp `whisper-cli` 呼び出し |
| `ayaka/wake.py` | 日本語ウェイクワード検出 |
| `ayaka/main.py` | 既存WAVの一回処理と連続実行 |
| `config.example.json` | 安全な設定テンプレート |
| `run_ayaka.ps1` / `.bat` | Windows起動スクリプト |
| `tests/test_core.py` | 外部デバイス不要のコアテスト |

## トラブルシューティング

### 入力デバイスが見つからない

Windowsの「サウンド入力」でJabraが入力デバイスとして有効か確認してください。`config.json` の名前は部分一致で評価されます。WASAPIの表示名が異なる場合は `hostapi_name` と `device_name` を修正してください。番号を設定する場合も、毎回 `sounddevice.query_devices()` で確認してください。

### whisper実行ファイルまたはモデルが見つからない

エラーメッセージに表示されたパスを確認し、`config.json` の相対パスがリポジトリ直下から正しいことを確認してください。モデルファイル、`vendor/whisper.cpp` のビルド成果物、WAVはGitHubへ追加しません。

### 無音のWAVになる

SDL2経路へ戻らず、PythonのWASAPI経路を使用してください。`ayaka_latest.wav` をWindowsで再生して無音なら、Jabraの入力選択、Windowsのマイク権限、他アプリによる占有を確認します。

### 認識精度が低い

まず `--wav ayaka_test.wav` で録音とSTTを切り分けます。5秒チャンク、16kHz、1chを基準にし、モデルやチャンク長の変更は一度に一つだけ行ってください。

## セキュリティとGit管理

`config.json`、`.env`、APIキー、モデル、録音ファイル、whisper.cppのビルド成果物は `.gitignore` 対象です。APIキーをこのアプリに直接埋め込まず、将来LLM連携を追加する場合は環境変数などから読み込みます。
