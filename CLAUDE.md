# Architecture Guidelines

## Python/JS Hybrid Structure

```
pipeline/           # Data processing
├── transcript.py   # Video transcription
├── llm.py          # LLM integration
├── slides.py       # Slide extraction
└── main.py         # Pipeline orchestration

frontend/src/       # React frontend
├── components/     # UI components
└── App.js          # Main app
```

## Dependency Rules

- Pipeline modules are independent
- Frontend uses React patterns
- LLM calls isolated in llm.py
- No direct API calls in components

## Naming Conventions

- Pipeline: `*.py`
- Components: `*.js` in components/
- Services: `*_service.js`

## Code Size Limits

- **Max 300 lines per file** (warn at 300)
- **Max 30 lines per function** (warn at 30)
- **Max nesting depth ≤ 4**
- **Max 3 parameters per function**

If code exceeds these limits, REFACTOR immediately using Extract Function or Extract Class.

## Before Generating Code

1. Identify frontend vs pipeline
2. Keep pipeline functions pure
3. Frontend follows React patterns
4. Keep files under 300 lines, functions under 30 lines
5. Run: `npm run lint` / `python -m pytest`