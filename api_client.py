import requests, time

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
                r = self.session.request(method, url, params=params, timeout=self.timeout)
                if r.status_code == 429:
                    time.sleep(self.backoff ** i)
                    continue
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException:
                if i == self.retries:
                    raise
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
