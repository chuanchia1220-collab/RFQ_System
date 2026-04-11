import os
import shutil
from datetime import datetime
import logging
from typing import Dict

class FileManager:
    """
    檔案管理模組，負責建立本地枝狀歸檔目錄結構。
    """
    def __init__(self, base_path: str = "rfq_archives"):
        self.base_path = base_path
        # 確保 base_path 存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def create_rfq_tree(self, rfq_id: str, item_name: str) -> Dict[str, str]:
        """
        在指定的 base_path 下建立完整的枝狀資料夾結構：
        ├── 1_原始需求/
        ├── 2_詢價內容/
        ├── 3_廠商報價/
        └── 4_詢比議價表/

        回傳各子資料夾的絕對路徑 Dict。
        """
        try:
            # 建立基底資料夾，例如: rfq_archives/20231025_RFQ123_ItemName
            date_str = datetime.now().strftime("%Y%m%d")
            # 清理 item_name 中的非法字元 (簡單處理)
            safe_item_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            folder_name = f"{date_str}_{rfq_id}_{safe_item_name}"
            rfq_root_path = os.path.join(self.base_path, folder_name)

            # 定義需要的子資料夾
            subdirs = [
                "1_原始需求",
                "2_詢價內容",
                "3_廠商報價",
                "4_詢比議價表"
            ]

            paths_dict = {"root": os.path.abspath(rfq_root_path)}

            # 建立結構
            for subdir in subdirs:
                full_path = os.path.join(rfq_root_path, subdir)
                os.makedirs(full_path, exist_ok=True)
                # 使用簡化的 key 名稱
                key_name = subdir.split('_', 1)[1] if '_' in subdir else subdir
                paths_dict[key_name] = os.path.abspath(full_path)

            logging.info(f"Successfully created RFQ tree for {rfq_id} at {rfq_root_path}")
            return paths_dict

        except OSError as e:
            logging.error(f"Error creating RFQ tree for {rfq_id}: {e}")
            return {}

# 建立預設實例供外部直接匯入使用
file_manager = FileManager()
