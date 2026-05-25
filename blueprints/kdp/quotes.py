import os
import threading

from flask import Blueprint, jsonify, request

from extensions import db_save, db_update
from jobs import create_job, jdone, jerror, jlog

bp = Blueprint('kdp_quotes', __name__)

# Sonnet 4.6 is the sweet spot for templated generation — fast + cheap.
# User explicitly requested this model.
ANTHROPIC_MODEL = "claude-sonnet-4-6"

QUOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "niche_summary": {
            "type": "string",
            "description": "1-sentence description of the niche identified from the titles",
        },
        "quotes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "lines": {"type": "integer"},
                    "category": {"type": "string"},
                },
                "required": ["text", "lines", "category"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["niche_summary", "quotes"],
    "additionalProperties": False,
}

PROMPT_TEMPLATE = """You are helping create an Amazon KDP coloring book in a specific niche.

Below are real Amazon book titles from this niche (scraped from search results):

{titles}

Tasks:
1. Identify the dominant theme, audience, and tone in 1 sentence (`niche_summary`).
2. Generate EXACTLY 50 short, positive quotes appropriate for a coloring-book interior page in this niche.

Quote requirements:
- 3–7 words each (max 6 for best visual impact)
- Match the niche tone (mindfulness → calm/reflective; humor → witty; faith → spiritual; fitness → motivational)
- Variety: different angles within the theme
- Positive / inspirational (these go inside coloring books often given as gifts)
- No quotation marks inside the `text` field
- For `lines`: estimate visual lines on the page — 1 if ≤3 words, 2 if 4–6 words, 3 if longer
- For `category`: one-word thematic tag (calm, joy, gratitude, focus, faith, etc.)

Return the result strictly in the requested JSON shape."""


@bp.route('/quotes/generate', methods=['POST'])
def quotes_generate():
    keywords = request.form.get('keywords', '').strip()
    scrapeops_key = request.form.get('scrapeops_api_key', '').strip()

    if not keywords:
        return jsonify({'error': 'Podaj słowa kluczowe'}), 400
    if not scrapeops_key:
        return jsonify({'error': 'Podaj klucz ScrapeOps API'}), 400
    if not os.getenv('ANTHROPIC_API_KEY'):
        return jsonify({'error': 'Brak ANTHROPIC_API_KEY w .env'}), 400

    keys = [k.strip() for k in keywords.splitlines() if k.strip()][:5]
    jid = create_job()
    rid = db_save('kdp_quotes', {'keywords': keys})

    def run():
        try:
            import json
            import anthropic
            import requests as req
            from bs4 import BeautifulSoup

            titles = []

            for key in keys:
                url = 'https://www.amazon.com/s?k=' + key.replace(' ', '+')
                jlog(jid, f'🔍 Amazon: "{key}"')
                try:
                    r = req.get('https://proxy.scrapeops.io/v1/',
                                params={'api_key': scrapeops_key, 'url': url},
                                timeout=40)
                    r.encoding = 'utf-8'
                    soup = BeautifulSoup(r.text, 'lxml')
                    found = []
                    for el in soup.select('h2 a span'):
                        t = el.get_text(strip=True)
                        if t and 10 < len(t) < 250 and t not in found:
                            found.append(t)
                    titles.extend(found[:40])
                    jlog(jid, f'   ✅ {len(found)} tytułów')
                except Exception as e:
                    jlog(jid, f'   ❌ {e}')

            # Dedupe across all keywords, cap at 200 for prompt size
            seen = set()
            unique_titles = []
            for t in titles:
                if t not in seen:
                    seen.add(t)
                    unique_titles.append(t)
            unique_titles = unique_titles[:200]

            if not unique_titles:
                jerror(jid, 'Nie znaleziono żadnych tytułów na Amazon — sprawdź klucz ScrapeOps i słowa kluczowe')
                db_update(rid, 'error')
                return

            jlog(jid, f'📊 Łącznie unikalnych tytułów: {len(unique_titles)}')
            jlog(jid, f'🤖 Wywołuję Claude ({ANTHROPIC_MODEL})...')

            client = anthropic.Anthropic()
            titles_block = '\n'.join(f'- {t}' for t in unique_titles)
            user_prompt = PROMPT_TEMPLATE.format(titles=titles_block)

            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                thinking={"type": "disabled"},
                output_config={
                    "format": {"type": "json_schema", "schema": QUOTE_SCHEMA},
                    "effort": "low",
                },
                messages=[{"role": "user", "content": user_prompt}],
            )

            text = next(b.text for b in response.content if b.type == "text")
            data = json.loads(text)

            usage = response.usage
            jlog(jid, f'💰 Tokens — in: {usage.input_tokens}, out: {usage.output_tokens}')
            jlog(jid, f'📝 Niche: {data["niche_summary"]}')
            jlog(jid, f'✅ Wygenerowano {len(data["quotes"])} cytatów')

            jdone(jid, None, len(data["quotes"]), data=data)
            db_update(rid, 'done', len(data["quotes"]))

        except anthropic.AuthenticationError:
            jerror(jid, 'Niepoprawny ANTHROPIC_API_KEY')
            db_update(rid, 'error')
        except anthropic.RateLimitError:
            jerror(jid, 'Claude API rate limit — spróbuj za chwilę')
            db_update(rid, 'error')
        except anthropic.APIError as e:
            jerror(jid, f'Claude API: {e}')
            db_update(rid, 'error')
        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))
            db_update(rid, 'error')

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})
