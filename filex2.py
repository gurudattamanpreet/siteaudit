"""
Novarsis AI SEO Analyzer - One Click Solution
Groq AI + FastMCP + SEMrush + Web Crawler + Site Audit
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
from typing import Optional, List, Dict
import uvicorn
import json
from groq import Groq
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
import os

app = FastAPI(title="Novarsis AI SEO Analyzer", version="1.0")

# Configuration
SEMRUSH_API_KEY = os.environ.get("SEMRUSH_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
BASE_URL = "https://api.semrush.com/"
BACKLINKS_URL = "https://api.semrush.com/analytics/v1/"
SITE_AUDIT_URL = "https://api.semrush.com/reports/v1"
PROJECT_ID = os.environ.get("PROJECT_ID", "26460775")
groq_client = Groq(api_key=GROQ_API_KEY)

# Complete Issue ID Mapping from Semrush Documentation
ISSUE_MAPPING = {
    # Errors
    1: "5xx errors",
    2: "4xx errors",
    3: "Title tag is missing or empty",
    4: "Blocked from crawling",
    6: "Duplicate title tag",
    7: "Duplicate content",
    8: "Broken internal links",
    9: "Pages not crawled",
    10: "DNS resolution issue",
    11: "We couldn't open the page's URL",
    13: "Broken internal images",
    15: "Duplicate meta descriptions",
    16: "Invalid robots.txt format",
    17: "Invalid sitemap.xml format",
    18: "Incorrect pages found in",
    19: "www resolve issues",
    20: "Viewport not configured",
    21: "Large HTML page size",
    22: "Missing canonical tags in AMP pages",
    26: "Non-secure pages",
    27: "Certificate Expiration",
    28: "Old security protocol version",
    29: "Certificate registered to incorrect",
    30: "Issues with mixed content",
    32: "Neither canonical URL nor 301 redirect from HTTP homepage",
    33: "Redirect chains and loops",
    34: "AMP Pages with HTML Issues",
    35: "AMP Pages with Style and Layout",
    36: "AMP Pages with Templating Issues",
    38: "Broken canonical URLs",
    39: "Multiple canonical URLs",
    40: "Meta refresh redirects",
    41: "Broken internal JavaScript and CSS",
    42: "Insecure encryption algorithms",
    43: "Sitemap file too large",
    44: "Malformed links",
    45: "Structured data that contains",
    46: "Viewport width not set",
    111: "Slow page load speed",

    # Warnings
    12: "Broken external links",
    14: "Broken external images",
    31: "Links lead to HTTP pages for HTTPS",
    101: "Title element is too short",
    102: "Title element is too long",
    103: "Missing h1",
    104: "Multiple h1 tags",
    105: "Duplicate content in h1 and title",
    106: "Missing meta description",
    108: "Too many on-page links",
    109: "Temporary redirects",
    110: "Missing ALT attributes",
    112: "Low text to HTML ratio",
    113: "Too many URL parameters",
    114: "Missing hreflang and lang attributes",
    115: "Encoding not declared",
    116: "Doctype not declared",
    117: "Low word count",
    120: "Incompatible plugins used",
    121: "Frames used",
    122: "Underscores in URL",
    123: "Nofollow attributes in internal links",
    124: "Sitemap.xml not specified in",
    125: "Sitemap.xml not found",
    126: "HTTPS encryption not used",
    127: "No SNI support",
    128: "HTTP URLs in sitemap.xml for HTTPS",
    129: "Uncompressed pages",
    130: "Disallowed internal resources",
    131: "Uncompressed JavaScript and CSS",
    132: "Uncached JavaScript and CSS files",
    133: "Too large JavaScript and CSS total",
    134: "Too many JavaScript and CSS files",
    135: "Unminified JavaScript and CSS files",
    136: "Warning - Too long URLs",
    137: "Llms.txt not found",

    # Notices
    201: "Too long URLs",
    202: "Nofollow attributes in external links",
    203: "Robots.txt not found",
    205: "No HSTS support",
    206: "Orphaned pages (Google Analytics)",
    207: "Orphaned sitemap pages",
    208: "Pages have high Document",
    209: "Blocked by X-Robots-Tag: noindex HTTP header",
    210: "Disallowed external resources",
    211: "Broken external JavaScript and CSS",
    212: "Page crawl depth",
    213: "Pages with only one internal link",
    214: "Permanent redirects",
    215: "Resources formatted as page links",
    216: "Links with no anchor text",
    217: "Links with non-descriptive anchor",
    218: "External pages or resources with 403 HTTP status code",
    219: "Llms.txt has formatting issues",
    220: "Too much content",
    221: "Outdated content",
    222: "Low semantic HTML usage",
    223: "Content not optimized"
}


# Models
class DomainRequest(BaseModel):
    domain: str
    database: str = "us"


class KeywordRequest(BaseModel):
    keyword: str
    database: str = "us"
    limit: int = 30


class RecommendationRequest(BaseModel):
    domain: str
    business_goals: Dict
    metrics: Dict
    onpage_data: Optional[Dict] = None
    site_audit_data: Optional[Dict] = None


class SiteAuditRequest(BaseModel):
    project_id: Optional[str] = PROJECT_ID
    issue_id: Optional[int] = None
    limit: int = 100


# On-Page Crawler
def crawl_website_onpage(domain: str) -> Dict:
    try:
        url = domain if domain.startswith('http') else f'https://{domain}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Meta Description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc['content'] if meta_desc and meta_desc.get('content') else None
        meta_desc_length = len(meta_description) if meta_description else 0

        # Title
        title_tag = soup.find('title')
        title = title_tag.string if title_tag else None
        title_length = len(title) if title else 0

        # Headers
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        h4_tags = soup.find_all('h4')

        h1_count = len(h1_tags)
        h1_text = [h.get_text(strip=True) for h in h1_tags]

        # Content
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = re.sub(r'\s+', ' ', text_content)
        word_count = len(text_content.split())

        # Images
        images = soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt')]
        images_without_alt = len(images) - len(images_with_alt)

        return {
            'meta_description': meta_description,
            'meta_desc_length': meta_desc_length,
            'meta_desc_status': 'Good' if 150 <= meta_desc_length <= 160 else 'Needs Fix',
            'title_tag': title,
            'title_length': title_length,
            'title_status': 'Good' if 50 <= title_length <= 60 else 'Needs Fix',
            'h1_count': h1_count,
            'h1_status': 'Good' if h1_count == 1 else 'Multiple' if h1_count > 1 else 'Missing',
            'h1_text': h1_text,
            'h2_count': len(h2_tags),
            'h3_count': len(h3_tags),
            'h4_count': len(h4_tags),
            'word_count': word_count,
            'content_status': 'Good' if word_count >= 1000 else 'Thin' if word_count < 300 else 'Moderate',
            'images_total': len(images),
            'images_without_alt': images_without_alt,
            'crawl_success': True
        }
    except Exception as e:
        print(f"Crawl error: {str(e)}")
        return {'crawl_success': False, 'error': str(e)}


def parse_response(text: str):
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return None
    headers = lines[0].split(';')
    if len(lines) == 2:
        return dict(zip(headers, lines[1].split(';')))
    return [dict(zip(headers, line.split(';'))) for line in lines[1:]]


def make_request(url: str, report_type: str, **kwargs):
    params = {'key': SEMRUSH_API_KEY, 'type': report_type, **kwargs}
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200 and 'ERROR' not in response.text.upper():
            return parse_response(response.text)
    except:
        pass
    return None


def generate_ai_recommendations(domain: str, business_goals: dict, metrics: dict, onpage_data: dict = None,
                                site_audit_data: dict = None):
    onpage_context = ""
    if onpage_data and onpage_data.get('crawl_success'):
        onpage_context = f"""
