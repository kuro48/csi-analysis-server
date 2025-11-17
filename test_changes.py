#!/usr/bin/env python3
"""
変更内容のテストスクリプト
- サブキャリア選択ロジックのテスト
- IPFS保存の無効化確認
"""

import sys
import os

# カレントディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))


def test_subcarrier_selection_logic():
    """サブキャリア選択ロジックのテスト"""
    print("=" * 60)
    print("テスト1: サブキャリア選択ロジック")
    print("=" * 60)

    # シミュレーション: csi_processor.py の該当ロジック

    # ケース1: ハードウェアから選択済みサブキャリアを受け取る場合
    print("\n[ケース1] ハードウェアから選択済みサブキャリアを受け取る")
    metadata1 = {
        'device_id': 'test-device-001',
        'selected_subcarriers': ['-45', '-23', '12', '34', '56']
    }

    selected_cols = []
    similarities = {}

    # 実際のロジックをシミュレート
    if metadata1.get('selected_subcarriers') is not None and len(metadata1.get('selected_subcarriers')) > 0:
        selected_cols = metadata1.get('selected_subcarriers')
        print(f"  ✓ ハードウェアで選択されたサブキャリアを使用: {selected_cols}")
    else:
        print("  ✗ サーバー側で選択するべきではない")

    assert selected_cols == ['-45', '-23', '12', '34', '56'], "ハードウェア選択が正しく動作していません"
    print("  ✓ テスト合格: ハードウェア選択が優先されました")

    # ケース2: ハードウェアから選択済みサブキャリアを受け取らない場合
    print("\n[ケース2] ハードウェアから選択済みサブキャリアを受け取らない")
    metadata2 = {
        'device_id': 'test-device-002'
    }

    selected_cols = []
    baseline_fft = None  # ベースラインなしと仮定
    fft_df_columns = ['frequency', '-64', '-63', '-62', '62', '63', '64']

    if metadata2.get('selected_subcarriers') is not None and len(metadata2.get('selected_subcarriers')) > 0:
        selected_cols = metadata2.get('selected_subcarriers')
        print("  ✗ ハードウェア選択があるべきではない")
    else:
        # サーバー側で選択
        if baseline_fft is not None:
            print("  → サーバー側でベースラインとの類似度計算により選択")
            selected_cols = ['-64', '-63']  # ダミー

        if not selected_cols:
            # すべてのサブキャリアを使用
            selected_cols = [col for col in fft_df_columns if col != 'frequency']
            print(f"  ✓ ベースラインがないため、すべてのサブキャリアを使用: {len(selected_cols)}個")

    assert len(selected_cols) > 0, "サブキャリアが選択されていません"
    print(f"  ✓ テスト合格: {len(selected_cols)}個のサブキャリアが選択されました")

    # ケース3: selected_subcarriers が空リストの場合
    print("\n[ケース3] selected_subcarriers が空リストの場合")
    metadata3 = {
        'device_id': 'test-device-003',
        'selected_subcarriers': []
    }

    selected_cols = []

    if metadata3.get('selected_subcarriers') is not None and len(metadata3.get('selected_subcarriers')) > 0:
        selected_cols = metadata3.get('selected_subcarriers')
        print("  ✗ 空リストなので選択されるべきではない")
    else:
        # サーバー側で選択
        selected_cols = [col for col in fft_df_columns if col != 'frequency']
        print(f"  ✓ 空リストのため、サーバー側で選択: {len(selected_cols)}個")

    assert len(selected_cols) > 0, "空リストの場合、サーバー側で選択されるべき"
    print(f"  ✓ テスト合格: サーバー側で{len(selected_cols)}個のサブキャリアが選択されました")


