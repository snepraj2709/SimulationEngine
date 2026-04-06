from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SampleSite:
    normalized_url: str
    html: str


NETFLIX_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>Netflix India - Watch TV Shows Online, Watch Movies Online</title>
    <meta
      name="description"
      content="Watch Netflix anywhere. Stream award-winning TV shows, movies, anime, documentaries and more on your phone, tablet, laptop and TV."
    />
  </head>
  <body>
    <header>
      <h1>Unlimited movies, TV shows and more</h1>
      <p>Starts at Rs 149. Cancel anytime.</p>
      <p>Ready to watch? Enter your email to create or restart your membership.</p>
    </header>
    <section>
      <h2>Enjoy on your TV</h2>
      <p>Watch on smart TVs, PlayStation, Xbox, Chromecast, Apple TV, Blu-ray players and more.</p>
    </section>
    <section>
      <h2>Download your shows to watch offline</h2>
      <p>Save your favourites easily and always have something to watch.</p>
    </section>
    <section>
      <h2>Watch everywhere</h2>
      <p>Stream unlimited movies and TV shows on your phone, tablet, laptop and TV.</p>
    </section>
    <section>
      <h2>Create profiles for kids</h2>
      <p>Send kids on adventures with their favourite characters in a space made just for them.</p>
    </section>
    <section>
      <h2>Plans to suit your needs</h2>
      <ul>
        <li>Mobile</li>
        <li>Basic</li>
        <li>Standard</li>
        <li>Premium</li>
      </ul>
    </section>
    <section>
      <h2>Frequently Asked Questions</h2>
      <p>What is Netflix? How much does Netflix cost? Where can I watch? How do I cancel?</p>
    </section>
  </body>
</html>
"""


SAMPLE_SITES: dict[str, SampleSite] = {
    "https://www.netflix.com": SampleSite(normalized_url="https://www.netflix.com", html=NETFLIX_HTML),
    "https://www.netflix.com/": SampleSite(normalized_url="https://www.netflix.com", html=NETFLIX_HTML),
}


def get_sample_site(normalized_url: str) -> SampleSite | None:
    normalized_lookup = normalized_url.rstrip("/")
    return SAMPLE_SITES.get(normalized_lookup) or SAMPLE_SITES.get(f"{normalized_lookup}/")
