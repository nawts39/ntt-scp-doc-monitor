# 🔍 NTT SCP Document Monitor

NTT Smart Connect Platform (SCP) Type-V リソースプール仕様書の変更を自動監視するシステム。

## 概要

- **監視対象**: https://cloud.nttsmc.com/doc/scp/scp_type-v_spec_resource-pool/
- **実行頻度**: 毎日午前9時（JST）
- **通知方法**: GitHub Issue自動作成
- **履歴管理**: GitHubリポジトリにスナップショット保存

## 機能

- ✅ 毎日自動でドキュメントを取得
- ✅ 前回との差分を自動検出
- ✅ 変更時にGitHub Issueを自動作成
- ✅ HTMLスナップショットの履歴管理
- ✅ 差分サマリー（追加/削除行数）
- ✅ 詳細な差分表示

## ディレクトリ構成

```
ntt-scp-doc-monitor/
├── .github/
│   └── workflows/
│       └── doc-monitor.yml     # GitHub Actions workflow
├── scripts/
│   ├── fetch_doc.py            # ドキュメント取得スクリプト
│   └── check_diff.py           # 差分検出スクリプト
├── snapshots/                  # 日次スナップショット保存先
│   └── YYYYMMDD.html
└── README.md
```

## セットアップ

### 1. GitHubリポジトリ作成

```bash
# GitHub CLIでリポジトリ作成
gh repo create ntt-scp-doc-monitor --public --description "NTT SCP仕様書変更監視"

# または手動でGitHub.comから作成
```

### 2. ローカル初期化

```bash
cd /Users/naofumiiso/command/claude/ntt-scp-doc-monitor
git init
git add .
git commit -m "Initial commit: Setup document monitoring system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ntt-scp-doc-monitor.git
git push -u origin main
```

### 3. GitHub Actions有効化

リポジトリ設定で以下を確認:

- **Settings > Actions > General**
  - "Allow all actions and reusable workflows" を選択
  - "Workflow permissions": "Read and write permissions" を有効化
  - "Allow GitHub Actions to create and approve pull requests" をチェック

### 4. 初回実行（手動テスト）

1. GitHubリポジトリの **Actions** タブを開く
2. "NTT SCP Document Monitor" ワークフローを選択
3. **Run workflow** ボタンをクリック
4. 実行完了後、Issuesタブに通知が作成されることを確認

## 使い方

### 自動実行

- 毎日午前9時（JST）に自動実行
- 変更検知時のみIssue作成

### 手動実行

1. GitHub > Actions > "NTT SCP Document Monitor"
2. "Run workflow" > "Run workflow"

### 通知の確認

- **Issues**タブに新しいIssueが作成される
- タイトル: `🚨 NTT SCP仕様書が更新されました (YYYYMMDD)`
- 内容:
  - 変更サマリー（追加/削除行数）
  - 詳細な差分表示
  - 最新スナップショットへのリンク

### 履歴の確認

```bash
# スナップショット一覧
ls -l snapshots/

# 特定日時のスナップショット表示
cat snapshots/20260120.html

# 差分比較
git diff snapshots/20260119.html snapshots/20260120.html
```

## カスタマイズ

### 監視頻度の変更

`.github/workflows/doc-monitor.yml` の `cron` を編集:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # 6時間ごと
    - cron: '0 0 * * 1'    # 毎週月曜日
```

### 監視URLの追加

複数URLを監視する場合:

1. `doc-monitor.yml` にマトリックス戦略を追加
2. 各URL用のスナップショットディレクトリを分離

### 通知先の変更

Slack通知を追加する場合:

```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## トラブルシューティング

### ワークフローが実行されない

- **Settings > Actions** の権限設定を確認
- リポジトリがpublicであることを確認（privateの場合、GitHub Actions分数制限あり）

### Issue作成に失敗する

- **Settings > Actions > General > Workflow permissions** で "Read and write permissions" が有効か確認

### 差分が検出されすぎる

- `scripts/fetch_doc.py` でスクリプトタグなどの動的コンテンツを除外済み
- さらに除外したい要素がある場合、`fetch_doc.py` を編集

## ライセンス

MIT License

## 参考リンク

- [NTT SCP Type-V 仕様書](https://cloud.nttsmc.com/doc/scp/scp_type-v_spec_resource-pool/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
