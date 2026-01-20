#!/usr/bin/env python3
"""Create test diff for notification testing."""

import sys
from pathlib import Path
from datetime import datetime


def create_test_diff():
    """Create dummy diff files for testing notifications."""

    # Create summary
    summary = """📊 **変更サマリー（テストモード）**

- 追加行: 14行
- 削除行: 6行
- 合計変更: 20行

**主な変更内容:**
- リソースプール仕様のタイトル更新
- 更新日付情報の追加
- vCPU上限: 128コア → 256コア
- メモリ上限: 1TB → 2TB
- ストレージ仕様の追加
"""

    with open("diff_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    # Create detailed diff with more HTML context
    diff_details = """--- snapshots/20260119.html
+++ snapshots/20260120.html
@@ -95,20 +95,29 @@
       </head>
       <body>
         <div class="container">
           <header>
             <h1>NTT Smart Connect Platform</h1>
             <nav>
               <ul>
                 <li><a href="#spec">仕様</a></li>
                 <li><a href="#pricing">料金</a></li>
               </ul>
             </nav>
           </header>
           <main>
             <section id="spec" class="content">
-              <h2>リソースプール仕様</h2>
+              <h2>リソースプール仕様（更新版）</h2>
+              <p class="update-notice">
+                <span class="badge">NEW</span>
+                最終更新: 2026年1月20日
+              </p>
               <table class="spec-table">
                 <thead>
                   <tr>
                     <th>項目</th>
                     <th>仕様</th>
                   </tr>
                 </thead>
                 <tbody>
                   <tr>
-                    <td>vCPU</td>
-                    <td>最大 128コア</td>
+                    <td>vCPU（仮想CPU）</td>
+                    <td>最大 256コア（従来比2倍）</td>
                   </tr>
                   <tr>
-                    <td>メモリ</td>
-                    <td>最大 1TB</td>
+                    <td>メモリ（RAM）</td>
+                    <td>最大 2TB（従来比2倍）</td>
+                  </tr>
+                  <tr>
+                    <td>ストレージ</td>
+                    <td>最大 100TB（SSD対応）</td>
                   </tr>
                 </tbody>
               </table>
             </section>
           </main>
         </div>
       </body>
     </html>
"""

    with open("diff_details.txt", "w", encoding="utf-8") as f:
        f.write(diff_details)

    print("✅ Test diff files created")
    print("  - diff_summary.txt")
    print("  - diff_details.txt")


if __name__ == "__main__":
    create_test_diff()
