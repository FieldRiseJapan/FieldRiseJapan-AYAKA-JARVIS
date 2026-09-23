# AYAKA JARVIS — v0.1「彩花の耳」

Python の Windows WASAPI 録音から whisper.cpp の日本語音声認識へ接続し、音声区間を自動検出して「彩花」などのウェイクワードを判定する構成です。SDL2 の `whisper-stream` 録音経路は使用しません。

## v0.1 の構成

```text
Jabra Speak2 40 MS
        │ Windows WASAPI
        ▼
Python sounddevice / VAD recorder
        │ 発話開始・無音終了・WAV保存
        ▼
whisper.cpp whisper-cli.exe + ggml-small.bin
        │ 日本語テキスト
        ▼
WakeWordDetector（「彩花」「おはよう」など）
        │
        └── 任意: PowerShell System.Speech 応答
```

コードは後続の Speaker ID、LLM、TTS、UI を追加しやすいように、設定・録音・VAD・STT・ウェイクワード検出を分離しています。

## Windows セットアップ

1. Python 3.13 64bit と whisper.cpp x64 Release ビルドを用意します。
2. リポジトリ直下で仮想環境を作り、依存関係をインストールします。

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

3. `config.json` の `whisper.executable` と `whisper.model` を実際の配置に合わせます。実機で確認済みの既定値は `vendor/whisper.cpp/build-release-x64/bin/whisper-cli.exe` と `vendor/whisper.cpp/ggml-small.bin` です。大容量モデルとビルド成果物はGitHubへコミットしません。
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

VAD有効時は、録音開始前に音声レベルを監視します。発話が始まるとプリロールを含めて録音し、設定時間の無音が続くと即座にWAVを保存してwhisper.cppへ渡します。発話が検出されない限り、空のWAVをwhisper.cppへ送信しません。

表示例:

```text
AYAKA JARVIS v0.1
🎧 音声待機中...
🎙️ 発話を検出しました
🔴 録音中...
⏹️ 発話終了を検出
🧠 音声認識中...
📝 認識結果: おはよう
🔔 ウェイクワード検出: おはよう
🗣️ AYAKA: おはようございます、社長。
```

`--tts` を付けると、ウェイクワード検出時に Windows の `System.Speech` で設定された応答を発話します。音声デバイス設定自体は変更しません。

## v0.2 UI foundation: three monitors

v0.2 Phase 1–2 adds a separate Tkinter UI launcher without modifying the proven audio/STT/VAD loop. It creates independent LEFT, CENTER, and RIGHT windows, discovers Windows displays through the Win32 monitor API, and assigns the primary display to LEFT. Additional displays are assigned deterministically to CENTER and RIGHT by their position. On a single display, all three roles safely fall back to the same monitor for development.

Start the UI on Windows with:

```text
run_ayaka_ui.bat
```

The LEFT window is the AYAKA character placeholder, CENTER is the FieldRise dashboard with clock, system status, core pulse, SoundOn and YouTube placeholders, and RIGHT is the MOMOKA developer panel. The current UI state model already contains AYAKA/MOMOKA themes, STANDBY/LISTENING/THINKING/SPEAKING/EXECUTING/COMPLETE states, and HOME/SNS/SOUNDON/GITHUB navigation history for the next voice-command phase.

The headless monitor mapping can be inspected without opening windows:

```powershell
py -3 -m ayaka.ui.launcher --print-layout
```

Linux validation covers monitor assignment, UI state, compilation, and the headless layout command. Actual Windows display enumeration and three-window placement require the user's Windows PC. The UI launcher is intentionally separate from `run_ayaka.bat`, which continues to launch the v0.1 voice service.

## v0.2 Phase 3–4: voice commands and mode switching

The command router converts conservatively normalized Japanese transcripts into `WAKE`, `SLEEP`, `AYAKA_MODE`, `MOMOKA_MODE`, `HOME`, `BACK`, `SNS`, `SOUNDON`, `GITHUB`, or `UNKNOWN`. Alias forms such as `サウンドオン出して`, `ギットハブ見せて`, and `SNSのデータ見せて` are supported without broad substring matching, reducing accidental activations.

For an integrated Windows test, use the new launcher:

```text
run_ayaka_jarvis.bat
```

This starts the three-monitor UI and a daemon voice worker. The worker performs the existing VAD and whisper.cpp flow, then places recognized text into a queue. Only the Tkinter main thread consumes that queue and updates UI state. `桃花` switches all three windows to the dark MOMOKA purple theme; `彩花` switches them back to AYAKA blue. `ホーム`, `戻って`, `SNS見せて`, `SoundOn見せて`, and `GitHub見せて` update the CENTER page model. `おやすみ` speaks the existing Windows TTS response and schedules UI shutdown.

