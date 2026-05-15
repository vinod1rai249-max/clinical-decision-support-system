import httpx
import xml.etree.ElementTree as ET
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class PubMedTool:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def search_papers(self, client, query, max_results=3):
        """Search PubMed and return list of PMIDs with Circuit Breaker (Tenacity)."""
        url = f"{self.BASE_URL}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": f"{query} AND (human[Filter])",
            "retmode": "json",
            "retmax": max_results
        }
        try:
            response = await client.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [429, 500, 502, 503, 504]:
                print(f"[PubMed Circuit Breaker] Rate limited or server error ({e.response.status_code}). Retrying...")
                raise e # Trigger tenacity retry
            return []
        except Exception as e:
            print(f"[PubMed Error] Search failed: {str(e)}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def fetch_abstracts(self, client, pmid_list):
        """Fetch abstracts for a list of PMIDs with Circuit Breaker."""
        if not pmid_list:
            return []
        
        url = f"{self.BASE_URL}efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmid_list),
            "retmode": "xml",
            "rettype": "abstract"
        }
        try:
            response = await client.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            abstracts = []
            for article in root.findall(".//PubmedArticle"):
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "0"
                
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "Untitled Research"
                
                abstract_text = ""
                abstract_element = article.find(".//AbstractText")
                if abstract_element is not None:
                    abstract_text = "".join(abstract_element.itertext())
                
                abstracts.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract_text
                })
            return abstracts
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [429, 500, 502, 503, 504]:
                raise e # Trigger tenacity retry
            return []
        except Exception:
            return []

    async def get_research(self, client, query, max_results=3):
        """Full pipeline: search and fetch."""
        pmids = await self.search_papers(client, query, max_results)
        if not pmids:
            return []
        return await self.fetch_abstracts(client, pmids)
