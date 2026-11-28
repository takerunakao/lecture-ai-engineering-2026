#!/usr/bin/env python3
"""Day4の提出ファイルを配置する。ネットワークやモデルAPIは使用しない。"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import urlsplit

PACKAGE = {'files': {'lectures/04/answer.md': '# 第4回 解答\n'
                                    '\n'
                                    '## 演習\n'
                                    '\n'
                                    '本提出では、発展課題の調査結果を以下の「宿題」欄に記載する。演習のラベル付け・LLM採点の実測結果は、本レポートの対象に含めない。\n'
                                    '\n'
                                    '## 宿題\n'
                                    '\n'
                                    '### 1. 取り組んだ内容と調査対象\n'
                                    '\n'
                                    '- **取り組んだレベル：発展。**\n'
                                    '- **対象：SWE-bench '
                                    'Verified**（`princeton-nlp/SWE-bench_Verified`、`default/test`、500件）。[S1]\n'
                                    '- **調査日：2026年11月10日（日本時間）。**\n'
                                    '- **やったこと：** '
                                    '実問題5件の内容と難しさを整理し、作成者・検証者・品質確認の手順・採点方法を一次資料で調べ、講座の評価セットと比較した。公開注釈データの件数も照合した。\n'
                                    '- **結果：** '
                                    '問題の品質を検証する人の役割と、モデルの出力を採点する方法を分けて比較できた。品質による除外と、その後の500件への選定も区別した。\n'
                                    '- **実施範囲：** '
                                    '調査レポート。モデルAPIの呼び出し、修正パッチの作成、ベンチマークのテスト実行、モデルの解決率の測定は行っていない。\n'
                                    '\n'
                                    '課題は、ベンチマークの問題を3〜5件読み、人数・作成と検証の手順・採点法を調査するものである。問題全文は転載せず、以下では要約を記す。[S0]\n'
                                    '\n'
                                    '選んだ理由は、数値計算・機械学習・可視化などの既存ライブラリで、問題の解決と既存機能の維持を両立する課題を読めるためである。Day3で取り組んだエージェントの評価を、「回答が返ったか」から「成功を何で確かめるか」へ進めて考える題材にした。\n'
                                    '\n'
                                    '### 2. データの確認範囲と5件の選び方\n'
                                    '\n'
                                    '公式Dataset '
                                    'ViewerのAPIから500件の行を取得し、IDが500種類あることと、以下の5件が含まれることを確認した。要約は各行の`problem_statement`と元のIssueを根拠にした。データセットのリポジトリSHAは、取得前後とも`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`だった。行取得API自体は版を固定しないため、このSHAは取得時に確認した版として記録する。[S1]\n'
                                    '\n'
                                    '5件は、科学計算に近い4プロジェクトと、Webフレームワーク1件を選んだ**目的抽出**である。無作為標本ではなく、この5件から全体の難易度分布やモデル性能は推定しない。問題ID、元IssueとPRのURL、問題文のハッシュ、参照データの情報は[research_manifest.json](research_manifest.json)に記録した。\n'
                                    '\n'
                                    '#### 2-1. Astropy：入れ子にしたモデルの依存関係\n'
                                    '\n'
                                    '**問題ID：`astropy__astropy-12907`**／[元Issue '
                                    '#12906](https://github.com/astropy/astropy/issues/12906)／[対応PR '
                                    '#12907](https://github.com/astropy/astropy/pull/12907)\n'
                                    '\n'
                                    '- **何を問うか：** '
                                    '複数のモデルを合成した際、一部を入れ子の`CompoundModel`にまとめると、`separability_matrix`が独立な入力・出力を相互依存と判定してしまう。同じ計算のまとまり方が変わっても、入力と出力の依存関係を正しく求める課題である。\n'
                                    '- **自分なら解けるかの見立て：** '
                                    '小さい例の依存関係を図や行列にして追うところから取り組めそうだ。ただし、修正を完了できるかは未判定で、Astropyのモデル合成と再帰処理を読む必要がある。実装・実行による確認はしていない。\n'
                                    '- **LLMにとっての難しさという考察：** '
                                    '例示された行列だけを正しくする変更では不十分である。平坦な合成と入れ子の合成で依存関係が一致するという性質を、異なる組合せでも維持する必要がある。\n'
                                    '\n'
                                    '#### 2-2. SymPy：次元の異なる点の距離\n'
                                    '\n'
                                    '**問題ID：`sympy__sympy-11618`**／[元Issue '
                                    '#11617](https://github.com/sympy/sympy/issues/11617)／[対応PR '
                                    '#11618](https://github.com/sympy/sympy/pull/11618)\n'
                                    '\n'
                                    '- **何を問うか：** '
                                    '2次元点と3次元点の距離を計算すると、第3座標が無視されてしまう。異なる次元の点について、座標の扱いをそろえた正しい距離を返す課題である。\n'
                                    '- **自分なら解けるかの見立て：** '
                                    '距離の数式と期待値の理解からは取り組みやすそうだ。一方、ライブラリとしての修正には、足りない座標の規約、引数の順序、記号式を含む場合の確認が必要であり、修正完了の可否は未判定である。\n'
                                    '- **LLMにとっての難しさという考察：** '
                                    '数式の知識を持つことに加え、長さが違う系列の処理で座標が落ちる原因をコード上で見つける必要がある。例の数値だけを合わせず、次元や引数を変えても一貫する処理が求められる。\n'
                                    '\n'
                                    '#### 2-3. scikit-learn：推定器のクラスを持つモデルの複製\n'
                                    '\n'
                                    '**問題ID：`scikit-learn__scikit-learn-12585`**／[元Issue '
                                    '#12521](https://github.com/scikit-learn/scikit-learn/issues/12521)／[対応PR '
                                    '#12585](https://github.com/scikit-learn/scikit-learn/pull/12585)\n'
                                    '\n'
                                    '- **何を問うか：** '
                                    'パラメータに推定器のインスタンスではなくクラスそのものを持つ場合、`clone`が`get_params`を呼んで`self`不足の例外になる。クラスをパラメータに持つラッパーも適切に複製できることが期待される。\n'
                                    '- **自分なら解けるかの見立て：** '
                                    'クラスとインスタンスの違い、メソッドの呼び出し方から原因候補を考えることはできそうだ。例外を止めるだけで正しい修正と判断せず、`clone`の契約と通常の推定器への影響を確認したい。実装による可否判定はしていない。\n'
                                    '- **LLMにとっての難しさという考察：** '
                                    '`get_params`という属性の有無だけで対象を分類できない点がある。通常の推定器、クラス、ネストしたパラメータの扱いを両立させる必要がある。\n'
                                    '\n'
                                    '#### 2-4. Matplotlib：`hexbin`の表示閾値の不一致\n'
                                    '\n'
                                    '**問題ID：`matplotlib__matplotlib-26113`**／[元Issue '
                                    '#12926](https://github.com/matplotlib/matplotlib/issues/12926)／[対応PR '
                                    '#26113](https://github.com/matplotlib/matplotlib/pull/26113)\n'
                                    '\n'
                                    '- **何を問うか：** '
                                    '`hexbin`で`mincnt=1`を指定しても、集計値`C`を渡すと1点だけのビンが表示されない。`C`の有無で閾値の意味が変わるため、境界条件を一貫させる課題である。\n'
                                    '- **自分なら解けるかの見立て：** '
                                    '閾値の比較という観点では着手しやすそうだ。ただし、空ビン、集計関数、既定値の挙動まで含むと確認範囲が広い。完全な修正ができるとはまだ判断せず、境界条件を表にしてから調べたい。描画や修正の実行はしていない。\n'
                                    '- **LLMにとっての難しさという考察：** '
                                    '見た目の違いを、引数に応じた処理分岐と比較条件へ結び付ける必要がある。境界だけ直しても、空のデータへ集計関数を適用する場合などに別の問題を生む可能性がある。\n'
                                    '\n'
                                    '#### 2-5. Django：入れ子クラスを参照するマイグレーション\n'
                                    '\n'
                                    '**問題ID：`django__django-12125`**／[元Ticket '
                                    '#27914](https://code.djangoproject.com/ticket/27914)／[対応PR '
                                    '#12125](https://github.com/django/django/pull/12125)\n'
                                    '\n'
                                    '- **何を問うか：** '
                                    'クラスの内部で定義した型をフィールド等に使うと、`makemigrations`が外側のクラス名を落とした参照パスを出力する。生成したマイグレーションから正しい型を参照できるようにする課題である。\n'
                                    '- **自分なら解けるかの見立て：** '
                                    'パスの誤りは理解できるが、Djangoの内部を初見で修正し切るのは難しそうだ。完全修飾名とシリアライザの選択を調べ、生成側と復元側を追う必要がある。実際に修正・実行した結果ではない。\n'
                                    '- **LLMにとっての難しさという考察：** '
                                    '元のモデル定義だけでなく、生成された別ファイルでも参照が成立するかを追う必要がある。扱う型によって処理が分かれるため、1つの例への修正を全体の解決と早合点しやすい。\n'
                                    '\n'
                                    '以上の「解けるか」と「LLMにとっての難しさ」は、問題文に基づく見立てであり、実測した解決率ではない。共通して、症状を理解すること、原因箇所を特定すること、既存機能を壊さず修正を完了することの間に段階があると考えた。\n'
                                    '\n'
                                    '### 3. 誰が、どう作り、どう検証したか\n'
                                    '\n'
                                    '#### 3-1. 元の問題とデータセットの作成\n'
                                    '\n'
                                    '元のSWE-benchは、12のPythonリポジトリにある実際のIssueと解決PRから構築された。約9万件のPRを収集し、Issueを解決するマージ済みPR、テストの変更、実行可能性、修正前後で失敗から成功へ変わるテストの存在などで絞り込み、2,294件のテスト集合を作った。[S2]\n'
                                    '\n'
                                    '問題の元になった報告や修正は、OSSの利用者・開発者によるものである。**元Issueの投稿者・解決PRの作成者の総人数は、確認した一次資料では集計値を確認できなかった。** '
                                    '以下の93人は、Verified化の品質検証に参加した人数として扱う。\n'
                                    '\n'
                                    '#### 3-2. Verified化の人手検証\n'
                                    '\n'
                                    'OpenAIとSWE-benchの研究者が協力し、Python経験のあるソフトウェア開発者93人で、元集合から無作為に抽出した1,699件を検証した。参加者は50件の事前ラベルを用いた導入試験を経て、各問題を異なる3人が確認した。問題文の明確さとテストの妥当性を深刻度0〜3で評価し、品質判定には3人のうち最大の深刻度を使う。2以上の判定や他の重大な問題がある項目を除外する。残ったものから時間を要する問題を優先的に含め、残りを無作為抽出して500件を選んだ。[S3]\n'
                                    '\n'
                                    'この手順は、良い問題まで落とす可能性を受け入れて、曖昧な問題の混入を抑える設計と読める。全員が同意した割合や、人間の解決率を表す人数ではない。注釈の指示書も、問題文だけで成功条件が理解できるか、テストが仕様に書かれていない実装上の細部を要求していないかを確認させている。[S4]\n'
                                    '\n'
                                    '#### 3-3. 公開注釈を照合して分かった除外件数\n'
                                    '\n'
                                    '公式記事に添付された注釈ZIPを読み、`ensembled_annotations_public.csv`の`filter_out`を集計した。原注釈CSVでも1,699件×3人＝5,097行、検証者ID93種類、全問題に異なる3人の記録があることを確認した。以下の件数は、記事の割合からの逆算ではなく、**公開CSVの再集計結果**である。[S5]\n'
                                    '\n'
                                    '| 段階 | 件数 | 意味 |\n'
                                    '|---|---:|---|\n'
                                    '| 人手検証の対象 | 1,699 | 注釈CSVの問題ID数 |\n'
                                    '| 品質による除外 | 1,160 | `filter_out=True` |\n'
                                    '| 品質フィルタを通過 | 539 | `filter_out=False` |\n'
                                    '| Verifiedに最終採用 | 500 | 公式データセットの問題ID数 |\n'
                                    '| 通過後、最終集合に入らなかった項目 | 39 | 539件と500件のID集合の差 |\n'
                                    '\n'
                                    '除外率は1,160÷1,699＝約68.3%となる。公式データセット500件のIDがすべて品質フィルタを通過した539件に含まれることも照合した。**不適切として除外した1,160件と、通過後の選定で採用されなかった39件は、別の理由によるものとして記録する。**[S1]・[S5]\n'
                                    '\n'
                                    '再確認に使ったZIP・CSVのSHA-256、取得時のデータセット版、集計条件を[research_manifest.json](research_manifest.json)に残した。分類別の問題は重複し得るため、分類ごとの件数を足して除外総数にしていない。\n'
                                    '\n'
                                    '### 4. 採点方法と、採点が保証する範囲\n'
                                    '\n'
                                    'モデルにはIssueの問題文と修正前のコードベースを与え、コード差分を生成させる。採点では差分を適用し、Docker環境で対象リポジトリのテストを実行する。[S2]・[S6]\n'
                                    '\n'
                                    '| テスト | 確認すること |\n'
                                    '|---|---|\n'
                                    '| `FAIL_TO_PASS` | 修正前に失敗していた、問題解決に関係するテストが成功するか |\n'
                                    '| `PASS_TO_PASS` | もともと成功していたテストが引き続き成功するか |\n'
                                    '\n'
                                    '公式harnessの`get_resolution_status`では、両グループの成功率がともに1のときに完全解決とする。集計指標は、評価対象のうち解決した問題の割合である。正解パッチと同じ文字列を書く必要はなく、所定のテストが判定の基準になる。[S2]・[S7]\n'
                                    '\n'
                                    'ここでの成功は、**指定されたテストの範囲での成功**である。可読性、保守性、すべての入力に対する正しさ、未知の利用者の要望まで保証されるわけではないと考える。実行環境の不備による失敗と、修正内容の不備による失敗も区別してログを見る必要がある。コードで採点すれば判定処理は機械化できるが、そのテストが適切な成功条件を表しているかの検証は残る。\n'
                                    '\n'
                                    '### 5. 講座の評価セットとの比較\n'
                                    '\n'
                                    '講座側は、配布された課題説明と採点基準に記載された設計を比較対象にした。以下は自分のLLM採点結果を測定した表ではない。[S0]・[S9]\n'
                                    '\n'
                                    '| 比較軸 | 講座の評価セット | SWE-bench Verified |\n'
                                    '|---|---|---|\n'
                                    '| 主な目的 | 学習支援エージェントの回答を採点するLLMについて、人との一致と判断できない項目を確かめる | '
                                    '既存リポジトリのIssueを解決するコード修正能力を測る |\n'
                                    '| 規模 | 10件 | 500件。本調査で内容を読んだのは5件 |\n'
                                    '| 問題・参照の由来 | 講師1人が準備した質問・回答。用語集・期待するふるまいを参照し、意図的な失敗も含む | '
                                    'OSSのIssueと解決PRに由来する問題文・コード・テスト |\n'
                                    '| 検証の体制 | 受講者のラベルとLLMの判定を比べ、講師の参考ラベルとも比較する。参考ラベルとの相違も検討対象 | '
                                    '93人の検証者が各問題を3人で確認し、問題文とテストの品質で選別 |\n'
                                    '| 採点の分担 | LLMが根拠・範囲・ヒント・分かりやすさの4基準、コードが回の表示を判定。人の判定と照合 | '
                                    '対象コードへ変更を適用し、解決用・回帰確認用のテストで判定 |\n'
                                    '| 判定と集計 | `pass/fail/unsure`。一致率、要確認件数、coverageを見る。分かりやすさは総合合否の対象外 | '
                                    '所定のテスト条件を満たした問題の解決率 |\n'
                                    '| 曖昧さへの対応 | 判断がつかない項目を人手に回し、基準に方針を明記する | '
                                    '事前の品質検証で、仕様やテストに重大な問題がある項目を除外する |\n'
                                    '\n'
                                    '表の講座側は[S0]・[S9]、SWE-bench側は[S1]〜[S7]を根拠とする。\n'
                                    '\n'
                                    '**比較からの考察：** '
                                    '両者とも、モデルを測る前に「何をもって成功とするか」を定める必要がある。ただし、講座は採点者の判断を人と照合する学習の場であり、SWE-benchはテストに基づいてコード修正を測る。件数の多さだけで、一方の評価方法が他方の用途にも優れているとは判断できない。\n'
                                    '\n'
                                    '講座の一致率では`unsure`が分母から外れるため、一致率とcoverageを合わせて読む必要がある。[S0] '
                                    '自動判定しやすい例だけを残せば高い一致率になり得るのと同様、ベンチマークでも選別後の問題の分布を意識する必要があると考えた。\n'
                                    '\n'
                                    '### 6. 追加調査：Verifiedにも残る評価の限界\n'
                                    '\n'
                                    'OpenAIは2026年2月23日の公式報告で、テスト設計の問題と学習時の混入を理由にSWE-bench '
                                    'Verifiedのスコア報告を停止したと説明している。その再監査では、OpenAI '
                                    'o3が64回の独立試行で安定して解けなかった138件を選び、各件を少なくとも6人が確認した。監査対象の59.4%に、テストまたは問題文の重大な問題があったと報告している。[S8]\n'
                                    '\n'
                                    '**この59.4%の分母は、失敗しやすかった138件である。500件から無作為に選んだ標本ではないため、500件全体の不備率としては扱わない。** '
                                    'また、2024年のデータ選別と2026年の再監査は、対象と目的が異なるので、68.3%と59.4%を同じ率として比較しない。\n'
                                    '\n'
                                    'この事例から、検証済みという名称が恒久的な品質保証になるわけではなく、モデル能力の変化や訓練データへの混入も含め、評価手段を見直し続ける必要があると考えた。テストを通らない理由が、モデルの能力不足なのか、問題文にない条件を採点側が要求しているためなのかを分けて調べることが重要である。\n'
                                    '\n'
                                    '### 7. 気づき・疑問と、自分の評価設計への接続\n'
                                    '\n'
                                    '**気づき1：確認する対象を分ける。** '
                                    'Day3では、8件の実行が完了していても、用語集検索の省略や根拠のない補足があることを記録した。[S10] '
                                    '今回も、処理の完了、テストへの合格、利用目的に沿う品質をそれぞれ確認する必要があると考えた。\n'
                                    '\n'
                                    '**気づき2：人の人数だけで品質を説明しない。** '
                                    '何人が見たかに加え、何を見たか、意見が割れたときの扱い、除外によって残る問題がどう変わるかまで必要である。今回、作問者と検証者、品質除外と最終選定を分けたことで、500件に至る理由を説明しやすくなった。\n'
                                    '\n'
                                    '**気づき3：採点基準の改善にも、別の確認用データが必要になる。** '
                                    '同じ10件を見ながら基準を調整すると、その10件に合わせ過ぎる可能性がある。今後自分のエージェントを評価するなら、基準の調整用と、調整後の確認用の質問を分け、合否だけでなく根拠の一致・要確認・見逃しを記録したい。これは今回の調査から得た設計案であり、追加実験の結果ではない。\n'
                                    '\n'
                                    '**残った疑問：** '
                                    '複数の妥当な修正がある問題で、正解PR固有の実装に寄ったテストをどこまで減らせるか。自動判定できる割合を保ちながら、採点器の疑わしい判定を人へ返す仕組みをどう設計するか。完全に自動化する範囲と、人の判断を残す範囲を分けて検討したい。\n'
                                    '\n'
                                    '### 8. AI支援と記録の扱い\n'
                                    '\n'
                                    '一次資料の探索、問題の要約、公開注釈の集計、比較と文章の整理にAI支援を用いた。原典に記載された事実、公開データから再集計した数、問題文からの見立てを区別している。各問題の「解けるか」は実装未試行の見通しであり、修正に成功した実績としては扱っていない。講義PDF・問題全文・正解パッチの再配布は行わず、要約と出典、照合用の識別情報を残した。\n'
                                    '\n'
                                    '### 9. 参照資料\n'
                                    '\n'
                                    '調査日：2026年11月10日。個別問題の元Issue・PRは第2節に記載した。\n'
                                    '\n'
                                    '- [S0] 講座公式リポジトリ「第4回 '
                                    '演習・宿題」。確認した版：`bc41dfac203acff0706b7da10d09339d91830bfe`。添付の宿題資料p.3〜4、演習講義資料p.8・11〜12・21〜22とも照合。\n'
                                    '- [S1] Princeton NLP, SWE-bench Verified dataset / Dataset Viewer '
                                    'API。`default/test`、参照時のリポジトリ版：`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`。\n'
                                    '- [S2] Jimenez et al., *SWE-bench: Can Language Models Resolve '
                                    'Real-World GitHub Issues?*, arXiv:2310.06770v3, §2.1–2.2。\n'
                                    '- [S3] OpenAI, *Introducing SWE-bench Verified*, '
                                    '2024-08-13、ページの更新表記2025-02-24。Our Approach / Dataset construction。\n'
                                    '- [S4] OpenAI, *SWE-bench Annotation Instructions*, 問題文とテストに関する基準。\n'
                                    '- [S5] OpenAI, *SWE-bench annotation '
                                    'results*。公開ZIP内の集約CSVと原注釈CSV。第3節の除外件数と注釈件数は再集計。\n'
                                    '- [S6] SWE-bench公式ドキュメント、Evaluation Guide。\n'
                                    '- [S7] SWE-bench公式harness API、`get_resolution_status`。\n'
                                    '- [S8] OpenAI, *Why SWE-bench Verified no longer measures frontier '
                                    'coding capabilities*, 2026-02-23。\n'
                                    '- [S9] 講座公式リポジトリ、`data/eval/rubric.md`。S0と同じ版。\n'
                                    '- [S10] 自分のDay3提出レポート。実行記録と考察の確認済み版。\n'
                                    '\n'
                                    '[S0]: '
                                    'https://github.com/matsuolab/lecture-ai-engineering-2026/blob/bc41dfac203acff0706b7da10d09339d91830bfe/lectures/04/problem.md\n'
                                    '[S1]: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified\n'
                                    '[S2]: https://arxiv.org/html/2310.06770v3\n'
                                    '[S3]: https://openai.com/index/introducing-swe-bench-verified/\n'
                                    '[S4]: '
                                    'https://cdn.openai.com/introducing-swe-bench-verified/swe-b-annotation-instructions.pdf\n'
                                    '[S5]: '
                                    'https://cdn.openai.com/introducing-swe-bench-verified/swe-bench-annotation-results.zip\n'
                                    '[S6]: https://www.swebench.com/SWE-bench/guides/evaluation/\n'
                                    '[S7]: '
                                    'https://www.swebench.com/SWE-bench/api/harness/#swebench.harness.grading.get_resolution_status\n'
                                    '[S8]: '
                                    'https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/\n'
                                    '[S9]: '
                                    'https://github.com/matsuolab/lecture-ai-engineering-2026/blob/bc41dfac203acff0706b7da10d09339d91830bfe/data/eval/rubric.md\n'
                                    '[S10]: '
                                    'https://github.com/takerunakao/lecture-ai-engineering-2026/blob/3f25c1f65c90d073ab6b58f206e738e997b42624/lectures/03/answer.md\n',
           'lectures/04/PR_BODY.md': '## 目的\n'
                                     '\n'
                                     'Day4の発展課題として、SWE-bench '
                                     'Verifiedの実問題と作成・検証・採点方法を調べ、講座の10件の評価セットとの違いを整理します。\n'
                                     '\n'
                                     '## 提出内容\n'
                                     '\n'
                                     '- 公式データセットに含まれる5件を選び、問題の要約、解けるかの見立て、LLMにとっての難しさを記載しました。\n'
                                     '- 元のIssue・PRの作成者と、Verifiedの品質検証を担当した93人を区別しました。\n'
                                     '- 公開注釈を照合し、1,699件中1,160件の品質除外と、通過した539件から500件への選定を分けて記録しました。\n'
                                     '- 講座の評価セットと、規模・検証体制・テスト採点とLLM採点の役割を比較しました。\n'
                                     '- 2026年の再監査について、138件の選択集合の結果を全500件へ一般化しないことを明記しました。\n'
                                     '- 出典・問題ID・参照したデータ版・照合用ハッシュを保存しました。\n'
                                     '\n'
                                     '## 実施範囲\n'
                                     '\n'
                                     '調査と考察にAI支援を利用しています。各問題の修正パッチ作成、ベンチマークのテスト実行、モデルの解決率測定は行っていません。問題文は全文転載せず要約しています。\n'
                                     '\n'
                                     '提出レポート：`lectures/04/answer.md`\n'
                                     '調査記録：`lectures/04/research_manifest.json`\n'
                                     'Quri用の回答：`lectures/04/quri_answers.md`\n',
           'lectures/04/quri_answers.md': '# Day4 Quri入力用\n'
                                          '\n'
                                          '## Q1\n'
                                          '\n'
                                          '発展｜Advanced\n'
                                          '\n'
                                          '## Q2\n'
                                          '\n'
                                          'https://github.com/takerunakao/lecture-ai-engineering-2026\n'
                                          '\n'
                                          '## Q3（237文字）\n'
                                          '\n'
                                          'SWE-bench '
                                          'Verifiedの実問題5件を調べ、内容・必要知識・解決の難しさを整理しました。作問者と93人の検証者を区別し、公開注釈から1,699件中1,160件の除外、残る539件から500件の選定を確認しました。講座の10件と、検証体制やテスト採点・LLM採点の役割を比較しています。2026年の再監査も参照し、138件の監査結果を全500件へ一般化しない点と、採点器自体の妥当性を重視しました。AI支援を用い、出典・問題ID・参照したデータ版を記録しています。\n'
                                          '\n'
                                          '## 提出前の確認\n'
                                          '\n'
                                          'answer.mdの5件の問題要約と出典を読み、各問の「自分なら解けるかの見立て」が自身の判断と合うことを確認してから提出する。異なる見立ては自身の言葉に直す。本課題は調査レポートであり、問題の修正実装やモデルAPIの実行結果は含めていない。\n',
           'lectures/04/research_manifest.json': '{\n'
                                                 '  "schema_version": 1,\n'
                                                 '  "research_date_jst": "2026-11-10",\n'
                                                 '  "assignment_level": "Advanced",\n'
                                                 '  "assignment_kind": "benchmark research report",\n'
                                                 '  "model_api_executed": false,\n'
                                                 '  "benchmark_solution_implemented": false,\n'
                                                 '  "benchmark_tests_executed": false,\n'
                                                 '  "ai_assistance": [\n'
                                                 '    "source discovery",\n'
                                                 '    "problem summarization",\n'
                                                 '    "public annotation aggregation",\n'
                                                 '    "analysis and writing"\n'
                                                 '  ],\n'
                                                 '  "course_reference": {\n'
                                                 '    "repository": '
                                                 '"matsuolab/lecture-ai-engineering-2026",\n'
                                                 '    "commit": "bc41dfac203acff0706b7da10d09339d91830bfe",\n'
                                                 '    "problem_path": "lectures/04/problem.md",\n'
                                                 '    "rubric_path": "data/eval/rubric.md"\n'
                                                 '  },\n'
                                                 '  "dataset": {\n'
                                                 '    "name": "princeton-nlp/SWE-bench_Verified",\n'
                                                 '    "url": '
                                                 '"https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified",\n'
                                                 '    "config": "default",\n'
                                                 '    "split": "test",\n'
                                                 '    "metadata_revision_before": '
                                                 '"c104f840cc67f8b6eec6f759ebc8b2693d585d4a",\n'
                                                 '    "metadata_revision_after": '
                                                 '"c104f840cc67f8b6eec6f759ebc8b2693d585d4a",\n'
                                                 '    "unique_rows_read": 500,\n'
                                                 '    "gated": false,\n'
                                                 '    "retrieval_method": "Official Dataset Viewer rows API, '
                                                 '5 pages of 100 rows. The API was not revision-pinned; '
                                                 'metadata revisions before and after were checked to '
                                                 'match.",\n'
                                                 '    "source_metadata_url": '
                                                 '"https://huggingface.co/api/datasets/princeton-nlp/SWE-bench_Verified"\n'
                                                 '  },\n'
                                                 '  "selected_problem_count": 5,\n'
                                                 '  "selection_method": "Purposive selection of four '
                                                 'scientific-computing projects and one web framework; no '
                                                 'claim of representativeness or measured solving '
                                                 'performance.",\n'
                                                 '  "selected_problems": [\n'
                                                 '    {\n'
                                                 '      "instance_id": "astropy__astropy-12907",\n'
                                                 '      "repo": "astropy/astropy",\n'
                                                 '      "canonical_row_index": 0,\n'
                                                 '      "canonical_base_commit": '
                                                 '"d16bfe05a744909de4b27f5875fe0d4ed41ce607",\n'
                                                 '      "problem_statement_sha256": '
                                                 '"c01334ec1b21a089c650cf2e7b96ab974469076bf1260d23885799e1f0a7551f",\n'
                                                 '      "problem_statement_chars": 1246,\n'
                                                 '      "issue_url": '
                                                 '"https://github.com/astropy/astropy/issues/12906",\n'
                                                 '      "pr_url": '
                                                 '"https://github.com/astropy/astropy/pull/12907"\n'
                                                 '    },\n'
                                                 '    {\n'
                                                 '      "instance_id": "sympy__sympy-11618",\n'
                                                 '      "repo": "sympy/sympy",\n'
                                                 '      "canonical_row_index": 425,\n'
                                                 '      "canonical_base_commit": '
                                                 '"360290c4c401e386db60723ddb0109ed499c9f6e",\n'
                                                 '      "problem_statement_sha256": '
                                                 '"7eec6e997311bf1014a07659710714c0a891fd0e5b9d58dadb31a83b23746330",\n'
                                                 '      "problem_statement_chars": 252,\n'
                                                 '      "issue_url": '
                                                 '"https://github.com/sympy/sympy/issues/11617",\n'
                                                 '      "pr_url": '
                                                 '"https://github.com/sympy/sympy/pull/11618"\n'
                                                 '    },\n'
                                                 '    {\n'
                                                 '      "instance_id": "scikit-learn__scikit-learn-12585",\n'
                                                 '      "repo": "scikit-learn/scikit-learn",\n'
                                                 '      "canonical_row_index": 354,\n'
                                                 '      "canonical_base_commit": '
                                                 '"bfc4a566423e036fbdc9fb02765fd893e4860c85",\n'
                                                 '      "problem_statement_sha256": '
                                                 '"0bd52ce53c9612da5326a0742940720ef9520cb2c0f8893e2e49f1513706b4a6",\n'
                                                 '      "problem_statement_chars": 1422,\n'
                                                 '      "issue_url": '
                                                 '"https://github.com/scikit-learn/scikit-learn/issues/12521",\n'
                                                 '      "pr_url": '
                                                 '"https://github.com/scikit-learn/scikit-learn/pull/12585"\n'
                                                 '    },\n'
                                                 '    {\n'
                                                 '      "instance_id": "matplotlib__matplotlib-26113",\n'
                                                 '      "repo": "matplotlib/matplotlib",\n'
                                                 '      "canonical_row_index": 282,\n'
                                                 '      "canonical_base_commit": '
                                                 '"5ca694b38d861c0e24cd8743753427dda839b90b",\n'
                                                 '      "problem_statement_sha256": '
                                                 '"dd3266ec4a7c3e8cc3d0b7ccb0bd76d85b33814bedadceb4277d755db08479ca",\n'
                                                 '      "problem_statement_chars": 9424,\n'
                                                 '      "issue_url": '
                                                 '"https://github.com/matplotlib/matplotlib/issues/12926",\n'
                                                 '      "pr_url": '
                                                 '"https://github.com/matplotlib/matplotlib/pull/26113"\n'
                                                 '    },\n'
                                                 '    {\n'
                                                 '      "instance_id": "django__django-12125",\n'
                                                 '      "repo": "django/django",\n'
                                                 '      "canonical_row_index": 71,\n'
                                                 '      "canonical_base_commit": '
                                                 '"89d41cba392b759732ba9f1db4ff29ed47da6a56",\n'
                                                 '      "problem_statement_sha256": '
                                                 '"d466ceb9860bfb421821c9bab47b1fa2c11295523365b174ea0b2a5a3b125a65",\n'
                                                 '      "problem_statement_chars": 1589,\n'
                                                 '      "issue_url": '
                                                 '"https://code.djangoproject.com/ticket/27914",\n'
                                                 '      "pr_url": '
                                                 '"https://github.com/django/django/pull/12125"\n'
                                                 '    }\n'
                                                 '  ],\n'
                                                 '  "annotation_audit": {\n'
                                                 '    "source_url": '
                                                 '"https://cdn.openai.com/introducing-swe-bench-verified/swe-bench-annotation-results.zip",\n'
                                                 '    "zip_sha256": '
                                                 '"b9297c31f6c2ef712218b5bb2830bd47a7f600dedf6b927191d0170177266ab9",\n'
                                                 '    "ensemble_csv_filename": '
                                                 '"ensembled_annotations_public.csv",\n'
                                                 '    "ensemble_csv_sha256": '
                                                 '"d2743650f6b2d31eeaf6d9952c3766b022930964d9d9452fc35cfbeb1967827c",\n'
                                                 '    "reviewed_instances": 1699,\n'
                                                 '    "filter_out_true": 1160,\n'
                                                 '    "filter_out_false": 539,\n'
                                                 '    "excluded_rate_unrounded": 0.6827545615067687,\n'
                                                 '    "final_verified_instances": 500,\n'
                                                 '    "all_verified_ids_within_passed_filter_ids": true,\n'
                                                 '    "passed_but_not_selected": 39,\n'
                                                 '    "raw_annotation_rows": 5097,\n'
                                                 '    "distinct_annotator_ids": 93,\n'
                                                 '    "every_instance_has_three_distinct_annotators": true,\n'
                                                 '    "filter_rule": "underspecified >= 2 OR false_negative '
                                                 '>= 2 OR other_major_issues == 1",\n'
                                                 '    "filter_rule_agrees_with_filter_out_all_rows": true,\n'
                                                 '    "aggregation_note": "Counts were recomputed from '
                                                 'published CSVs. The 39 passed-but-not-selected instances '
                                                 'are not counted as rejected for quality."\n'
                                                 '  },\n'
                                                 '  "later_audit_context": {\n'
                                                 '    "source_url": '
                                                 '"https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/",\n'
                                                 '    "publication_date": "2026-02-23",\n'
                                                 '    "audited_instances": 138,\n'
                                                 '    "reported_material_issue_percentage": 59.4,\n'
                                                 '    "selection_condition": "Tasks that OpenAI o3 did not '
                                                 'consistently solve over 64 independent runs.",\n'
                                                 '    "reviewers_per_case_minimum": 6,\n'
                                                 '    "generalization_note": "The 138 instances form a '
                                                 'selected failure-prone subset; 59.4% is not an estimate of '
                                                 'the defect rate for all 500 instances."\n'
                                                 '  },\n'
                                                 '  "self_assessment_scope": "Tentative difficulty '
                                                 'assessments based on reading the problem statements; no '
                                                 'assertion of personally implemented or successful fixes."\n'
                                                 '}\n'},
 'upstream_homework_template': '## 宿題\n\n- 取り組んだレベル：基礎 / 実装 / 発展\n- やったこと：\n- 結果：\n- 気づき・疑問：\n',
 'q3': 'SWE-bench '
       'Verifiedの実問題5件を調べ、内容・必要知識・解決の難しさを整理しました。作問者と93人の検証者を区別し、公開注釈から1,699件中1,160件の除外、残る539件から500件の選定を確認しました。講座の10件と、検証体制やテスト採点・LLM採点の役割を比較しています。2026年の再監査も参照し、138件の監査結果を全500件へ一般化しない点と、採点器自体の妥当性を重視しました。AI支援を用い、出典・問題ID・参照したデータ版を記録しています。',
 'pr_title': 'Day4 発展：SWE-bench Verifiedの調査と講座評価セットの比較'}
PACKAGE["homework_text"] = "## 宿題\n" + PACKAGE["files"]["lectures/04/answer.md"].split("## 宿題\n", 1)[1]



TARGETS = (
    "lectures/04/answer.md",
    "lectures/04/PR_BODY.md",
    "lectures/04/quri_answers.md",
    "lectures/04/research_manifest.json",
)
HOMEWORK_HEADING = re.compile(rb"(?m)^## \xe5\xae\xbf\xe9\xa1\x8c(?:\r?\n|$)")
EXPECTED_REPOSITORY = "takerunakao/lecture-ai-engineering-2026"


def git_read(root: Path, *arguments: str) -> str:
    """Gitの読み取り専用コマンドを実行し、リモートURL等は画面に出さない。"""
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError("Gitが見つかりません。講座のCodespacesで実行してください。") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Gitの状態確認が時間内に終わりませんでした。") from exc
    if result.returncode != 0:
        raise ValueError("Gitの状態を確認できません。講座リポジトリのルートで実行してください。")
    return result.stdout.strip()


def is_expected_origin(url: str) -> bool:
    """HTTPS、SSH URL、git@github.com:...形式を受け付ける。"""
    if url.startswith("git@github.com:"):
        repository = url.removeprefix("git@github.com:")
    else:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https", "ssh"} or parsed.hostname != "github.com":
            return False
        if parsed.query or parsed.fragment:
            return False
        if parsed.scheme == "ssh" and parsed.username not in {None, "git"}:
            return False
        repository = parsed.path.lstrip("/")
    repository = repository.rstrip("/").removesuffix(".git")
    return repository.casefold() == EXPECTED_REPOSITORY.casefold()


def normalized_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def homework_start(data: bytes, description: str) -> re.Match[bytes]:
    matches = list(HOMEWORK_HEADING.finditer(data))
    if len(matches) != 1:
        raise ValueError(f"{description}の「## 宿題」が1か所ではありません。上書きせず停止します。")
    return matches[0]


def ensure_safe_path(root: Path, target: Path) -> None:
    """書き込み対象とその親を確認し、リンク先への書き込みを避ける。"""
    relative = target.relative_to(root)
    cursor = root
    for index, part in enumerate(relative.parts):
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("シンボリックリンクには配置できません: " + relative.as_posix())
        if cursor.exists():
            is_last = index == len(relative.parts) - 1
            if is_last and not cursor.is_file():
                raise ValueError("配置先が通常のファイルではありません: " + relative.as_posix())
            if not is_last and not cursor.is_dir():
                raise ValueError("配置先の親がフォルダではありません: " + relative.as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="配置可能か確認するだけ")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if not (root / "pyproject.toml").is_file():
        raise ValueError("pyproject.tomlがある講座リポジトリのルートで実行してください。")
    if Path(git_read(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("リポジトリ内のサブフォルダではなく、一番上の階層で実行してください。")
    if git_read(root, "branch", "--show-current") != "lec04":
        raise ValueError("作業ブランチをlec04に切り替えてから実行してください。")
    origin_urls = git_read(root, "remote", "get-url", "--all", "origin").splitlines()
    origin_urls += git_read(root, "remote", "get-url", "--push", "--all", "origin").splitlines()
    if not origin_urls or not all(is_expected_origin(url) for url in origin_urls):
        raise ValueError("originがご自身の講座リポジトリではありません。配置を停止します。")

    files = PACKAGE.get("files")
    if not isinstance(files, dict) or set(files) != set(TARGETS):
        raise ValueError("提出データのファイル一覧が正しくありません。スクリプトを取り直してください。")
    if not all(isinstance(content, str) for content in files.values()):
        raise ValueError("提出データの内容が正しくありません。")
    q3 = PACKAGE.get("q3")
    if not isinstance(q3, str) or not 1 <= len(q3) <= 400:
        raise ValueError("Q3の文章が400文字以内になっていません。")
    title = PACKAGE.get("pr_title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("PRタイトルが見つかりません。")
    homework_text = PACKAGE.get("homework_text")
    template_text = PACKAGE.get("upstream_homework_template")
    if not isinstance(homework_text, str) or not isinstance(template_text, str):
        raise ValueError("宿題欄の提出データが正しくありません。")
    homework = normalized_newlines(homework_text.encode("utf-8"))
    template = normalized_newlines(template_text.encode("utf-8"))
    if homework_start(homework, "完成した提出データ").start() != 0:
        raise ValueError("完成した宿題欄の見出しが先頭にありません。")
    if homework_start(template, "配布テンプレート").start() != 0:
        raise ValueError("配布テンプレートの宿題欄が正しくありません。")
    new_answer = files["lectures/04/answer.md"].encode("utf-8")
    new_heading = homework_start(new_answer, "新規のanswer.md")
    if normalized_newlines(new_answer[new_heading.start():]) != homework:
        raise ValueError("新規のanswer.mdと宿題欄の内容が一致しません。")

    pending: list[tuple[Path, bytes, bytes | None]] = []
    unchanged = 0
    for name in TARGETS:
        target = root / name
        ensure_safe_path(root, target)
        current = target.read_bytes() if target.exists() else None
        desired = files[name].encode("utf-8")
        if current is not None and name == "lectures/04/answer.md":
            heading = homework_start(current, "既存のanswer.md")
            existing_homework = normalized_newlines(current[heading.start():])
            if existing_homework not in (template, homework):
                raise ValueError("answer.mdの宿題欄に独自の記述があります。上書きせず停止します。")
            newline = b"\r\n" if heading.group().endswith(b"\r\n") else b"\n"
            replacement = homework.replace(b"\n", newline)
            desired = current[:heading.start()] + replacement
        elif current is not None and current != desired:
            raise ValueError("独自の変更があるため、上書きせず停止します: " + name)
        if current == desired:
            unchanged += 1
        else:
            pending.append((target, desired, current))

    print(f"配置先を確認しました。変更予定: {len(pending)}ファイル、反映済み: {unchanged}ファイル。")
    if args.check:
        print("確認のみ。ファイルの変更は行っていません。")
        return

    # 全ファイルの検査後、書き込み前に配置先と内容が変わっていないか再確認する。
    for target, _, expected_before in pending:
        ensure_safe_path(root, target)
        current = target.read_bytes() if target.exists() else None
        if current != expected_before:
            raise ValueError("確認中にファイルが変更されました。上書きせず停止します。")

    for target, desired, expected_before in pending:
        ensure_safe_path(root, target)
        mode = stat.S_IMODE(target.stat().st_mode) if expected_before is not None else 0o644
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".day4-submit-", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(desired)
            temporary.chmod(mode)
            temporary.replace(target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print("配置: " + target.relative_to(root).as_posix())

    print("Day4の提出ファイルを反映しました。モデルAPIは呼び出していません。")
    print("各問題について『自分なら解けるか』の見立てを自身で確認し、必要に応じて修正してからGitHubへ保存してください。")
    print("PRタイトル: " + title)
    print("Q3文字数: " + str(len(q3)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        raise SystemExit("提出ファイルの配置を中止しました: " + str(exc))