The router keeps a dedicated field-tested name-alias dictionary. MOMOKA aliases are `桃花`, `ももか`, `モモカ`, `もも`, `モモ`, `まもか`, `まもかぁ`, `ももかわ`, `モモカー`, `もうもう`, `もうもうか`, `モモンカー`, `モンモンカー`, `おもが`, `もうまか`, and `何もか`. AYAKA aliases are `彩花`, `あやか`, `アヤカ`, `あやかぁ`, `あや`, `アヤ`, `おやか`, `あうや`, `アイアー`, and `あやかー`. Ambiguous field-log words such as `（笑）`, `[音楽]`, `はっ`, `まんま`, `かあ`, and `ご覧` are intentionally excluded.

The CENTER HOME dashboard is CORE-first: a large animated blue/cyan or purple/violet CORE occupies the vertical monitor's middle, while compact cards are grouped at the bottom in a 2×2 grid for SoundOn (今月収益), YouTube (直近28日再生), TikTok (直近7日再生), and Instagram (直近30日リーチ). TikTok and Instagram currently display `-- / DATA WAITING`; no social API is connected in this phase. The lightweight animation draws a pulsing sphere with multiple rings and can later be replaced by a higher-quality CORE renderer.

The existing `run_ayaka.bat` and `run_ayaka_ui.bat` launchers are unchanged. COEIROINK, idle timers, real dashboard data, character assets, and background wake-listener persistence remain later phases.

## Official AYAKA LEFT display

The LEFT monitor uses the approved AYAKA design at `assets/characters/ayaka/ayaka_left_official.png`. `ayaka/ui/left_display.py` owns this surface so the image renderer can later be replaced by Live2D or another animated character layer without changing CENTER, RIGHT, or the audio pipeline. On Windows, LEFT uses the Win32 `MONITORINFO.rcWork` work area rather than the full monitor rectangle, so a visible taskbar is excluded dynamically. The image is fit within that work area while preserving its aspect ratio; minimal letterboxing is preferred to cropping the HUD. If the asset or Pillow renderer is unavailable, the previous AYAKA placeholder is shown instead. AYAKA mode displays the official image, while MOMOKA mode keeps the existing developer fallback.

On Windows, install the added Pillow dependency and launch the integrated UI:

```powershell
py -3 -m pip install -r requirements.txt
run_ayaka_jarvis.bat
```

## VAD設定

`config.json` の `vad` で調整できます。音量値は16-bit PCMのRMSスケールです。

| 設定 | 既定値 | 意味 |
|---|---:|---|
| `enabled` | `true` | `false`にすると従来の固定録音へ戻す |
| `threshold` | `500` | 発話開始と判定するRMS閾値 |
| `silence_seconds` | `0.8` | 発話後、この秒数の無音で終了 |
| `pre_roll_seconds` | `0.3` | 発話開始直前に保持する音声 |
| `max_record_seconds` | `12.0` | 異常な長時間録音を防ぐ上限 |
| `block_seconds` | `0.02` | 音量監視のチャンク長 |

環境音で誤反応する場合は `threshold` を少し上げ、普通の声を取りこぼす場合は少し下げてください。会話の語尾が切れる場合は `silence_seconds` を長くします。

`vad` が存在しない旧 `config.json` でも、上表のデフォルト値で起動します。`enabled: false` を設定すれば、既存の固定秒数録音へ戻せます。

## 既存WAVでの確認

実機で作成済みのWAVを、マイクを使わずに確認できます。

```powershell
.venv\Scripts\python.exe -m ayaka.main --config config.json --wav ayaka_test.wav
```

この経路では、録音とSTTおよびウェイクワード判定を分離して検証できます。

## STTモデル比較ベンチマーク

Windows実機で録音した同じWAVに対して、multilingual版の `small`、`base`、`tiny` を比較できます。

```powershell
.venv\Scripts\python.exe -m ayaka.benchmark_stt runtime\ayaka_latest.wav --config config.json
```

既定では、設定されたモデルと同じディレクトリにある次の3ファイルを順番に探します。

```text
vendor/whisper.cpp/ggml-small.bin
vendor/whisper.cpp/ggml-base.bin
vendor/whisper.cpp/ggml-tiny.bin
```

`ggml-base.bin` と `ggml-tiny.bin` が未配置の場合は、そのモデルだけ `ERROR` と終了コード `2` で表示されます。モデルはwhisper.cpp公式系の配布物からWindows側へ手動で取得し、`vendor/whisper.cpp/` 配下へ配置してください。自動ダウンロードは行わず、モデルファイルはGitHubへコミットしません。

