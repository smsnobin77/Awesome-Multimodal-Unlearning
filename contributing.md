# Contributing

## What to Add
- Relevant papers (VLMs, DMs, Audio, Video, etc.)
- Fix links, formatting, or missing information
- Improve organization (categories, ordering)

## Guidelines
- Use **official links** (arXiv, OpenReview, etc.)
- Follow existing **format and structure**
- Keep entries **concise and consistent**
- Avoid duplicates

## How to Add a Paper
1. Add an entry to `papers.yaml`. Required fields: `key`, `title`, `year`, `kind`, and `links`. For a method, also set `stage` and `family`. The allowed ids are in `survey.yaml`.
2. Put the tags you choose under `added`, for example `added: {model: [vlm], target: [identity]}`. The `tags` field is reserved for what the survey itself states.
3. Run `uv run scripts/build.py`. It updates the README list and the explorer data.
4. Optional: run `uv run --group embed scripts/embed.py` so semantic search covers the new paper.
5. Open a pull request. CI checks that the generated files are current and runs the tests.

You can also [suggest a paper](https://github.com/smsnobin77/Awesome-Multimodal-Unlearning/issues/new?template=add-paper.yml), and we will add it.
