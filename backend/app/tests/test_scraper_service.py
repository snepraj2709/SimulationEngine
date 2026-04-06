from app.services.scraper_service import ScraperService


def test_parse_html_extracts_product_signals_without_demo_shortcut() -> None:
    html = """
    <html>
      <head>
        <title>Acme Revenue OS</title>
        <meta name="description" content="Automate onboarding, renewals, and customer analytics." />
      </head>
      <body>
        <h1>Automate onboarding and renewals</h1>
        <h2>Built for customer success teams</h2>
        <p>Annual plans with custom enterprise pricing.</p>
        <p>Analytics, dashboards, and workflow automation for revenue teams.</p>
        <a>Request a demo</a>
      </body>
    </html>
    """

    result = ScraperService()._parse_html("https://acme.example/", html, fetch_source="network")

    assert result.title == "Acme Revenue OS"
    assert result.fetch_source == "network"
    assert "Annual plans with custom enterprise pricing." in result.paragraphs
    assert any("pricing" in clue.lower() or "annual" in clue.lower() for clue in result.pricing_clues)
