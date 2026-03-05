import requests
import os
import time


EMAIL = "test@test.com"

HEADERS = {
    "User-Agent": f"MyAnalysisApp {EMAIL}",
    "Accept-Encoding": "gzip, deflate",
}


def _find_10k_in_filings(filings: dict) -> tuple | None:
    """
    공시 목록에서 첫 번째 10-K 항목을 찾아
    (accessionNumber_clean, primaryDocument) 튜플 반환. 없으면 None.
    """
    for i, form in enumerate(filings.get('form', [])):
        if form == '10-K':
            acc_num_clean = filings['accessionNumber'][i].replace('-', '')
            doc_name = filings['primaryDocument'][i]
            return acc_num_clean, doc_name
    return None


def download_10k(ticker: str, save_dir: str = "./reports") -> dict:
    """
    10-K 보고서를 다운로드하고 결과를 딕셔너리로 반환.

    Returns:
        {
            "success": bool,
            "message": str,
            "save_path": str | None,
            "download_url": str | None,
        }
    """
    ticker = ticker.upper().strip()

    try:
        # 1. CIK 조회
        ticker_url = "https://www.sec.gov/files/company_tickers.json"
        res = requests.get(ticker_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
        time.sleep(0.1)

        cik_padded = None
        cik_int_str = None
        company_name = None

        for item in data.values():
            if item['ticker'] == ticker:
                cik_padded = str(item['cik_str']).zfill(10)
                cik_int_str = str(int(cik_padded))
                company_name = item.get('title', ticker)
                break

        if not cik_padded:
            return {"success": False, "message": f"'{ticker}' 티커를 찾을 수 없습니다.", "save_path": None, "download_url": None}

        # 2. 공시 정보 조회
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        sub_res = requests.get(submissions_url, headers=HEADERS, timeout=10)
        sub_res.raise_for_status()
        time.sleep(0.1)

        submissions_data = sub_res.json()

        # 3. 10-K 탐색 (recent → 전체 파일 목록)
        filing_result = _find_10k_in_filings(submissions_data['filings']['recent'])

        if not filing_result:
            for extra_file in submissions_data['filings'].get('files', []):
                extra_url = f"https://data.sec.gov/submissions/{extra_file['name']}"
                extra_res = requests.get(extra_url, headers=HEADERS, timeout=10)
                extra_res.raise_for_status()
                time.sleep(0.1)
                filing_result = _find_10k_in_filings(extra_res.json())
                if filing_result:
                    break

        if not filing_result:
            return {"success": False, "message": f"'{ticker}'의 10-K 보고서를 찾을 수 없습니다.", "save_path": None, "download_url": None}

        acc_num_clean, doc_name = filing_result

        # 4. 다운로드
        download_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int_str}/{acc_num_clean}/{doc_name}"
        )

        os.makedirs(save_dir, exist_ok=True)
        ext = os.path.splitext(doc_name)[1]
        save_path = os.path.join(save_dir, f"{ticker}_10K{ext}")

        with requests.get(download_url, headers=HEADERS, stream=True, timeout=30) as file_res:
            file_res.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in file_res.iter_content(chunk_size=8192):
                    f.write(chunk)

        return {
            "success": True,
            "message": f"{company_name} ({ticker}) 10-K 보고서 다운로드 완료",
            "save_path": save_path,
            "download_url": download_url,
        }

    except requests.exceptions.HTTPError as e:
        return {"success": False, "message": f"HTTP 오류: {e.response.status_code}", "save_path": None, "download_url": None}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "네트워크 연결 오류. 인터넷 연결을 확인해주세요.", "save_path": None, "download_url": None}
    except requests.exceptions.Timeout:
        return {"success": False, "message": "요청 시간 초과. 잠시 후 다시 시도해주세요.", "save_path": None, "download_url": None}
    except Exception as e:
        return {"success": False, "message": f"예상치 못한 오류: {e}", "save_path": None, "download_url": None}