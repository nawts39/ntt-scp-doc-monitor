#!/usr/bin/env python3
"""Create test diff for notification testing."""

import sys
from pathlib import Path
from datetime import datetime


def create_test_diff():
    """Create dummy diff files for testing notifications."""

    # Create summary
    summary = """📊 **変更サマリー（テストモード）**

- 追加行: 5行
- 削除行: 3行
- 合計変更: 8行
"""

    with open("diff_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    # Create detailed diff
    diff_details = """--- snapshots/20260119.html
+++ snapshots/20260120.html
@@ -100,7 +100,10 @@
 <div class="content">
-  <h2>リソースプール仕様</h2>
+  <h2>リソースプール仕様（更新版）</h2>
+  <p class="update-notice">
+    最終更新: 2026年1月20日
+  </p>
   <table class="spec-table">
     <tr>
-      <td>vCPU</td><td>最大 128コア</td>
+      <td>vCPU</td><td>最大 256コア</td>
     </tr>
     <tr>
-      <td>メモリ</td><td>最大 1TB</td>
+      <td>メモリ</td><td>最大 2TB</td>
     </tr>
   </table>
 </div>
"""

    with open("diff_details.txt", "w", encoding="utf-8") as f:
        f.write(diff_details)

    print("✅ Test diff files created")
    print("  - diff_summary.txt")
    print("  - diff_details.txt")


if __name__ == "__main__":
    create_test_diff()