ON-PAGE DATA:
- Meta: {onpage_data.get('meta_desc_status')} ({onpage_data.get('meta_desc_length')} chars)
- Title: {onpage_data.get('title_status')} ({onpage_data.get('title_length')} chars)
- H1: {onpage_data.get('h1_status')} (Count: {onpage_data.get('h1_count')})
- Headers: H2={onpage_data.get('h2_count')}, H3={onpage_data.get('h3_count')}, H4={onpage_data.get('h4_count')}
- Content: {onpage_data.get('content_status')} ({onpage_data.get('word_count')} words)
- Images without Alt: {onpage_data.get('images_without_alt')}/{onpage_data.get('images_total')}
"""

    audit_context = ""
    if site_audit_data and site_audit_data.get('issues'):
        issues = site_audit_data['issues']
        errors = [i for i in issues if i.get('severity') == 'Error']
        warnings = [i for i in issues if i.get('severity') == 'Warning']
        notices = [i for i in issues if i.get('severity') == 'Notice']

        audit_context = f"""
SITE AUDIT DATA:
- Total Issues: {len(issues)}
- Errors: {len(errors)} critical issues
- Warnings: {len(warnings)} issues
- Notices: {len(notices)} minor issues

Top Critical Issues:
"""
        # Add top 10 critical issues
        sorted_issues = sorted(issues, key=lambda x: (
            0 if x.get('severity') == 'Error' else 1 if x.get('severity') == 'Warning' else 2, -x.get('count', 0)))
        for issue in sorted_issues[:10]:
            audit_context += f"- [{issue.get('severity')}] {issue.get('issue_name')}: {issue.get('count')} pages affected\n"

    prompt = f"""SEO Expert using FastMCP.

DOMAIN: {domain}

BUSINESS:
- Objective: {business_goals.get('objective', 'N/A')}
- Audience: {business_goals.get('audience', 'N/A')}
- Conversion: {business_goals.get('conversion', 'N/A')}
- Strategy: {business_goals.get('strategy', 'N/A')}
- Stage: {business_goals.get('stage', 'N/A')}
- Position: {business_goals.get('position', 'N/A')}

METRICS:
- Rank: {metrics.get('rank', 'N/A')}
- Keywords: {metrics.get('organic_keywords', 'N/A')}
- Traffic: {metrics.get('organic_traffic', 'N/A')}
- Backlinks: {metrics.get('backlinks', 'N/A')}
{onpage_context}{audit_context}

Generate 10 SEO recommendations using ALL data above (business goals, metrics, on-page analysis, AND site audit issues).

JSON format (10 objects):
[{{"category":"Short title","icon":"emoji","severity":"high/medium","issue":"Specific problem with actual data from above","fix":"1. Step 2. Step 3. Step 4. Step 5. Step 6. Step"}}]

