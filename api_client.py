import requests, time
import urllib3
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class GitLabAPIClient:
    def __init__(self, cfg):
        self.base_url = cfg["BASE_URL"]
        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": cfg["PRIVATE_TOKEN"]})
        self.timeout = cfg["REQUEST_TIMEOUT"]
        self.retries = cfg["MAX_RETRIES"]
        self.backoff = cfg["BACKOFF_FACTOR"]

    def request(self, method, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        for i in range(1, self.retries + 1):
            try:
                r = self.session.request(method, url, params=params, timeout=self.timeout, verify=False)
                if r.status_code == 429:
                    logger.warning(f"Rate limit hit (429). Retrying in {self.backoff ** i} seconds...")
                    time.sleep(self.backoff ** i)
                    continue
                r.raise_for_status()
                
                # Handle JSON decode errors
                try:
                    return r.json()
                except ValueError as json_err:
                    logger.error(f"Invalid JSON response from {url}: {str(json_err)}")
                    logger.debug(f"Response content: {r.text[:500]}")
                    raise ValueError(f"GitLab returned invalid JSON for {endpoint}") from json_err
                    
            except requests.exceptions.HTTPError as http_err:
                # Don't retry on 4xx client errors (except 429 which is handled above)
                if 400 <= http_err.response.status_code < 500:
                    raise  # Immediately raise, no retry
                # Retry on 5xx server errors
                if i == self.retries:
                    raise
                logger.warning(f"HTTP error {http_err.response.status_code}. Retry {i}/{self.retries} in {self.backoff ** i} seconds...")
                time.sleep(self.backoff ** i)
            except requests.exceptions.RequestException as req_err:
                # Retry on network/timeout errors
                if i == self.retries:
                    raise
                logger.warning(f"Network error: {str(req_err)}. Retry {i}/{self.retries} in {self.backoff ** i} seconds...")
                time.sleep(self.backoff ** i)

    def paginate(self, endpoint, params=None):
        page, results = 1, []
        while True:
            data = self.request("GET", endpoint, {**(params or {}), "page": page, "per_page": 100})
            results.extend(data)
            if len(data) < 100:
                break
            page += 1
        return results
