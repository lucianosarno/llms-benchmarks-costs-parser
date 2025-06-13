# Vals.ai LLM Benchmarks Data Parser

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Description

This repository contains a Python script to programmatically scrape benchmark data from the [Vals.ai Benchmarks](https://www.vals.ai/benchmarks) website. The goal is to provide a structured, machine-readable dataset of LLM performance metrics (Accuracy, Cost Input/Output, Latency) across various benchmarks, updated daily.

The scraped data is stored in a JSON file (`benchmarks_data.json`) in this repository, allowing for easier analysis, comparison, and visualization of different Large Language Models and their providers.

## Features

*   Scrapes all available benchmark links from the main Vals.ai benchmarks page.
*   Visits each benchmark page to extract detailed model data.
*   Parses Model Name, Company (from SVG icon filename), Accuracy, Cost Input, Cost Output, and Latency for each model.
*   Stores the collected data in a structured JSON format.
*   Includes a timestamp for when the data was last updated.
*   Automated daily updates via GitHub Actions (see [Automation](#automation)).

## Getting Started

### Prerequisites

*   Python 3.x installed.
*   `pip` (Python package installer).

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/lucianosarno/llm-benchmarks-costs-parser.git
    cd llm-benchmarks-costs-parser
    ```
2.  (Recommended) Create and activate a Python virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
    ```
3.  Install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the scraping script manually:

```bash
source .venv/bin/activate # Activate virtual environment if you created one
python vals_parser.py
```

This script will fetch the latest data and update the benchmarks_data.json file in the root of the repository.
Data Output: benchmarks_data.json

The core output of the script is the benchmarks_data.json file. This file contains a JSON object with the following structure:

```json
{
    "timestamp_utc": "YYYY-MM-DDTHH:MM:SS.ssssss", // UTC timestamp of the data scrape
    "benchmarks": [
        {
            "benchmark": "benchmark-name-from-url", // e.g., "legal-qa"
            "model": "Model Name",                // e.g., "Grok 3 Beta"
            "company": "Company Name",            // e.g., "xAI", "OpenAI"
            "accuracy": "Percentage%",            // e.g., "88.1%"
            "cost_input": "$Value",               // e.g., "\$3.00"
            "cost_output": "$Value",              // e.g., "\$15.00"
            "latency": "Value s"                  // e.g., "3.91 s"
        },
        // ... more model entries ...
    ]
}
```

You can view the latest version of this file directly on GitHub or access its raw content via:

https://raw.githubusercontent.com/lucianosarno/llms-benchmarks-costs-parser/main/benchmarks_data.json

## Data Visualization

The data collected by this script is used to power interactive dashboards hosted on Zoho Analytics, providing visual insights into LLM performance across benchmarks and providers.

### LLM Providers vs. Benchmarks vs. Cost
https://analytics.zoho.com/open-view/2732937000006457007

This chart aggregates data by provider, showing average costs across different benchmarks.

### Individual LLM Models vs. Benchmarks vs. Cost
https://analytics.zoho.com/open-view/2732937000006459493"
This chart provides a detailed view of individual model performance and costs per benchmark.

### Chart Filters and Cost Explanation

Both embedded charts offer interactive filters to refine the data being displayed:

#### Minimum Accuracy Filter
Located on the chart interface, this filter allows you to set a minimum accuracy threshold. Only models that achieved an accuracy score above this minimum percentage in all benchmarks included in the current view will be shown. This helps focus on top-performing models.
#### Timestamp Filter
This date filter allows you to select the data from a specific date's scrape. The script saves data with a timestamp_utc, and this filter uses that timestamp to let you view historical snapshots of the benchmark results.
#### Costs
The charts primarily visualize costs based on the 'Cost Input' metric from the scraped data. It's important to note that the raw data in benchmarks_data.json includes both 'Cost Input' and 'Cost Output', which are often proportional or related based on the model's pricing structure. The charts may simplify by focusing on one metric, but the full cost breakdown is available in the source JSON.

## Automation

The script is configured to run daily using GitHub Actions. This ensures the benchmarks_data.json file is automatically updated with the latest information from Vals.ai without manual intervention.

(Note: This README assumes you will set up the GitHub Action workflow. You'll need to create the .github/workflows directory and a .yml file for the workflow configuration.)
Contributing

Contributions are welcome! If you find issues or have suggestions for improvements (e.g., adding more data points, improving parsing robustness), please open an issue or submit a pull request.
License

This project is licensed under the MIT License - see the LICENSE file for details.