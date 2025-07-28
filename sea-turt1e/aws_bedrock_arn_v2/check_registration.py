#!/usr/bin/env python3
"""
Dify プラグイン登録確認スクリプト
"""

import requests
import json
import os

def check_plugin_registration():
    """Dify APIでプラグインの登録状況を確認"""
    
    # Dify API endpoint
    api_base = "http://localhost:5001"
    
    try:
        # プラグイン一覧の取得
        response = requests.get(f"{api_base}/console/api/plugins")
        
        if response.status_code == 200:
            plugins = response.json()
            print("📋 登録済みプラグイン:")
            print(json.dumps(plugins, indent=2, ensure_ascii=False))
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        
    try:
        # モデルプロバイダー一覧の取得
        response = requests.get(f"{api_base}/console/api/workspaces/current/model-providers")
        
        if response.status_code == 200:
            providers = response.json()
            print("\n📋 利用可能なモデルプロバイダー:")
            for provider in providers.get('data', []):
                print(f"  - {provider.get('provider_name')} ({provider.get('provider_type')})")
        else:
            print(f"❌ プロバイダー取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ プロバイダー確認エラー: {e}")

def check_plugin_daemon():
    """プラグインデーモンの状況確認"""
    
    try:
        response = requests.get("http://localhost:5003/health")
        if response.status_code == 200:
            print("✅ プラグインデーモンは正常に動作中")
        else:
            print(f"⚠️ プラグインデーモン応答異常: {response.status_code}")
    except Exception as e:
        print(f"❌ プラグインデーモン接続エラー: {e}")

if __name__ == "__main__":
    print("Dify プラグイン登録状況確認")
    print("=" * 40)
    
    check_plugin_daemon()
    print()
    check_plugin_registration()
    
    print("\n💡 トラブルシューティング:")
    print("1. プラグインが表示されない場合:")
    print("   - プラグインを一度停止 (Ctrl+C)")
    print("   - Difyを再起動: docker-compose restart")
    print("   - プラグインを再起動: python main.py")
    print("2. ブラウザのキャッシュをクリアしてページをリロード")
    print("3. Dify管理画面で Settings > Model Providers を確認")