別のパスを比較する場合は、カンマ区切りで指定できます。

```powershell
.venv\Scripts\python.exe -m ayaka.benchmark_stt runtime\ayaka_latest.wav --models vendor\whisper.cpp\ggml-small.bin,vendor\whisper.cpp\ggml-base.bin,vendor\whisper.cpp\ggml-tiny.bin
```

各モデルについて、モデル名、実行時間、音声長、RTF、認識結果、whisper.cppの終了コードを表示します。Linux側では実機音声の速度・精度を断定せず、最終モデルは社長の声を録音した同一WAVでWindows実機比較を行ってください。

## テスト

外部音声デバイスを必要としないユニットテストを実行します。

```powershell
python -m unittest discover -s tests -v
```

VADテストでは、RMSによる発話開始、プリロール、無音終了、最大録音時間、発話なし時の抑制、設定の後方互換性を確認します。Windows + Jabra実機の最終確認は、音声デバイスを接続したWindows PCで別途行います。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `ayaka/config.py` | 音声・VAD・whisper・アプリ設定の型付き定義 |
| `ayaka/devices.py` | WASAPIホストAPIと入力デバイスの自動検出 |
| `ayaka/recorder.py` | 固定録音またはVAD録音によるWAV保存 |
| `ayaka/vad.py` | ハードウェア非依存のRMS VAD状態機械 |
| `ayaka/stt.py` | whisper.cpp `whisper-cli` 呼び出し |
| `ayaka/benchmark_stt.py` | 同一WAVでsmall/base/tinyを比較するベンチマーク |
| `ayaka/wake.py` | 日本語ウェイクワード検出 |
| `ayaka/main.py` | 既存WAVの一回処理と連続実行 |
| `ayaka/ui/monitors.py` | Windowsモニター検出とLEFT/CENTER/RIGHT割当 |
| `ayaka/ui/state.py` | モード、状態、テーマ、Dashboard履歴 |
| `ayaka/ui/app.py` | 3独立Tkinterウィンドウの描画 |
| `ayaka/ui/left_display.py` | AYAKA正式画像のLEFT表示、cover crop、Fallback |
| `ayaka/ui/launcher.py` | v0.2 UI起動とヘッドレス配置確認 |
| `ayaka/ui/controller.py` | IntentからUI状態への適用 |
| `ayaka/ui/integrated.py` | Queue経由の音声Worker＋UI統合起動 |
| `ayaka/ui/dashboard.py` | CENTER HOMEの4カード定義とプレースホルダー |
| `ayaka/commands.py` | 音声文字列のIntent変換と実機名前Alias辞書 |
| `config.example.json` | 安全な設定テンプレート |
| `run_ayaka.ps1` / `.bat` | Windows起動スクリプト |
| `tests/test_core.py` / `test_vad.py` / `test_benchmark.py` / `test_core_redesign.py` | 外部デバイス不要のテスト |

## トラブルシューティング

### 入力デバイスが見つからない

Windowsの「サウンド入力」でJabraが入力デバイスとして有効か確認してください。`config.json` の名前は部分一致で評価されます。WASAPIの表示名が異なる場合は `hostapi_name` と `device_name` を修正してください。番号を設定する場合も、毎回 `sounddevice.query_devices()` で確認してください。

### VADが発話を検出しない／環境音に反応する

`threshold` を調整してください。まず `500` を基準にし、検出しない場合は下げ、環境音に反応する場合は上げます。語頭が欠ける場合は `pre_roll_seconds` を増やします。語尾が切れる場合は `silence_seconds` を増やします。

### whisper実行ファイルまたはモデルが見つからない

エラーメッセージに表示されたパスを確認し、`config.json` の相対パスがリポジトリ直下から正しいことを確認してください。モデルファイル、`vendor/whisper.cpp` のビルド成果物、WAVはGitHubへ追加しません。

### 無音のWAVになる

SDL2経路へ戻らず、PythonのWASAPI経路を使用してください。`ayaka_latest.wav` をWindowsで再生して無音なら、Jabraの入力選択、Windowsのマイク権限、他アプリによる占有を確認します。必要なら一時的に `vad.enabled` を `false` にして、従来の固定録音で入力経路を切り分けます。

## セキュリティとGit管理

`config.json`、`.env`、APIキー、モデル、録音ファイル、whisper.cppのビルド成果物は `.gitignore` 対象です。APIキーをこのアプリに直接埋め込まず、将来LLM連携を追加する場合は環境変数などから読み込みます。
