# Manuscript Figures

`figure-1-latency.svg` and `figure-2-communication.svg` are generated assets.
To reproduce them from a fresh checkout, first run:

```bash
python3 scripts/analysis/analyze_final_campaign.py --campaign campaign-20261020T083014Z-70543371b61f
python3 scripts/analysis/render_final_figures.py
```

The generator reads only the derived summaries written by the analysis script;
neither command edits immutable raw campaign data.