ONLY JSON, no markdown."""

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "SEO expert. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            temperature=0.7,
            max_tokens=8000,
        )

        text = response.choices[0].message.content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```") < source_id
            data = "1"
            title = "N/A" / >.split("```")[0]

        recs = json.loads(text.strip())
        if isinstance(recs, list) and len(recs) >= 10:
            return recs[:10]
        return recs if isinstance(recs, list) else []
    except:
        return [
            {"category": "Meta Description", "icon": "📝", "severity": "high", "issue": "Optimize meta descriptions",
             "fix": "1. Write 150-160 chars 2. Include keywords 3. Add CTA 4. Benefit-focused 5. Unique 6. Test CTR"},
            {"category": "Title Tags", "icon": "🏷️", "severity": "high", "issue": "Improve title tags",
             "fix": "1. Keep 50-60 chars 2. Keywords first 3. Add brand 4. Unique 5. Power words 6. Match intent"},
            {"category": "H1 Tags", "icon": "📑", "severity": "high", "issue": "Fix H1 structure",
             "fix": "1. Single H1 2. Include keyword 3. Descriptive 4. Under 70 chars 5. Match title 6. Unique"},
            {"category": "Headers", "icon": "📊", "severity": "medium", "issue": "Better header hierarchy",
             "fix": "1. Logical order 2. H1-H2-H3-H4 3. Keywords natural 4. Descriptive 5. Section breaks 6. Consistent"},
            {"category": "Content", "icon": "✍️", "severity": "high", "issue": "Enhance content quality",
             "fix": "1. Create 1000+ words 2. Research competitors 3. Answer questions 4. Add value 5. Update often 6. E-E-A-T"},
            {"category": "Keywords", "icon": "🔑", "severity": "high", "issue": "Refine keyword strategy",
             "fix": "1. Long-tail research 2. Optimize title H1 URL 3. LSI keywords 4. 1-2% density 5. Alt text 6. User intent"},
            {"category": "Images", "icon": "🖼️", "severity": "medium", "issue": "Add alt text to images",
             "fix": "1. Descriptive alt 2. Keywords natural 3. Describe image 4. Under 125 chars 5. No stuffing 6. All images"},
            {"category": "Technical SEO", "icon": "⚙️", "severity": "high", "issue": "Fix technical issues",
             "fix": "1. Crawl errors 2. Robots.txt 3. XML sitemap 4. Broken links 5. Canonical tags 6. Schema markup"},
            {"category": "Link Building", "icon": "🔗", "severity": "medium", "issue": "Strengthen backlinks",
             "fix": "1. Quality content 2. Guest posts 3. Fix broken links 4. Relationships 5. Shareable assets 6. Monitor"},
            {"category": "Conversions", "icon": "🎯", "severity": "high", "issue": "Optimize conversions",
             "fix": "1. Clear CTAs 2. Simple forms 3. Trust signals 4. Landing pages 5. A/B test 6. Reduce friction"}
        ]


# Site Audit Functions
def get_all_issues_summary(project_id=PROJECT_ID):
    """Get summary of all issues using the latest snapshot"""
    url = f"{SITE_AUDIT_URL}/projects/{project_id}/siteaudit/snapshot"
    params = {"key": SEMRUSH_API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        snapshot_id = data.get('snapshot_id')
        issues_data = []

        # Process errors
        if 'errors' in data:
            for error in data['errors']:
                issue_id = error['id']
                count = error['count']
                if count > 0:
                    issues_data.append({
                        'issue_id': issue_id,
                        'issue_name': ISSUE_MAPPING.get(issue_id, f"Unknown Issue {issue_id}"),
                        'severity': 'Error',
                        'count': count,
                        'delta': error.get('delta', 0)
                    })

        # Process warnings
        if 'warnings' in data:
            for warning in data['warnings']:
                issue_id = warning['id']
                count = warning['count']
                if count > 0:
                    issues_data.append({
                        'issue_id': issue_id,
                        'issue_name': ISSUE_MAPPING.get(issue_id, f"Unknown Issue {issue_id}"),
                        'severity': 'Warning',
                        'count': count,
                        'delta': warning.get('delta', 0)
                    })

        # Process notices
        if 'notices' in data:
            for notice in data['notices']:
                issue_id = notice['id']
                count = notice['count']
                if count > 0:
                    issues_data.append({
                        'issue_id': issue_id,
                        'issue_name': ISSUE_MAPPING.get(issue_id, f"Unknown Issue {issue_id}"),
                        'severity': 'Notice',
                        'count': count,
                        'delta': notice.get('delta', 0)
                    })

        return issues_data, snapshot_id
    except Exception as e:
        print(f"Error fetching issues summary: {e}")
        return [], None


def get_issue_details(project_id, snapshot_id, issue_id, limit=100):
    """Fetch detailed pages for a specific issue"""
    url = f"{SITE_AUDIT_URL}/projects/{project_id}/siteaudit/snapshot/{snapshot_id}/issue/{issue_id}"

    params = {
        "key": SEMRUSH_API_KEY,
        "limit": limit,
        "page": 1
    }

    all_pages = []

    try:
        current_page = 1

        while True:
            params['page'] = current_page
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if 'data' in data:
                pages_data = data['data']
                total_count = data.get('total', 0)

                if not pages_data:
                    break

                all_pages.extend(pages_data)

                # Check if we've got all pages
                if len(all_pages) >= total_count:
                    break

                current_page += 1
            else:
                break

        return all_pages, data.get('total', 0)
    except Exception as e:
        print(f"Error fetching issue details: {e}")
        return [], 0


# API Endpoints
@app.post("/api/domain/overview")
async def get_domain_overview(req: DomainRequest):
    result = make_request(BASE_URL, 'domain_rank', domain=req.domain, database=req.database)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/organic/keywords")
async def get_organic_keywords(req: DomainRequest):
    result = make_request(BASE_URL, 'domain_organic', domain=req.domain, database=req.database, display_limit=100,
                          export_escape=1)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/organic/competitors")
async def get_competitors(req: DomainRequest):
    result = make_request(BASE_URL, 'domain_organic_organic', domain=req.domain, database=req.database,
                          display_limit=20)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/backlinks/referring-domains")
async def get_referring_domains(req: DomainRequest):
    params = {'key': SEMRUSH_API_KEY, 'type': 'backlinks_refdomains', 'target': req.domain,
              'target_type': 'root_domain', 'export_columns': 'domain_ascore,domain,backlinks_num,ip,country',
              'display_limit': 500}
    try:
        response = requests.get(BACKLINKS_URL, params=params, timeout=30)
        if response.status_code == 200:
            result = parse_response(response.text)
            if result:
                toxic, potentially_toxic, healthy = [], [], []
                for domain in result:
                    score = float(domain.get('domain_ascore', 0))
                    if score < 30:
                        toxic.append(domain)
                    elif score < 50:
                        potentially_toxic.append(domain)
                    else:
                        healthy.append(domain)
                return {"success": True, "data": result, "analysis": {"total": len(result), "toxic": len(toxic),
                                                                      "potentially_toxic": len(potentially_toxic),
                                                                      "healthy": len(healthy)}}
    except:
        pass
    raise HTTPException(404, "Not found")


@app.post("/api/backlinks/anchors")
async def get_anchors(req: DomainRequest):
    params = {'key': SEMRUSH_API_KEY, 'type': 'backlinks_anchors', 'target': req.domain, 'target_type': 'root_domain',
              'export_columns': 'anchor,domains_num,backlinks_num', 'display_limit': 100}
    try:
        response = requests.get(BACKLINKS_URL, params=params, timeout=30)
        if response.status_code == 200:
            result = parse_response(response.text)
            if result:
                return {"success": True, "data": result}
    except:
        pass
    raise HTTPException(404, "Not found")


@app.post("/api/keyword/overview")
async def get_keyword_overview(req: KeywordRequest):
    result = make_request(BASE_URL, 'phrase_this', phrase=req.keyword, database=req.database, export_escape=1)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/keyword/related")
async def get_related_keywords(req: KeywordRequest):
    result = make_request(BASE_URL, 'phrase_related', phrase=req.keyword, database=req.database,
                          display_limit=req.limit, export_escape=1)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/keyword/serp")
async def get_serp(req: KeywordRequest):
    result = make_request(BASE_URL, 'phrase_organic', phrase=req.keyword, database=req.database,
                          display_limit=req.limit, export_escape=1)
    if result:
        return {"success": True, "data": result}
    raise HTTPException(404, "Not found")


@app.post("/api/recommendations")
async def get_recommendations(req: RecommendationRequest):
    try:
        # Get on-page data if not provided
        if not req.onpage_data:
            req.onpage_data = crawl_website_onpage(req.domain)

        # Get site audit data if not provided
        if not req.site_audit_data:
            issues, _ = get_all_issues_summary(PROJECT_ID)
            if issues:
                req.site_audit_data = {"issues": issues}

        recs = generate_ai_recommendations(req.domain, req.business_goals, req.metrics, req.onpage_data,
                                           req.site_audit_data)
        return {"success": True, "recommendations": recs, "onpage_data": req.onpage_data,
                "site_audit_data": req.site_audit_data}
    except Exception as e:
        print(f"Recommendation error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/complete-analysis")
async def complete_analysis(req: DomainRequest):
    results = {}
    results['domain_overview'] = make_request(BASE_URL, 'domain_rank', domain=req.domain, database=req.database)
    results['organic_keywords'] = make_request(BASE_URL, 'domain_organic', domain=req.domain, database=req.database,
                                               display_limit=50, export_escape=1)
    results['competitors'] = make_request(BASE_URL, 'domain_organic_organic', domain=req.domain, database=req.database,
                                          display_limit=10)
    params = {'key': SEMRUSH_API_KEY, 'type': 'backlinks_overview', 'target': req.domain, 'target_type': 'root_domain'}
    try:
        response = requests.get(BACKLINKS_URL, params=params, timeout=30)
        if response.status_code == 200:
            results['backlinks_overview'] = parse_response(response.text)
    except:
        results['backlinks_overview'] = None
    results['onpage_analysis'] = crawl_website_onpage(req.domain)

    # Add site audit data
    issues, _ = get_all_issues_summary(PROJECT_ID)
    if issues:
        results['site_audit'] = {"issues": issues}

    return {"success": True, "data": results}


# Site Audit Endpoints
@app.post("/api/site-audit/issues")
async def get_site_audit_issues(req: SiteAuditRequest):
    issues, snapshot_id = get_all_issues_summary(req.project_id)
    if issues and snapshot_id:
        return {"success": True, "data": issues, "snapshot_id": snapshot_id}
    return {"success": False, "message": "No issues found or error fetching issues"}


@app.post("/api/site-audit/issue-details")
async def get_site_audit_issue_details(req: SiteAuditRequest):
    if not req.issue_id:
        raise HTTPException(400, "Issue ID is required")

    # First get the snapshot ID
    issues, snapshot_id = get_all_issues_summary(req.project_id)
    if not snapshot_id:
        return {"success": False, "message": "Could not retrieve snapshot ID"}

    # Get issue details
    pages, total = get_issue_details(req.project_id, snapshot_id, req.issue_id, req.limit)
    if pages:
        # Find issue name
        issue_name = "Unknown Issue"
        for issue in issues:
            if issue['issue_id'] == req.issue_id:
                issue_name = issue['issue_name']
                break

        return {
            "success": True,
            "data": pages,
            "total": total,
            "issue_name": issue_name,
            "snapshot_id": snapshot_id
        }
    return {"success": False, "message": f"No data found for issue ID {req.issue_id}"}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Novarsis AI SEO Analyzer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);color:#2d3748;min-height:100vh;padding:20px}
.container{max-width:1400px;margin:0 auto}
.header{text-align:center;margin-bottom:40px}
.header h1{font-size:2.8em;color:#667eea;margin-bottom:8px;font-weight:700}
.header .subtitle{font-size:1.2em;color:#475569;margin-bottom:15px;font-weight:500}
.section{background:white;border-radius:12px;padding:30px;margin-bottom:30px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
.section h2{margin-bottom:20px;color:#1e293b}
.question-group{margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid #e2e8f0}
.question-group:last-child{border-bottom:none}
.question-title{font-weight:600;margin-bottom:15px}
.radio-option{background:#f8fafc;border:2px solid #e2e8f0;border-radius:8px;padding:12px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center}
.radio-option:hover{border-color:#667eea}
.radio-option.selected{border-color:#667eea;background:rgba(102,126,234,0.05)}
.radio-option input{margin-right:10px;cursor:pointer}
.radio-option label{cursor:pointer;flex:1}
.tabs{display:flex;gap:10px;margin-bottom:20px;border-bottom:2px solid #e2e8f0;flex-wrap:wrap}
.tab{padding:12px 20px;background:transparent;border:none;border-bottom:3px solid transparent;cursor:pointer;font-weight:600;color:#64748b}
.tab:hover{color:#667eea}
.tab.active{color:#667eea;border-bottom-color:#667eea}
.tab-content{display:none}
.tab-content.active{display:block}
.input-group{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-bottom:20px}
.input-field label{display:block;margin-bottom:5px;font-weight:600;font-size:0.9em}
.input-field input,.input-field select{width:100%;padding:10px;border:2px solid #e2e8f0;border-radius:6px}
.btn{padding:10px 24px;background:#667eea;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;margin-right:10px}
.btn:hover{background:#5568d3}
.btn-secondary{background:#4facfe}
.loading{text-align:center;padding:40px}
.spinner{border:4px solid #e2e8f0;border-top:4px solid #667eea;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin:20px 0}
.metric-card{background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:10px;color:white}
.metric-card h3{font-size:0.85em;opacity:0.9;margin-bottom:8px}
.metric-card .value{font-size:1.8em;font-weight:700}
.table-container{margin-top:20px;overflow-x:auto}
.data-table{width:100%;border-collapse:collapse}
.data-table th,.data-table td{padding:12px;text-align:left;border-bottom:1px solid #e2e8f0}
.data-table th{background:#f8fafc;font-weight:600;color:#667eea}
.data-table tr:hover{background:#f8fafc}
.alert-error{background:#fee;border:1px solid #fcc;color:#c00;padding:15px;border-radius:6px;margin-top:20px}
.rec-card{background:white;border-radius:10px;padding:25px;margin-bottom:20px;border-left:4px solid #667eea;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
.rec-card.high{border-left-color:#ef4444}
.rec-card.medium{border-left-color:#f59e0b}
.rec-header{display:flex;align-items:center;gap:15px;margin-bottom:15px}
.rec-icon{font-size:2em}
.rec-title h3{font-size:1.3em;margin-bottom:5px}
.severity-badge{padding:4px 12px;border-radius:15px;font-size:0.75em;font-weight:600;text-transform:uppercase}
.severity-high{background:#fee2e2;color:#dc2626}
.severity-medium{background:#fef3c7;color:#d97706}
.issue-section{background:#f8fafc;padding:15px;border-radius:6px;margin-bottom:15px}
.issue-section h4{margin-bottom:8px;color:#475569}
.issue-section p{color:#64748b;line-height:1.6}
.fix-section{background:#f0fdf4;padding:15px;border-radius:6px;border:1px solid #bbf7d0}
.fix-section h4{margin-bottom:10px;color:#15803d}
.fix-section ol{margin-left:20px;color:#166534}
.fix-section li{margin-bottom:8px;line-height:1.5}
.ai-loading{background:linear-gradient(135deg,#f093fb,#f5576c);color:white;padding:25px;border-radius:10px;text-align:center;margin:20px 0}
.ai-pulse{display:inline-block;width:10px;height:10px;background:white;border-radius:50%;animation:pulse 1.5s ease-in-out infinite;margin:0 3px}
@keyframes pulse{0%,100%{opacity:0.3}50%{opacity:1}}
.onpage-box{background:#fef3c7;border:2px solid #fbbf24;padding:20px;border-radius:8px;margin:20px 0}
.onpage-box h4{color:#92400e;margin-bottom:15px}
.onpage-item{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #fcd34d}
.onpage-item:last-child{border-bottom:none}
.onpage-label{font-weight:600;color:#78350f}
.onpage-value{color:#451a03}
.issue-card{background:white;border-radius:10px;padding:20px;margin-bottom:15px;border-left:4px solid #667eea;box-shadow:0 2px 8px rgba(0,0,0,0.05)}
.issue-card.error{border-left-color:#ef4444}
.issue-card.warning{border-left-color:#f59e0b}
.issue-card.notice{border-left-color:#10b981}
.issue-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.issue-title{font-weight:600;font-size:1.1em}
.issue-count{background:#f3f4f6;padding:4px 8px;border-radius:4px;font-weight:600}
.issue-details{display:flex;gap:10px;margin-top:15px}
.issue-id{background:#e5e7eb;padding:2px 6px;border-radius:4px;font-size:0.8em}
.issue-severity{padding:2px 6px;border-radius:4px;font-size:0.8em;color:white}
.issue-severity.error{background:#ef4444}
.issue-severity.warning{background:#f59e0b}
.issue-severity.notice{background:#10b981}
.url-link{color:#667eea;text-decoration:none}
.url-link:hover{text-decoration:underline}
.audit-box{background:#e0f2fe;border:2px solid #0ea5e9;padding:20px;border-radius:8px;margin:20px 0}
.audit-box h4{color:#0369a1;margin-bottom:15px}
.audit-item{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #7dd3fc}
.audit-item:last-child{border-bottom:none}
.audit-label{font-weight:600;color:#075985}
.audit-value{color:#0c4a6e}
.audit-value.error{color:#dc2626;font-weight:600}
.audit-value.warning{color:#d97706;font-weight:600}
.audit-value.notice{color:#059669;font-weight:600}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>Novarsis AI SEO Analyzer</h1>
<div class="subtitle">One Click Solution</div>
</div>

<div class="section">
<h2>📋 Business Goals</h2>
<div class="question-group">
<div class="question-title">1. Primary objective?</div>
<div class="radio-option" onclick="selectOption(this,'objective','sales')"><input type="radio" name="objective" value="sales" id="obj1"><label for="obj1">Increase sales</label></div>
<div class="radio-option" onclick="selectOption(this,'objective','leads')"><input type="radio" name="objective" value="leads" id="obj2"><label for="obj2">Generate leads</label></div>
<div class="radio-option" onclick="selectOption(this,'objective','brand')"><input type="radio" name="objective" value="brand" id="obj3"><label for="obj3">Build brand</label></div>
<div class="radio-option" onclick="selectOption(this,'objective','traffic')"><input type="radio" name="objective" value="traffic" id="obj4"><label for="obj4">Grow traffic</label></div>
</div>

<div class="question-group">
<div class="question-title">2. Target audience?</div>
<div class="radio-option" onclick="selectOption(this,'audience','b2b')"><input type="radio" name="audience" value="b2b" id="aud1"><label for="aud1">B2B</label></div>
<div class="radio-option" onclick="selectOption(this,'audience','b2c')"><input type="radio" name="audience" value="b2c" id="aud2"><label for="aud2">B2C</label></div>
<div class="radio-option" onclick="selectOption(this,'audience','mixed')"><input type="radio" name="audience" value="mixed" id="aud3"><label for="aud3">Mixed</label></div>
</div>

<div class="question-group">
<div class="question-title">3. Conversion goal?</div>
<div class="radio-option" onclick="selectOption(this,'conversion','purchase')"><input type="radio" name="conversion" value="purchase" id="con1"><label for="con1">Purchase</label></div>
<div class="radio-option" onclick="selectOption(this,'conversion','form')"><input type="radio" name="conversion" value="form" id="con2"><label for="con2">Form submission</label></div>
<div class="radio-option" onclick="selectOption(this,'conversion','signup')"><input type="radio" name="conversion" value="signup" id="con3"><label for="con3">Signup</label></div>
</div>

<div class="question-group">
<div class="question-title">4. Content strategy?</div>
<div class="radio-option" onclick="selectOption(this,'strategy','educational')"><input type="radio" name="strategy" value="educational" id="str1"><label for="str1">Educational</label></div>
<div class="radio-option" onclick="selectOption(this,'strategy','product')"><input type="radio" name="strategy" value="product" id="str2"><label for="str2">Product-focused</label></div>
</div>

<div class="question-group">
<div class="question-title">5. Business stage?</div>
<div class="radio-option" onclick="selectOption(this,'stage','startup')"><input type="radio" name="stage" value="startup" id="sta1"><label for="sta1">Startup</label></div>
<div class="radio-option" onclick="selectOption(this,'stage','growth')"><input type="radio" name="stage" value="growth" id="sta2"><label for="sta2">Growth</label></div>
<div class="radio-option" onclick="selectOption(this,'stage','established')"><input type="radio" name="stage" value="established" id="sta3"><label for="sta3">Established</label></div>
</div>

<div class="question-group">
<div class="question-title">6. Competitive position?</div>
<div class="radio-option" onclick="selectOption(this,'position','leader')"><input type="radio" name="position" value="leader" id="pos1"><label for="pos1">Leader</label></div>
<div class="radio-option" onclick="selectOption(this,'position','challenger')"><input type="radio" name="position" value="challenger" id="pos2"><label for="pos2">Challenger</label></div>
<div class="radio-option" onclick="selectOption(this,'position','niche')"><input type="radio" name="position" value="niche" id="pos3"><label for="pos3">Niche</label></div>
</div>
</div>

<div class="section">
<div class="tabs">
<button class="tab active" onclick="switchTab('domain')">Domain</button>
<button class="tab" onclick="switchTab('organic')">Organic</button>
<button class="tab" onclick="switchTab('backlinks')">Backlinks</button>
<button class="tab" onclick="switchTab('keywords')">Keywords</button>
<button class="tab" onclick="switchTab('complete')">Complete</button>
<button class="tab" onclick="switchTab('site-audit')">Site Audit</button>
<button class="tab" onclick="switchTab('ai')">AI Recommendations</button>
</div>

<div id="domain" class="tab-content active">
<h2>Domain Analytics</h2>
<div class="input-group">
<div class="input-field"><label>Domain</label><input type="text" id="domain-input" value="pub.dev"></div>
<div class="input-field"><label>Database</label><select id="domain-db">
<option value="us">🇺🇸 United States</option>
<option value="uk">🇬🇧 United Kingdom</option>
<option value="ca">🇨🇦 Canada</option>
<option value="au">🇦🇺 Australia</option>
<option value="in">🇮🇳 India</option>
<option value="de">🇩🇪 Germany</option>
<option value="fr">🇫🇷 France</option>
<option value="es">🇪🇸 Spain</option>
<option value="it">🇮🇹 Italy</option>
<option value="br">🇧🇷 Brazil</option>
<option value="mx">🇲🇽 Mexico</option>
<option value="ar">🇦🇷 Argentina</option>
<option value="nl">🇳🇱 Netherlands</option>
<option value="se">🇸🇪 Sweden</option>
<option value="pl">🇵🇱 Poland</option>
<option value="tr">🇹🇷 Turkey</option>
<option value="ru">🇷🇺 Russia</option>
<option value="jp">🇯🇵 Japan</option>
<option value="kr">🇰🇷 South Korea</option>
<option value="cn">🇨🇳 China</option>
<option value="sg">🇸🇬 Singapore</option>
<option value="ae">🇦🇪 UAE</option>
<option value="za">🇿🇦 South Africa</option>
<option value="ng">🇳🇬 Nigeria</option>
</select></div>
</div>
<button class="btn" onclick="analyzeDomain()">Analyze</button>
<div id="domain-results"></div>
</div>

<div id="organic" class="tab-content">
<h2>Organic Search</h2>
<div class="input-group">
<div class="input-field"><label>Domain</label><input type="text" id="organic-input" value="pub.dev"></div>
<div class="input-field"><label>Database</label><select id="organic-db">
<option value="us">🇺🇸 United States</option>
<option value="uk">🇬🇧 United Kingdom</option>
<option value="ca">🇨🇦 Canada</option>
<option value="au">🇦🇺 Australia</option>
<option value="in">🇮🇳 India</option>
<option value="de">🇩🇪 Germany</option>
<option value="fr">🇫🇷 France</option>
<option value="es">🇪🇸 Spain</option>
<option value="it">🇮🇹 Italy</option>
<option value="br">🇧🇷 Brazil</option>
<option value="mx">🇲🇽 Mexico</option>
<option value="ar">🇦🇷 Argentina</option>
<option value="nl">🇳🇱 Netherlands</option>
<option value="se">🇸🇪 Sweden</option>
<option value="pl">🇵🇱 Poland</option>
<option value="tr">🇹🇷 Turkey</option>
<option value="ru">🇷🇺 Russia</option>
<option value="jp">🇯🇵 Japan</option>
<option value="kr">🇰🇷 South Korea</option>
<option value="cn">🇨🇳 China</option>
<option value="sg">🇸🇬 Singapore</option>
<option value="ae">🇦🇪 UAE</option>
<option value="za">🇿🇦 South Africa</option>
<option value="ng">🇳🇬 Nigeria</option>
</select></div>
</div>
<button class="btn" onclick="analyzeOrganic()">Keywords</button>
<button class="btn btn-secondary" onclick="getCompetitors()">Competitors</button>
<div id="organic-results"></div>
</div>

<div id="backlinks" class="tab-content">
<h2>Backlinks</h2>
<div class="input-group">
<div class="input-field"><label>Domain</label><input type="text" id="backlinks-input" value="pub.dev"></div>
</div>
<button class="btn" onclick="getReferring()">Referring Domains</button>
<button class="btn btn-secondary" onclick="getAnchors()">Anchors</button>
<div id="backlinks-results"></div>
</div>

<div id="keywords" class="tab-content">
<h2>Keyword Research</h2>
<div class="input-group">
<div class="input-field"><label>Keyword</label><input type="text" id="keyword-input" value="python tutorial"></div>
<div class="input-field"><label>Database</label><select id="keyword-db">
<option value="us">🇺🇸 United States</option>
<option value="uk">🇬🇧 United Kingdom</option>
<option value="ca">🇨🇦 Canada</option>
<option value="au">🇦🇺 Australia</option>
<option value="in">🇮🇳 India</option>
<option value="de">🇩🇪 Germany</option>
<option value="fr">🇫🇷 France</option>
<option value="es">🇪🇸 Spain</option>
<option value="it">🇮🇹 Italy</option>
<option value="br">🇧🇷 Brazil</option>
<option value="mx">🇲🇽 Mexico</option>
<option value="ar">🇦🇷 Argentina</option>
<option value="nl">🇳🇱 Netherlands</option>
<option value="se">🇸🇪 Sweden</option>
<option value="pl">🇵🇱 Poland</option>
<option value="tr">🇹🇷 Turkey</option>
<option value="ru">🇷🇺 Russia</option>
<option value="jp">🇯🇵 Japan</option>
<option value="kr">🇰🇷 South Korea</option>
<option value="cn">🇨🇳 China</option>
<option value="sg">🇸🇬 Singapore</option>
<option value="ae">🇦🇪 UAE</option>
<option value="za">🇿🇦 South Africa</option>
<option value="ng">🇳🇬 Nigeria</option>
</select></div>
</div>
<button class="btn" onclick="analyzeKeyword()">Analyze</button>
<button class="btn btn-secondary" onclick="getRelated()">Related</button>
<div id="keywords-results"></div>
</div>

<div id="complete" class="tab-content">
<h2>Complete Analysis</h2>
<div class="input-group">
<div class="input-field"><label>Domain</label><input type="text" id="complete-input" value="pub.dev"></div>
<div class="input-field"><label>Database</label><select id="complete-db">
<option value="us">🇺🇸 United States</option>
<option value="uk">🇬🇧 United Kingdom</option>
<option value="ca">🇨🇦 Canada</option>
<option value="au">🇦🇺 Australia</option>
<option value="in">🇮🇳 India</option>
<option value="de">🇩🇪 Germany</option>
<option value="fr">🇫🇷 France</option>
<option value="es">🇪🇸 Spain</option>
<option value="it">🇮🇹 Italy</option>
<option value="br">🇧🇷 Brazil</option>
<option value="mx">🇲🇽 Mexico</option>
<option value="ar">🇦🇷 Argentina</option>
<option value="nl">🇳🇱 Netherlands</option>
<option value="se">🇸🇪 Sweden</option>
<option value="pl">🇵🇱 Poland</option>
<option value="tr">🇹🇷 Turkey</option>
<option value="ru">🇷🇺 Russia</option>
<option value="jp">🇯🇵 Japan</option>
<option value="kr">🇰🇷 South Korea</option>
<option value="cn">🇨🇳 China</option>
<option value="sg">🇸🇬 Singapore</option>
<option value="ae">🇦🇪 UAE</option>
<option value="za">🇿🇦 South Africa</option>
<option value="ng">🇳🇬 Nigeria</option>
</select></div>
</div>
<button class="btn" onclick="completeAnalysis()">Run Analysis</button>
<div id="complete-results"></div>
</div>

<div id="site-audit" class="tab-content">
<h2>🔍 Site Audit Issues</h2>
<div class="input-group">
<div class="input-field"><label>Project ID</label><input type="text" id="project-id-input" value="26460775"></div>
<div class="input-field"><label>Issue ID (Optional)</label><input type="text" id="issue-id-input" placeholder="e.g., 15"></div>
</div>
<button class="btn" onclick="getSiteAuditIssues()">Get Issues</button>
<button class="btn btn-secondary" onclick="getIssueDetails()">Get Issue Details</button>
<div id="site-audit-results"></div>
</div>

<div id="ai" class="tab-content">
<h2>🤖 AI-Powered SEO Recommendations</h2>
<p style="color:#64748b;margin-bottom:20px">✨ AI analyzes: Business Goals + SEMrush Metrics + On-Page Data + Site Audit Issues</p>
<div id="ai-results"></div>
</div>

</div>
</div>

<script>
let businessGoals = {objective:null,audience:null,conversion:null,strategy:null,stage:null,position:null};
let currentMetrics = {rank:null,organic_keywords:null,organic_traffic:null,backlinks:null,referring_domains:null,authority_score:null};
let currentOnPage = null;
let currentDomain = null;
let currentSnapshotId = null;
let currentSiteAudit = null;

function selectOption(el, key, val) {
  el.parentElement.querySelectorAll('.radio-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  el.querySelector('input').checked = true;
  businessGoals[key] = val;
}

function switchTab(tab) {
  document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
  document.getElementById(tab).classList.add('active');
  event.target.classList.add('active');
  if (tab === 'ai') loadAI();
}

function showLoading(id) {
  document.getElementById(id).innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
}

function showError(id, msg) {
  document.getElementById(id).innerHTML = '<div class="alert-error"><strong>Error:</strong> ' + msg + '</div>';
}

function clean(val) {
  return val ? String(val).replace(/"/g,'').replace(/\\r/g,'') : 'N/A';
}

function fmt(val) {
  return val && val !== 'N/A' ? parseInt(val).toLocaleString() : 'N/A';
}

async function analyzeDomain() {
  const domain = document.getElementById('domain-input').value;
  const database = document.getElementById('domain-db').value;
  if (!domain) return showError('domain-results', 'Enter domain');
  currentDomain = domain;
  showLoading('domain-results');
  try {
    const res = await fetch('/api/domain/overview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: database})
    });
    const data = await res.json();
    if (data.success) {
      const d = data.data;
      currentMetrics.rank = d.Rank;
      currentMetrics.organic_keywords = d['Organic Keywords'];
      currentMetrics.organic_traffic = d['Organic Traffic'];
      let html = '<div class="metric-grid">';
      html += '<div class="metric-card"><h3>Rank</h3><div class="value">#' + fmt(clean(d.Rank)) + '</div></div>';
      html += '<div class="metric-card"><h3>Keywords</h3><div class="value">' + fmt(clean(d['Organic Keywords'])) + '</div></div>';
      html += '<div class="metric-card"><h3>Traffic</h3><div class="value">' + fmt(clean(d['Organic Traffic'])) + '</div></div>';
      html += '<div class="metric-card"><h3>Value</h3><div class="value">$' + fmt(clean(d['Organic Cost'])) + '</div></div>';
      html += '</div>';
      document.getElementById('domain-results').innerHTML = html;
    } else {
      showError('domain-results', 'Failed');
    }
  } catch (e) {
    showError('domain-results', e.message);
  }
}

async function analyzeOrganic() {
  const domain = document.getElementById('organic-input').value;
  const database = document.getElementById('organic-db').value;
  if (!domain) return;
  showLoading('organic-results');
  try {
    const res = await fetch('/api/organic/keywords', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: database})
    });
    const data = await res.json();
    if (data.success) {
      let html = '<div class="table-container"><table class="data-table"><thead><tr><th>Keyword</th><th>Pos</th><th>Volume</th></tr></thead><tbody>';
      data.data.slice(0, 50).forEach(r => {
        html += '<tr><td><strong>' + clean(r.Keyword) + '</strong></td><td>' + clean(r.Position) + '</td><td>' + fmt(clean(r['Search Volume'])) + '</td></tr>';
      });
      html += '</tbody></table></div>';
      document.getElementById('organic-results').innerHTML = html;
    }
  } catch (e) {
    showError('organic-results', e.message);
  }
}

async function getCompetitors() {
  const domain = document.getElementById('organic-input').value;
  const database = document.getElementById('organic-db').value;
  if (!domain) return;
  showLoading('organic-results');
  try {
    const res = await fetch('/api/organic/competitors', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: database})
    });
    const data = await res.json();
    if (data.success) {
      let html = '<div class="table-container"><table class="data-table"><thead><tr><th>Domain</th><th>Common</th><th>Organic</th></tr></thead><tbody>';
      data.data.forEach(r => {
        html += '<tr><td><strong>' + clean(r.Domain) + '</strong></td><td>' + fmt(clean(r['Common Keywords'])) + '</td><td>' + fmt(clean(r['Organic Keywords'])) + '</td></tr>';
      });
      html += '</tbody></table></div>';
      document.getElementById('organic-results').innerHTML = html;
    }
  } catch (e) {
    showError('organic-results', e.message);
  }
}

async function getReferring() {
  const domain = document.getElementById('backlinks-input').value;
  if (!domain) return;
  showLoading('backlinks-results');
  try {
    const res = await fetch('/api/backlinks/referring-domains', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: 'us'})
    });
    const data = await res.json();
    if (data.success) {
      const a = data.analysis;
      let html = '<div class="metric-grid">';
      html += '<div class="metric-card"><h3>Total</h3><div class="value">' + fmt(a.total) + '</div></div>';
      html += '<div class="metric-card" style="background:#ff6b6b"><h3>Toxic</h3><div class="value">' + fmt(a.toxic) + '</div></div>';
      html += '<div class="metric-card" style="background:#ffd93d"><h3>Caution</h3><div class="value">' + fmt(a.potentially_toxic) + '</div></div>';
      html += '<div class="metric-card" style="background:#51cf66"><h3>Healthy</h3><div class="value">' + fmt(a.healthy) + '</div></div>';
      html += '</div>';
      document.getElementById('backlinks-results').innerHTML = html;
    }
  } catch (e) {
    showError('backlinks-results', e.message);
  }
}

async function getAnchors() {
  const domain = document.getElementById('backlinks-input').value;
  if (!domain) return;
  showLoading('backlinks-results');
  try {
    const res = await fetch('/api/backlinks/anchors', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: 'us'})
    });
    const data = await res.json();
    if (data.success) {
      let html = '<div class="table-container"><table class="data-table"><thead><tr><th>Anchor</th><th>Domains</th></tr></thead><tbody>';
      data.data.slice(0, 30).forEach(r => {
        html += '<tr><td><strong>' + clean(r.anchor) + '</strong></td><td>' + fmt(clean(r.domains_num)) + '</td></tr>';
      });
      html += '</tbody></table></div>';
      document.getElementById('backlinks-results').innerHTML = html;
    }
  } catch (e) {
    showError('backlinks-results', e.message);
  }
}

async function analyzeKeyword() {
  const kw = document.getElementById('keyword-input').value;
  const database = document.getElementById('keyword-db').value;
  if (!kw) return;
  showLoading('keywords-results');
  try {
    const res = await fetch('/api/keyword/overview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({keyword: kw, database: database})
    });
    const data = await res.json();
    if (data.success) {
      const d = data.data;
      let html = '<div class="metric-grid">';
      html += '<div class="metric-card"><h3>Volume</h3><div class="value">' + fmt(clean(d['Search Volume'])) + '</div></div>';
      html += '<div class="metric-card"><h3>CPC</h3><div class="value">$' + clean(d.CPC) + '</div></div>';
      html += '</div>';
      document.getElementById('keywords-results').innerHTML = html;
    }
  } catch (e) {
    showError('keywords-results', e.message);
  }
}

async function getRelated() {
  const kw = document.getElementById('keyword-input').value;
  const database = document.getElementById('keyword-db').value;
  if (!kw) return;
  showLoading('keywords-results');
  try {
    const res = await fetch('/api/keyword/related', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({keyword: kw, database: database, limit: 30})
    });
    const data = await res.json();
    if (data.success) {
      let html = '<div class="table-container"><table class="data-table"><thead><tr><th>Keyword</th><th>Volume</th></tr></thead><tbody>';
      data.data.forEach(r => {
        html += '<tr><td><strong>' + clean(r.Keyword) + '</strong></td><td>' + fmt(clean(r['Search Volume'])) + '</td></tr>';
      });
      html += '</tbody></table></div>';
      document.getElementById('keywords-results').innerHTML = html;
    }
  } catch (e) {
    showError('keywords-results', e.message);
  }
}

async function completeAnalysis() {
  const domain = document.getElementById('complete-input').value;
  const database = document.getElementById('complete-db').value;
  if (!domain) return;
  currentDomain = domain;
  showLoading('complete-results');
  try {
    const res = await fetch('/api/complete-analysis', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({domain: domain, database: database})
    });
    const data = await res.json();
    if (data.success) {
      const d = data.data;
      let html = '';

      if (d.domain_overview) {
        const o = d.domain_overview;
        currentMetrics.rank = o.Rank;
        currentMetrics.organic_keywords = o['Organic Keywords'];
        currentMetrics.organic_traffic = o['Organic Traffic'];
        html += '<h3>Domain</h3><div class="metric-grid">';
        html += '<div class="metric-card"><h3>Rank</h3><div class="value">#' + fmt(clean(o.Rank)) + '</div></div>';
        html += '<div class="metric-card"><h3>Keywords</h3><div class="value">' + fmt(clean(o['Organic Keywords'])) + '</div></div>';
        html += '<div class="metric-card"><h3>Traffic</h3><div class="value">' + fmt(clean(o['Organic Traffic'])) + '</div></div>';
        html += '</div>';
      }

      if (d.backlinks_overview) {
        const b = d.backlinks_overview;
        currentMetrics.authority_score = b.ascore;
        currentMetrics.backlinks = b.total;
        currentMetrics.referring_domains = b.domains_num;
        html += '<h3 style="margin-top:30px">Backlinks</h3><div class="metric-grid">';
        html += '<div class="metric-card"><h3>Authority</h3><div class="value">' + clean(b.ascore) + '</div></div>';
        html += '<div class="metric-card"><h3>Total</h3><div class="value">' + fmt(clean(b.total)) + '</div></div>';
        html += '<div class="metric-card"><h3>Domains</h3><div class="value">' + fmt(clean(b.domains_num)) + '</div></div>';
        html += '</div>';
      }

      if (d.onpage_analysis && d.onpage_analysis.crawl_success) {
        const o = d.onpage_analysis;
        currentOnPage = o;
        html += '<div class="onpage-box" style="margin-top:30px"><h4>On-Page Analysis</h4>';
        html += '<div class="onpage-item"><span class="onpage-label">Meta:</span><span class="onpage-value">' + o.meta_desc_status + ' (' + o.meta_desc_length + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Title:</span><span class="onpage-value">' + o.title_status + ' (' + o.title_length + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">H1:</span><span class="onpage-value">' + o.h1_status + ' (' + o.h1_count + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Content:</span><span class="onpage-value">' + o.content_status + ' (' + o.word_count + ' words)</span></div>';
        html += '</div>';
      }

      if (d.site_audit && d.site_audit.issues) {
        currentSiteAudit = d.site_audit;
        const issues = d.site_audit.issues;
        const errors = issues.filter(i => i.severity === 'Error');
        const warnings = issues.filter(i => i.severity === 'Warning');
        const notices = issues.filter(i => i.severity === 'Notice');
        html += '<div class="audit-box" style="margin-top:30px"><h4>🔍 Site Audit Summary</h4>';
        html += '<div class="audit-item"><span class="audit-label">Total Issues:</span><span class="audit-value">' + issues.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Errors:</span><span class="audit-value error">' + errors.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Warnings:</span><span class="audit-value warning">' + warnings.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Notices:</span><span class="audit-value notice">' + notices.length + '</span></div>';
        html += '</div>';
      }

      document.getElementById('complete-results').innerHTML = html;
    }
  } catch (e) {
    showError('complete-results', e.message);
  }
}

async function getSiteAuditIssues() {
  const projectId = document.getElementById('project-id-input').value;
  if (!projectId) return showError('site-audit-results', 'Enter project ID');
  showLoading('site-audit-results');
  try {
    const res = await fetch('/api/site-audit/issues', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({project_id: projectId})
    });
    const data = await res.json();
    if (data.success) {
      currentSnapshotId = data.snapshot_id;
      let html = '<h3>Site Audit Issues</h3>';

      // Sort by severity and count
      const severityOrder = {'Error': 1, 'Warning': 2, 'Notice': 3};
      const sortedIssues = data.data.sort((a, b) => {
        if (severityOrder[a.severity] !== severityOrder[b.severity]) {
          return severityOrder[a.severity] - severityOrder[b.severity];
        }
        return b.count - a.count;
      });

      // Display by severity
      for (const severity of ['Error', 'Warning', 'Notice']) {
        const severityIssues = sortedIssues.filter(i => i.severity === severity);
        if (severityIssues.length > 0) {
          html += `<h4 style="margin-top:20px;color:${severity === 'Error' ? '#ef4444' : severity === 'Warning' ? '#f59e0b' : '#10b981'}">${severity}s</h4>`;
          html += '<div class="table-container"><table class="data-table"><thead><tr><th>Issue</th><th>Count</th><th>Delta</th><th>Actions</th></tr></thead><tbody>';

          severityIssues.forEach(issue => {
            const deltaSign = issue.delta > 0 ? '+' : '';
            const deltaStr = issue.delta !== 0 ? `(${deltaSign}${issue.delta})` : '';
            html += `<tr>
              <td><strong>${issue.issue_name}</strong></td>
              <td>${issue.count}</td>
              <td>${deltaStr}</td>
              <td><button class="btn" onclick="viewIssueDetails(${issue.issue_id})" style="padding:5px 10px;font-size:0.8em">View Details</button></td>
            </tr>`;
          });

          html += '</tbody></table></div>';
        }
      }

      document.getElementById('site-audit-results').innerHTML = html;
    } else {
      showError('site-audit-results', data.message || 'Failed to fetch issues');
    }
  } catch (e) {
    showError('site-audit-results', e.message);
  }
}

async function getIssueDetails() {
  const projectId = document.getElementById('project-id-input').value;
  const issueId = document.getElementById('issue-id-input').value;

  if (!projectId) return showError('site-audit-results', 'Enter project ID');
  if (!issueId) return showError('site-audit-results', 'Enter issue ID');

  showLoading('site-audit-results');
  try {
    const res = await fetch('/api/site-audit/issue-details', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({project_id: projectId, issue_id: parseInt(issueId)})
    });
    const data = await res.json();
    if (data.success) {
      let html = `<h3>Issue Details: ${data.issue_name} (ID: ${issueId})</h3>`;
      html += `<p>Total pages: ${data.total}</p>`;

      if (data.data && data.data.length > 0) {
        html += '<div class="table-container"><table class="data-table"><thead><tr><th>URL</th><th>Title</th></tr></thead><tbody>';

        data.data.slice(0, 50).forEach(page => {
          // Try multiple possible URL field names
          const url = page.target_url || page.url || page.page_url || page.page || 'N/A';
          const title = page.title || page.page_title || 'N/A';

          // Create a clickable link for the URL
          const urlDisplay = url !== 'N/A' ? 
            `<a href="${url}" target="_blank" class="url-link">${url}</a>` : 
            'N/A';

          html += `<tr><td>${urlDisplay}</td><td>${title}</td></tr>`;
        });

        html += '</tbody></table></div>';

        if (data.total > 50) {
          html += `<p>Showing first 50 of ${data.total} pages</p>`;
        }
      } else {
        html += '<p>No pages found for this issue</p>';
      }

      document.getElementById('site-audit-results').innerHTML = html;
    } else {
      showError('site-audit-results', data.message || 'Failed to fetch issue details');
    }
  } catch (e) {
    showError('site-audit-results', e.message);
  }
}

async function viewIssueDetails(issueId) {
  document.getElementById('issue-id-input').value = issueId;
  getIssueDetails();
}

async function loadAI() {
  if (!currentDomain) return showError('ai-results', 'Analyze domain first');
  document.getElementById('ai-results').innerHTML = '<div class="ai-loading"><h3>🤖 Generating AI Recommendations...</h3><p>Analyzing: Business Goals + SEMrush Data + On-Page + Site Audit</p><div><span class="ai-pulse"></span><span class="ai-pulse"></span><span class="ai-pulse"></span></div></div>';
  try {
    const res = await fetch('/api/recommendations', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        domain: currentDomain,
        business_goals: businessGoals,
        metrics: currentMetrics,
        onpage_data: currentOnPage,
        site_audit_data: currentSiteAudit
      })
    });
    const data = await res.json();
    if (data.success) {
      let html = '';

      if (data.onpage_data && data.onpage_data.crawl_success) {
        const o = data.onpage_data;
        html += '<div class="onpage-box"><h4>📊 On-Page Analysis Results</h4>';
        html += '<div class="onpage-item"><span class="onpage-label">Meta:</span><span class="onpage-value">' + o.meta_desc_status + ' (' + o.meta_desc_length + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Title:</span><span class="onpage-value">' + o.title_status + ' (' + o.title_length + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">H1:</span><span class="onpage-value">' + o.h1_status + ' (' + o.h1_count + ')</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Headers:</span><span class="onpage-value">H2=' + o.h2_count + ', H3=' + o.h3_count + ', H4=' + o.h4_count + '</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Content:</span><span class="onpage-value">' + o.content_status + ' (' + o.word_count + ' words)</span></div>';
        html += '<div class="onpage-item"><span class="onpage-label">Images Missing Alt:</span><span class="onpage-value">' + o.images_without_alt + '/' + o.images_total + '</span></div>';
        html += '</div>';
      }

      if (data.site_audit_data && data.site_audit_data.issues) {
        const issues = data.site_audit_data.issues;
        const errors = issues.filter(i => i.severity === 'Error');
        const warnings = issues.filter(i => i.severity === 'Warning');
        const notices = issues.filter(i => i.severity === 'Notice');
        html += '<div class="audit-box"><h4>🔍 Site Audit Summary</h4>';
        html += '<div class="audit-item"><span class="audit-label">Total Issues:</span><span class="audit-value">' + issues.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Errors:</span><span class="audit-value error">' + errors.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Warnings:</span><span class="audit-value warning">' + warnings.length + '</span></div>';
        html += '<div class="audit-item"><span class="audit-label">Notices:</span><span class="audit-value notice">' + notices.length + '</span></div>';
        html += '</div>';
      }

      data.recommendations.forEach(r => {
        const badge = r.severity === 'high' ? 'severity-high' : 'severity-medium';
        let steps = [];
        if (r.fix && typeof r.fix === 'string') {
          const regex = /\\d+\\.\\s*[^\\d]+(?=\\d+\\.|$)/g;
          const match = r.fix.match(regex);
          if (match) {
            steps = match.map(s => s.replace(/^\\d+\\.\\s*/, '').trim()).filter(s => s);
          }
        }
        html += '<div class="rec-card ' + r.severity + '">';
        html += '<div class="rec-header"><div class="rec-icon">' + r.icon + '</div><div class="rec-title"><h3>' + r.category + '</h3><span class="severity-badge ' + badge + '">' + r.severity + '</span></div></div>';
        html += '<div class="issue-section"><h4>⚠️ Issue</h4><p>' + r.issue + '</p></div>';
        html += '<div class="fix-section"><h4>✅ How to Fix</h4><ol>';
        if (steps.length > 0) {
          steps.forEach(s => {
            html += '<li>' + s + '</li>';
          });
        } else {
          html += '<li>Follow SEO best practices</li>';
        }
        html += '</ol></div></div>';
      });

      document.getElementById('ai-results').innerHTML = html;
    }
  } catch (e) {
    showError('ai-results', e.message);
  }
}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("=" * 70)
    print("Novarsis AI SEO Analyzer")
    print("One Click Solution")
    print("=" * 70)
    print("\n📊 Server: http://localhost:8000")
    print("\n✨ Features:")
    print("   ✓ 24+ Country Databases")
    print("   ✓ Groq AI + FastMCP")
    print("   ✓ On-Page SEO Analysis")
    print("   ✓ Business Goals Integration")
    print("   ✓ Site Audit Issues Analysis")
    print("   ✓ AI Recommendations with ALL Data")
    print("\n" + "=" * 70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)