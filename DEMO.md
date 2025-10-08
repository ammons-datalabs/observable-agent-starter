# Creating a Demo Screencast

To replace the placeholder image in README.md with an actual demo gif/screencast:

## Option 1: Terminal Recording (Recommended for CLI)

Use [asciinema](https://asciinema.org/) for terminal recordings:

```bash
# Install
brew install asciinema  # macOS
# or: pip install asciinema

# Record a session
asciinema rec demo.cast

# Run your demo commands during recording:
python -m agents.triage

# Press Ctrl+D to stop recording

# Convert to GIF using agg
cargo install agg
agg demo.cast demo.gif

# Or upload to asciinema.org
asciinema upload demo.cast
```

## Option 2: Screen Recording (Recommended for FastAPI)

Use [Kap](https://getkap.co/) (macOS) or [Peek](https://github.com/phw/peek) (Linux):

1. Start recording
2. Open terminal and run:
   ```bash
   uvicorn examples.fastapi_server:app --reload
   ```
3. Open browser to http://localhost:8000/docs
4. Test the `/triage` endpoint with Swagger UI
5. Stop recording
6. Export as GIF (keep under 5MB for GitHub)

## Option 3: Quick Screenshot

Use [Carbon](https://carbon.now.sh/) for beautiful code screenshots:

1. Visit https://carbon.now.sh/
2. Paste this example:
   ```bash
   $ curl -X POST http://localhost:8000/triage \\
     -H "Content-Type: application/json" \\
     -d '{"ticket": "My invoice has extra charges"}'

   {
     "route": "billing",
     "explanation": "Routes billing-related issues to the billing team"
   }
   ```
3. Export as PNG
4. Add to repo and update README.md

## Update README

Once you have your demo asset:

```bash
# If using a local file (recommended for <5MB assets):
git add demo.gif
# Update README.md line 41 to:
# ![Demo screencast](./demo.gif)

# If using an external host:
# ![Demo screencast](https://your-url.com/demo.gif)
```

## Recommended Demo Script

Show a complete workflow:

1. **Start with test output**: `pytest -q` showing all tests pass
2. **Run CLI agent**: `python -m agents.triage` with example ticket
3. **Start FastAPI server**: `uvicorn examples.fastapi_server:app --reload`
4. **Show Swagger docs**: Open http://localhost:8000/docs
5. **Test endpoint**: POST to `/triage` with example ticket
6. **Show Langfuse trace** (if configured): Brief glimpse of Langfuse dashboard

Keep it under 30 seconds for optimal engagement.
