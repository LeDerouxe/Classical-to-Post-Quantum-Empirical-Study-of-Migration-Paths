# Manuscript Figures

`figure-1-latency.svg`, `figure-2-communication.svg`,
`figure-3-network-sensitivity.svg`, `figure-s1-primary-batches.svg`, and
`figure-s2-compatibility-matrix.svg` are generated assets.
To reproduce them from a fresh checkout, first run:

```bash
python3 scripts/analysis/analyze_final_campaign.py --campaign campaign-20261020T083014Z-70543371b61f
python3 scripts/analysis/render_final_figures.py
python3 scripts/analysis/analyze_network_campaign.py --campaign campaign-20261114T202013Z-44a824c91fb9
python3 scripts/analysis/render_network_figure.py
python3 scripts/analysis/render_supplementary_figures.py
```

The generator reads only the derived summaries written by the analysis script;
neither command edits immutable raw campaign data.