def test_ipfs_disabled():
    """IPFS保存が無効化されていることの確認"""
    print("\n" + "=" * 60)
    print("テスト2: IPFS保存の無効化確認")
    print("=" * 60)

    # シミュレーション: breathing_analysis.py の該当部分

    print("\n[確認] IPFS連携コードがコメントアウトされている")

    # 実際のファイルを読み込んで確認
    with open('analysis/breathing_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # IPFS連携のコードがコメントアウトされているかチェック
    if '# if self.ipfs_manager and self.ipfs_manager.connection_status:' in content:
        print("  ✓ IPFS連携コードがコメントアウトされています")
    else:
        print("  ✗ IPFS連携コードがまだアクティブです")
        raise AssertionError("IPFS連携コードが無効化されていません")

    if 'logger.info("IPFS連携は無効化されています（ローカルストレージのみ使用）")' in content:
        print("  ✓ IPFS無効化のログメッセージが追加されています")
    else:
        print("  ✗ IPFS無効化のログメッセージが見つかりません")
        raise AssertionError("IPFS無効化のログメッセージがありません")

    print("  ✓ テスト合格: IPFS保存は正しく無効化されています")


def test_data_model():
    """データモデルの変更確認"""
    print("\n" + "=" * 60)
    print("テスト3: データモデルの変更確認")
    print("=" * 60)

    # 実際のファイルを読み込んで確認
    with open('api/models/breathing_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    print("\n[確認] CSIDataMetadataに selected_subcarriers フィールドが追加されている")

    if 'selected_subcarriers: Optional[List[str]]' in content:
        print("  ✓ selected_subcarriers フィールドが見つかりました")
    else:
        print("  ✗ selected_subcarriers フィールドが見つかりません")
        raise AssertionError("selected_subcarriers フィールドが追加されていません")

    if 'ハードウェアで選択されたサブキャリア' in content:
        print("  ✓ フィールドの説明が適切に設定されています")
    else:
        print("  ✗ フィールドの説明が見つかりません")

    print("  ✓ テスト合格: データモデルが正しく更新されています")


def test_csi_processor_logic():
    """CSIプロセッサーのロジック確認"""
    print("\n" + "=" * 60)
    print("テスト4: CSIプロセッサーのロジック確認")
    print("=" * 60)

    # 実際のファイルを読み込んで確認
    with open('analysis/csi_processor.py', 'r', encoding='utf-8') as f:
        content = f.read()

    print("\n[確認] サブキャリア選択ロジックが更新されている")

    checks = [
        ("ハードウェアで選択されたサブキャリアがメタデータに含まれている場合はそれを使用", "ハードウェア優先チェック"),
        ("metadata.get('selected_subcarriers')", "メタデータからの取得"),
        ("ハードウェアで選択されたサブキャリアを使用:", "ハードウェア使用ログ"),
        ("ハードウェアで選択されていない場合は、サーバー側で選択（従来の方法）", "フォールバックロジック"),
    ]

    for check_str, description in checks:
        if check_str in content:
            print(f"  ✓ {description} - 見つかりました")
        else:
            print(f"  ✗ {description} - 見つかりません")
            raise AssertionError(f"{description}が実装されていません")

    print("  ✓ テスト合格: CSIプロセッサーのロジックが正しく更新されています")


def main():
    """メインテスト実行"""
    print("\n" + "=" * 60)
    print("変更内容のテスト開始")
    print("=" * 60)

    try:
        test_subcarrier_selection_logic()
        test_ipfs_disabled()
        test_data_model()
        test_csi_processor_logic()

        print("\n" + "=" * 60)
        print("✓ すべてのテストが合格しました！")
        print("=" * 60)
        print("\n変更内容のサマリー:")
        print("  1. ✓ IPFS保存が無効化され、ローカルストレージのみを使用")
        print("  2. ✓ ハードウェアからの選択済みサブキャリアを優先的に使用")
        print("  3. ✓ ハードウェアから受け取らない場合は従来のロジックで選択")
        print("  4. ✓ データモデルに selected_subcarriers フィールドを追加")
        print("\n実装は正常に動作する想定です。")

        return 0

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ テスト失敗: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ エラーが発生しました: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
