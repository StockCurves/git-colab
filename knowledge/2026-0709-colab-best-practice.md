# Google Colab 與 本地編輯器 (Antigravity) 協作最佳實踐 (Best Practices)

本文件整理了在本地使用 Antigravity 編輯器修改程式碼，並同時在 Google Colab 執行 `.ipynb` 時的最佳開發工作流。

---

## 1. 邏輯抽離至 `.py` 模組 + `%autoreload`（最推薦）

這是開發複雜模型或大型模擬時最常用的做法。

### 實作步驟：
1. **抽離邏輯**：將核心的演算法、數學模型與繪圖邏輯寫在獨立的 `.py` 檔案中（例如 `sscg_generator.py`）。
2. **簡化 Notebook**：在 `.ipynb` 中只保留簡單的參數設定與模組呼叫。
3. **設定自動載入**：在 Colab 的開頭儲存格中載入 `autoreload` 擴充套件：
   ```python
   %load_ext autoreload
   %autoreload 2
   import sscg_generator as sscg
   ```

### 優點：
當您在 Antigravity 中修改 `.py` 檔案並儲存後，Colab 在執行下一個儲存格時會**自動重新載入**最新代碼，不需重啟 Colab Runtime。

---

## 2. 使用 Google Drive 桌面版進行即時同步

適用於需要直接在 Colab 中存取本地專案資料夾的所有 `.ipynb` 和 `.py` 檔案。

### 實作步驟：
1. **設定雲端同步**：安裝 **Google Drive 電腦版 (Google Drive for Desktop)**，將本地專案資料夾設定為與雲端硬碟即時同步。
2. **掛載硬碟**：在 Colab 中掛載雲端硬碟：
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
3. **切換目錄**：將 Colab 的工作目錄切換到該同步資料夾：
   ```python
   %cd /content/drive/MyDrive/YourProjectFolder
   ```

### 優點：
您在 Antigravity 中修改並儲存檔案後，檔案會透過 Google Drive 自動同步到雲端，Colab 可以直接讀取並執行最新版本。

---

## 3. Git / GitHub 工作流

適合版本控制、歷史追蹤與團隊協作。

### 實作步驟：
1. **本地推送**：在 Antigravity 完成程式碼修改後，將變更 `git commit` 並 `git push` 到 GitHub。
2. **Colab 載入**：
   * **直接開啟**：可使用瀏覽器擴充套件（如 Open in Colab）或直接輸入 `https://colab.research.google.com/github/username/repo/blob/main/path.ipynb` 開啟。
   * **命令列更新**：若是在 Colab 的虛擬機中下載了專案，可直接執行 `!git pull`。

---

## 4. 連接至 Local Runtime (本機執行期)

如果您希望在 Colab 的網頁介面上操作，但實際運算與檔案都存放在本地的電腦上。

### 實作步驟：
1. **安裝本地服務**：在本地環境中安裝 Jupyter 與連接套件：
   ```bash
   pip install jupyter_http_over_ws
   jupyter serverextension enable --py jupyter_http_over_ws
   ```
2. **啟動 Jupyter**：啟動本地伺服器並允許 Colab 連接：
   ```bash
   jupyter notebook --NotebookApp.allow_origin='https://colab.research.google.com' --port=8888 --NotebookApp.port_retries=0
   ```
3. **連線**：在 Colab 網頁右上角的「連線」選單中，選擇 **「連線至本機執行期」 (Connect to a local runtime)**，並輸入本機 Jupyter 的網址與 Token。

### 優點：
Colab 網頁端會直接操作您本地的檔案系統與運算資源，您在 Antigravity 中的任何修改皆會即時反映。
